from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.resume_shortlister_bot import router as chat
from src.routers.get_resumes import router as resumes
from src.routers.resume_upload import router as upload_resume
from src.routers.resume_download import router as download_resume
from src.routers.delete_resumes import router as delete_resume
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",   # React frontend
    "http://127.0.0.1:3000",
    "https://resume-chatbot-frontend-alpha.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # allowed domains
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE
    allow_headers=["*"],          # allow all headers
)

app.include_router(chat, prefix="/api")
app.include_router(upload_resume, prefix="/api")
app.include_router(download_resume, prefix="/api")
app.include_router(resumes, prefix="/api")
app.include_router(delete_resume, prefix="/api/resumes")
