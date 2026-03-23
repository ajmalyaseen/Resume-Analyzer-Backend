import os
import io
import re
import json
import logging
import PyPDF2
from fastapi import HTTPException
from groq import AsyncGroq
from tavily import TavilyClient
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from the .env file located in the same directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Initialize external clients
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# File upload constraints
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = ["application/pdf"]

async def extract_resume_text(pdf_file):
    """
    Extracts text content from an uploaded PDF file.
    Validates file type and size before processing.
    """
    # Validate content type
    if pdf_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Read the file contents into memory
    contents = await pdf_file.read()

    # Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5 MB.")

    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
    except Exception as e:
        logger.error(f"Failed to parse PDF file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file.")

    text = ""
    # Iterate through each page and append its text content
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text

async def analyzing_resume(resume_text, job_description):
    """
    Analyzes the resume against a job description using Groq's LLM.
    Returns a JSON object with match percentage, matches, missing skills, and suggestions.
    """
    system_prompt = """
    You are an expert HR and ATS (Applicant Tracking System) analyzer.
    Compare the provided Resume with the Job Description.
    Respond ONLY with a valid JSON object using these keys:
    1. match_percentage: (in percentage)
    2. matches: (list of matching skills)
    3. missing: (list of missing skills)
    4. suggestions: (how to reach 100% match)
    Do not include any text outside the JSON object.
    """

    user_content = f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}"

    try:
        # Request a completion from the Groq model
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="llama-3.3-70b-versatile",
        )
    
        # Get the response content from the model
        model_response = chat_completion.choices[0].message.content
        
        # Use regex to extract the JSON block from the model's text response
        json_match = re.search(r"\{.*\}", model_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            return {"error": "Could not identify analysis details in the response."}

    except Exception as e:
        logger.error(f"Resume analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process resume analysis. Please try again later.")

async def extract_skills(resume_text):
    """
    Extracts core professional skills from the resume text using Groq's LLM.
    """
    system_prompt = """
    You are a professional Career Consultant and Recruitment Specialist.
    Analyze the provided resume text and extract:
    1. The most important professional skills (top 5-10).
    2. The candidate's TOTAL professional experience level.
    3. The most appropriate "Target Job Title" for this candidate based on their specialization, projects, and skills (e.g., "AI Developer", "Backend Developer", "Data Scientist").

    ### Experience Level Guidelines:
    - **Internship/Fresher:** If the candidate only has internships, student projects, or < 1 year of total full-time experience.
    - **Junior:** 1–3 years of total full-time professional experience.
    - **Senior:** 5+ years of total full-time professional experience.
    - **Expert/Lead:** 10+ years or leadership roles.

    **CRITICAL:** Do NOT over-estimate experience based on the number of skills. A candidate with many skills but only 1 month of internship is a "Fresher/Intern".

    ### Instructions:
    1. Return the output strictly in the following JSON format:
    {
    "skills": ["Skill1", "Skill2", "Skill3"],
    "experience_level": "Fresher" | "Junior" | "Senior" | "Lead",
    "target_role": "Ideal Job Title"
    }
    2. No introduction, no explanation, only the raw JSON object.
    """

    try:
        # Request skill extraction from the Groq model
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Resume Text:\n{resume_text}"},
            ],
            model="llama-3.3-70b-versatile",
        )
    
        # Get the response content
        model_response = chat_completion.choices[0].message.content
        
        # Use regex to extract the JSON block
        json_match = re.search(r"\{.*\}", model_response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            return {"error": "Could not extract skills from the resume."}

    except Exception as e:
        logger.error(f"Skill extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process skill extraction. Please try again later.")

def search_jobs(extracted_skills_data):
    """
    Searches for relevant jobs based on extracted skills, experience level, and target role using Tavily.
    """
    try:
        # Extract skills, experience, and target role from the input data
        skills_list = extracted_skills_data.get("skills", [])
        experience_level = extracted_skills_data.get("experience_level", "Entry Level")
        target_role = extracted_skills_data.get("target_role", "Developer")
        
        if not skills_list:
            return {"error": "No skills were found to search for jobs."}

        # Refine the search query: Experience + Target Role + Top 2 Skills
        exp_prefix = "Fresher" if "fresher" in experience_level.lower() else experience_level
        search_query = f"{exp_prefix} {target_role} jobs in India using {' and '.join(skills_list[:2])}"
        
        logger.info(f"Searching for jobs with query: {search_query}")
        
        # Perform the search using Tavily
        search_results = tavily_client.search(query=search_query, max_results=5)
        
        if search_results.get('results'):
            return {
                "detected_skills": skills_list,
                "detected_experience": experience_level,
                "detected_target_role": target_role,
                "jobs": search_results['results']
            }
        else:
            return {"error": "No matching jobs found for the detected skills."}
            
    except Exception as e:
        logger.error(f"Job search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search for jobs. Please try again later.")

    
