from fastapi import APIRouter, HTTPException
from uuid import UUID
from src.database.db_resume_delete_query import delete_resume_from_db

router = APIRouter()

@router.delete("/{resume_id}")
def delete_resume(resume_id: UUID):
    # Example DB delete logic
    result = delete_resume_from_db(str(resume_id))  # your function

    if not result:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {"message": "Resume deleted successfully"}