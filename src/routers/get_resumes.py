from fastapi import APIRouter
from src.services.get_resumes import get_all_resumes

router = APIRouter()

@router.get("/resumes")
def fetch_resumes():
    resumes = get_all_resumes()
    return {
        "success": True,
        "data": resumes
    }