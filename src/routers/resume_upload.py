from fastapi import APIRouter, UploadFile, File
from src.schema.bot_schema import UploadResponse
from src.services.ingestion import process_resume

router = APIRouter()

@router.post("/upload-resume", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    resume_id, name = await process_resume(file)

    return UploadResponse(
        resume_id=resume_id,
        candidate_name=name,
        message="Resume uploaded successfully"
    )