from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from typing import List, Optional
from jobs import jobs
from utils import (
    get_embedding, 
    cosine_similarity, 
    extract_skills_and_summary, 
    extract_text_from_pdf,
    generate_rag_answer
)

app = FastAPI(title="AI Resume Screener")

# 🔹 In-memory storage (Limit 3)
candidates = []

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return FileResponse("index.html")

# ✅ Specific route for script.js to avoid 404
@app.get("/script.js")
def get_script():
    return FileResponse("script.js")

@app.post("/analyze")
async def analyze_resume(
    name: str = Form(...),
    resume_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    if len(candidates) >= 3:
        return JSONResponse({"error": "Candidate limit (3) reached. Please clear dashboard first."}, status_code=400)

    try:
        final_text = ""
        if file and file.filename:
            content = await file.read()
            if file.filename.endswith(".pdf"):
                final_text = extract_text_from_pdf(content)
            else:
                final_text = content.decode("utf-8")
        elif resume_text:
            final_text = resume_text
        else:
            return JSONResponse({"error": "No resume content provided."}, status_code=400)

        # 1. Extract Skills & Summary
        skills, summary = extract_skills_and_summary(final_text)

        # 2. RAG: Job Matching
        res_emb = get_embedding(final_text)
        matches = []
        for job in jobs:
            job_emb = get_embedding(job["desc"])
            score = cosine_similarity(res_emb, job_emb)
            matches.append({
                "title": job["title"],
                "score": round(score * 100, 1),
                "desc": job["desc"]
            })
        
        # Sort by score
        matches = sorted(matches, key=lambda x: x["score"], reverse=True)
        top_match = matches[0] if matches else {"title": "N/A", "score": 0}

        # 3. Store Candidate
        candidate_data = {
            "id": len(candidates) + 1,
            "name": name,
            "skills": skills,
            "summary": summary,
            "top_job": top_match["title"],
            "score": top_match["score"],
            "matches": matches[:3], # Top 3 matches
            "raw_text": final_text
        }
        candidates.append(candidate_data)

        return candidate_data

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/dashboard")
def get_dashboard():
    return candidates

@app.post("/chat")
def chat_with_hr(request: ChatRequest):
    if not candidates:
        return {"answer": "I don't have any candidate data yet. Please upload some resumes first!"}
    
    # Simple RAG: Pass all candidate info as context
    context = ""
    for c in candidates:
        context += f"Candidate: {c['name']}\nSkills: {', '.join(c['skills'])}\nBest Match: {c['top_job']} ({c['score']}%)\nSummary: {c['summary']}\n---\n"
    
    answer = generate_rag_answer(context, request.message)
    return {"answer": answer}

@app.post("/clear")
def clear_data():
    candidates.clear()
    return {"message": "Data cleared successfully."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)