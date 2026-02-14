import os
import io
import re
import json
import PyPDF2
from groq import AsyncGroq
from tavily import TavilyClient
from dotenv import load_dotenv

# Load environment variables from the .env file located in the same directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Initialize external clients
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

async def extract_resume_text(pdf_file):
    """
    Extracts text content from an uploaded PDF file.
    """
    # Read the file contents into memory
    contents = await pdf_file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))

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
    prompt = f"""
    You are an expert HR and ATS (Applicant Tracking System) analyzer.
    Compare the following Resume with the Job Description.
    
    Resume: {resume_text}
    Job Description: {job_description}
    
    Please provide the output in JSON format with these keys:
    1. match_percentage: (in percentage)
    2. matches: (list of matching skills)
    3. missing: (list of missing skills)
    4. suggestions: (how to reach 100% match)
    """

    try:
        # Request a completion from the Groq model
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
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
        # General error handling for the generation process
        return {"error": "Failed to process resume analysis. Please try again later."}

async def extract_skills(resume_text):
    """
    Extracts core professional skills from the resume text using Groq's LLM.
    """
    prompt = f"""
    You are a professional Career Consultant and Recruitment Specialist.
    Analyze the provided resume text and extract the most important professional skills, 
    certifications, and domain expertise.

    Resume Text: {resume_text}

    ### Instructions:
    1. Identify the top 5-10 core professional skills relevant to the user's career field.
    2. Group them into a single list of strings.
    3. Return the output strictly in the following JSON format:
    {{
    "skills": ["Skill1", "Skill2", "Skill3"]
    }}
    4. No introduction, no explanation, only the raw JSON object.
    """           

    try:
        # Request skill extraction from the Groq model
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
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
        # Error handling for skill extraction
        return {"error": "Failed to process skill extraction. Please try again later."}

def search_jobs(extracted_skills_data):
    """
    Searches for relevant jobs based on extracted skills using the Tavily search engine.
    """
    try:
        # Handle both dictionary input and raw list
        skills_list = extracted_skills_data.get("skills", []) if isinstance(extracted_skills_data, dict) else extracted_skills_data
        
        if not skills_list:
            return {"error": "No skills were found to search for jobs."}

        # Create a search query using the top 3 skills
        search_query = f"Jobs for {' and '.join(skills_list[:3])} in India"
        
        # Perform the search using Tavily
        search_results = tavily_client.search(query=search_query, max_results=5)
        
        if search_results.get('results'):
            return {
                "detected_skills": skills_list,
                "jobs": search_results['results']
            }
        else:
            return {"error": "No matching jobs found for the detected skills."}
            
    except Exception as e:
        # Error handling for the search process
        return {"error": "Failed to search for jobs. Please try again later."}

    
