import logging
from fastapi import FastAPI, UploadFile, File, Form, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .service import analyzing_resume, extract_skills, extract_resume_text, search_jobs
from .cors import setup_cors

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="AI Resume Analyzer API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup CORS middleware
setup_cors(app)

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_resume_endpoint(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(..., max_length=10000),
):
    """
    Endpoint to analyze a resume against a specific job description.
    """
    # 1. Extract text from the uploaded PDF
    resume_text = await extract_resume_text(resume)
    
    # 2. Perform the analysis using the LLM
    analysis_result = await analyzing_resume(resume_text, job_description)
    
    return analysis_result

@app.post("/find-jobs")
@limiter.limit("10/minute")
async def find_jobs_endpoint(request: Request, resume: UploadFile = File(...)):
    """
    Endpoint to extract skills from a resume and find matching jobs online.
    """
    # 1. Extract text from the uploaded PDF
    resume_text = await extract_resume_text(resume)
    
    # 2. Extract core skills from the resume text
    extracted_skills_data = await extract_skills(resume_text)
    
    # 3. Search for jobs based on the detected skills
    job_search_results = search_jobs(extracted_skills_data)
    
    return job_search_results