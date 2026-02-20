# 📄 AI Resume Analyzer & Job Matcher

A powerful AI-driven application that analyzes resumes against job descriptions, extracts core skills, and finds relevant job opportunities using **Groq (Llama 3.3)** and **Tavily AI**.

## 🚀 Features

- **Resume Analysis**: Compares your resume with a job description to give a match percentage, identifies missing skills, and provides suggestions for improvement.
- **Skill Extraction**: Automatically parses professional skills and domain expertise from PDF resumes.
- **AI Job Matcher**: Uses extracted skills to search for the most relevant job openings in India using real-time search.
- **Fast & Lightweight**: Built with **FastAPI** and **Groq Cloud** for lightning-fast AI responses.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **AI Model**: Groq (Llama-3.3-70b-versatile)
- **Search Engine**: Tavily AI
- **PDF Parsing**: PyPDF2
- **Environment Management**: Python-Dotenv

---

## 📥 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ajmalyaseen/ai-resume-analyzer.git
   cd ai-resume-analyzer
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file inside the `app/` directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

---

## 🏃 Running the Application

Start the local development server:
```bash
uvicorn app.main:app --reload
```
The API will be available at: `http://127.0.0.1:8000`

---

## 📡 API Endpoints

### 1. Analyze Resume
- **Endpoint**: `/analyze`
- **Method**: `POST`
- **Payload**: `resume` (PDF file), `job_description` (Text)
- **Returns**: Match percentage, Matches, Missing skills, and Suggestions.

### 2. Find Jobs
- **Endpoint**: `/find-jobs`
- **Method**: `POST`
- **Payload**: `resume` (PDF file)
- **Returns**: Detected skills and matching job links from Tavily.

---

## 🎯 Contributing
Feel free to fork this project and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
[MIT](https://choosealicense.com/licenses/mit/)
