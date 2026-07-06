from groq import Groq
import numpy as np
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import io
import json
import os
from dotenv import load_dotenv

# Load .env values into environment variables.
load_dotenv()

# 🔑 Groq client setup
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")
client = Groq(api_key=api_key)

# 🔹 Load a real embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(file_content):
    """Extract text from PDF bytes."""
    try:
        pdf = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def get_embedding(text):
    """Convert text to embedding vector."""
    return model.encode(text).tolist()

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def extract_skills_and_summary(text):
    """Extract skills and a short summary using Groq LLM."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an HR technical assistant. Analyze the resume text and return a JSON object with 'skills' (list) and 'summary' (brief 2-sentence summary)."
                },
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("skills", []), data.get("summary", "No summary available.")
    except Exception as e:
        print(f"LLM Error: {e}")
        return [], "Failed to analyze resume."

def generate_rag_answer(context, question):
    """Chatbot RAG response based on provided context."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are an AI HR Assistant. Use the following candidate data to answer questions briefly and professionally.\n\nContext:\n{context}"
                },
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Chat Error: {str(e)}"