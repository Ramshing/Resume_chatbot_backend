import fitz  # PyMuPDF
from src.database.db_connections import get_connection, release_connection
from src.services.embedding import get_embedding
from src.utils.generate_hash import generate_file_hash
from src.services.doc_struct_semantic_chunking import chunk_resume_pipeline
from src.utils.llm_groq import call_llm, clean_json
from src.utils.generate_hash import generate_file_hash
from PIL import Image
import fitz  
import io
import re
import json
import pytesseract
import pdfplumber
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def extract_resume_text(file_bytes):
    text = ""

    # Step 1: Try pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n".join(
                page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                for page in pdf.pages
            )
    except Exception as e:
        print("pdfplumber failed:", e)

    # Step 2: If text is poor → use OCR
    if len(text.strip()) < 300:  
        print("Using OCR fallback...")

        text = ""
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page in doc:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            text += pytesseract.image_to_string(img)

    return text

def structure_resume_with_groq(raw_text):
    prompt = f"""
    You are an AI that extracts structured information from resumes.

    Extract and return ONLY valid JSON in this format:

    {{
    "name":"",
    "contact_details":[
        {{
        "email":"",
        "phone_number":"",
        "address":"",
        "location":""
        }}
        ],
    "skills": [],
    "experience": [
        {{
        "company": "",
        "role": "",
        "duration": "",
        "description": ""
        }}
    ],
    "total_experience": "",
    "internship": [
        {{
        "company": "",
        "role": "",
        "duration": "",
        "description": ""
        }}
    ],
    "projects": [
        {{
        "name": "",
        "description": "",
        "skills": []
        }}
    ],
    "education": [
    {{
    "institution":"",
    "degree":"",
    "cgpa":"",
    "duration":""
    }}
    ],
    "certifications": [{{
    "certifications":"",
    "duration":""
    }}],
    "training": [
        {{
        "title": "",
        "description": ""
        }}
    ]
    }}

    Rules:
    - Extract ALL skills from entire resume
    - Infer skills where possible 
    - Do NOT include explanation, only JSON
    - If section missing, return empty list []
    - Keep descriptions short but meaningful
    - Understand the meaning of each company experience and return according to structure dont mix the work experience

    Duration Extraction Rules (CRITICAL):
    - Each experience/internship/education/certifications entry must have ONLY its OWN duration — never borrow or merge dates from another entry
    - Duration must appear in the same block/paragraph as the company and role it belongs to
    - Format duration exactly as it appears in the resume (e.g. "Jan 2022 – Mar 2023", "2021 - Present")
    - If no duration is found specifically for that entry, set duration to ""
    - Do NOT infer, guess, or carry over dates from adjacent entries
    - Process each job entry independently — do not let one entry's dates bleed into another

    Experience Separation Rules (CRITICAL):
    - Read and understand each company's experience block as a whole before categories
    - understand the meaning of each company's experience and categories accordingly
    - Each company must be a completely separate object in the list — never merge two companies into one
    - The company name, role, duration, and description must all belong to the SAME experience block
    - Do NOT mix bullet points, responsibilities, or descriptions from one company into another
    - If the candidate worked at the same company twice with different roles, create two separate entries
    - Preserve the exact order of experiences as they appear in the resume

    Total_Experience Rules (CRITICAL):
    - Calculate the duration which mentioned in experience section and give the overall experience in months
    - Calculate the total duration from start to end date and return strictly as an integer in months only (e.g. 6, 12, 18, 24) — no decimals, no text, no units, no null — if duration cannot be determined return 0

    Education Rules (CRITICAL):
    - Extract Institution name along with location
    
    Resume:
    {raw_text}
    """

    response = call_llm(prompt)

    #Clean and parse JSON safely
    try:
        structured_data = json.loads(response)
    except json.JSONDecodeError:
        # fallback cleanup
        content = response.strip("```json").strip("```")
        structured_data = json.loads(content)

    return structured_data

def llm_text_extract(file_bytes):

    try:
        # 1. text extraction
        extracted_content = extract_resume_text(file_bytes)
        print("extracted_content````````````````````````````",extracted_content)
        struct_output = structure_resume_with_groq(extracted_content)
        print("struct_output``````````````````````````````````",struct_output)
        if not struct_output:
            raise ValueError("LLM extraction failed")

        return struct_output, extracted_content

    except Exception as e:
        print("LLM extraction failed:", str(e))

        # -----------------------------
        # 2. Fallback → PyMuPDF
        # -----------------------------
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return " ".join([page.get_text() for page in doc])

        except Exception as fallback_error:
            raise Exception(
                f"Both LLM and fallback extraction failed: {fallback_error}"
            )
        
# def clean_llm_output(text):
#     # remove ```json and ```
#     text = re.sub(r"```json", "", text)
#     text = re.sub(r"```", "", text)

#     return text.strip()

# def parse_llm_output(text):
#     #If already dict → return directly
#     if isinstance(text, dict):
#         return text

#     try:
#         cleaned = clean_llm_output(text)
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         print("Invalid JSON from LLM")
#         return None
    
UPLOAD_DIR = "resumes/"

# def save_resume(file_bytes, filename):
#     os.makedirs(UPLOAD_DIR, exist_ok=True)

#     file_id = str(uuid.uuid4())
#     ext = filename.split(".")[-1]

#     file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")

#     with open(file_path, "wb") as f:
#         f.write(file_bytes)

#     return file_id, file_path

def get_resume_by_hash(file_hash):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, file_path
                FROM resumes
                WHERE file_hash = %s
            """, (file_hash,))
            
            return cursor.fetchone()
    finally:
        release_connection(conn)

def insert_resume(file_hash, file_path, candidate_name=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO resumes (file_hash, file_path, candidate_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (file_hash) DO NOTHING
                RETURNING id
            """, (file_hash, file_path, candidate_name))

            result = cursor.fetchone()

            if result:
                conn.commit()
                return result[0]  
            else:
                cursor.execute("""
                    SELECT id FROM resumes WHERE file_hash = %s
                """, (file_hash,))
                existing = cursor.fetchone()
                return existing[0]  

    finally:
        release_connection(conn)

def save_resume(file_bytes, filename, candidate_name=None):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_hash = generate_file_hash(file_bytes)

    # Check duplicate
    # existing_file = get_resume_by_hash(file_hash)
    # if existing_file:
    #     return existing_file["id"], existing_file["file_path"]

    ext = filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_hash}.{ext}")

    # Write only if file doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(file_bytes)

    return file_path, file_hash

def parse_llm_output(content):
    """
    Always returns a clean dictionary.
    Never crashes.
    """

    # -----------------------------
    # 1. Handle None / empty
    # -----------------------------
    if not content:
        return {}

    # -----------------------------
    # 2. If already dict → return
    # -----------------------------
    if isinstance(content, dict):
        return content

    # -----------------------------
    # 3. If it's string → clean it
    # -----------------------------
    if isinstance(content, str):

        # Remove unwanted text before/after JSON
        content = content.strip()

        #Extract JSON part only
        content = re.sub(r"^[^{]*", "", content)
        content = re.sub(r"[^}]*$", "", content)

        try:
            parsed = json.loads(content)

            # ensure dict
            if isinstance(parsed, dict):
                return parsed
            else:
                return {}

        except Exception as e:
            print("JSON parse error:", e)
            return {}

    # -----------------------------
    # 4. Unknown type
    # -----------------------------
    return {}


async def process_resume(file):

    # =============================
    # 1. Read file ONCE
    # =============================
    file_bytes = await file.read()

    # =============================
    # 2. Save file
    # =============================
    file_path, file_hash = save_resume(file_bytes, file.filename)

    # =============================
    # 3. Extract text (LLM)
    # =============================
    struct_text, text_content, *_ = llm_text_extract(file_bytes)

    print("LLM_content:", text_content)

    parsed = parse_llm_output(struct_text)

    #ensure parsed is dict
    parsed = parsed if isinstance(parsed, dict) else {}

    # =============================
    # 4. Extract fields safely
    # =============================

    # NAME
    candidate_name = parsed.get("name", "Unknown")

    # SKILLS (IMPORTANT FIX)
    skills = parsed.get("skills", [])

    if isinstance(skills, list):
        skills = [s.lower().strip() for s in skills if isinstance(s, str)]
    else:
        skills = []

    # EXPERIENCE (convert to months)
    experience_months = parsed.get("total_experience", 0)

    # if isinstance(exp, (int, float)):
    #     experience_months = int(exp * 12)
    # else:
    #     experience_months = 0

    # =============================
    # 5. Store in DB
    # =============================
    conn = get_connection()
    cursor = conn.cursor()

    try:
        #Check duplicate
        cursor.execute("""
            SELECT id FROM resumes WHERE file_hash = %s
        """, (file_hash,))
        existing = cursor.fetchone()

        if existing:
            return str(existing[0]), "Already exists"

        #Insert resume
        cursor.execute("""
            INSERT INTO resumes 
            (candidate_name, full_text, skills, experience_months, file_hash, file_path)
            VALUES (%s, %s, %s::jsonb, %s, %s, %s)
            RETURNING id;
        """, (
            candidate_name,
            text_content,
            json.dumps(skills),  
            experience_months,
            file_hash,
            file_path
        ))

        resume_id = cursor.fetchone()[0]

        # =============================
        # 6. Chunk text
        # =============================
        chunks = chunk_resume_pipeline(struct_text)

        print("Chunks:", chunks)

        # =============================
        # 7. Store chunks + embeddings
        # =============================
        for idx, doc in enumerate(chunks):

            content = doc.page_content
            metadata = doc.metadata or {}

            emb = get_embedding(content)[0]

            cursor.execute("""
                INSERT INTO chunks 
                (resume_id, chunk_text, chunk_index, metadata, embedding, tsv)
                VALUES (%s, %s, %s, %s, %s, to_tsvector('english', %s))
            """, (
                str(resume_id),
                content,
                idx,
                json.dumps(metadata),
                emb,
                content
            ))

        conn.commit()

        return str(resume_id), candidate_name

    finally:
        cursor.close()
        release_connection(conn)
