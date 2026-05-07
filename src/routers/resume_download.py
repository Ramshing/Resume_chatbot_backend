# src/routers/download.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from src.database.db_connections import get_connection, release_connection

router = APIRouter()
BASE_DIR = "/mnt/d/Resume_shortlister_bot"

def get_resume_by_id(resume_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT candidate_name, file_path
            FROM resumes
            WHERE id = %s
        """, (resume_id,))

        row = cursor.fetchone()

        if not row:
            return None

        name, file_path = row

        return {
            "name": name,
            "file_path": file_path
        }

    finally:
        cursor.close()
        release_connection(conn)


@router.get("/download/{resume_id}")
def download_resume(resume_id: str):

    #Step 1: Fetch from DB
    resume = get_resume_by_id(resume_id)
    print("file_path````````````````````````````````",resume)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found in database"
        )

    file_path = resume["file_path"]
    #file_path = os.path.join(BASE_DIR, resume["file_path"])

    #Step 2: Validate file exists
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Resume file not found on server"
        )

    #Step 3: Extract file extension
    file_ext = file_path.split(".")[-1].lower()

    #Step 4: Set correct media type
    media_types = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }

    media_type = media_types.get(file_ext, "application/octet-stream")

    #Step 5: Return file
    return FileResponse(
        path=file_path,
        filename=f"{resume['name']}.{file_ext}",
        media_type=media_type
    )