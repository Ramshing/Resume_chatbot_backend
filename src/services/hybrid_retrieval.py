from sentence_transformers import CrossEncoder
from src.database.db_connections import get_connection, release_connection
from src.services.embedding import get_embedding, get_query_embedding
import json
from collections import defaultdict
from src.utils.llm_groq import call_llm, clean_json
from datetime import date
today_date = date.today().strftime("%B %d, %Y") 

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_chunks(query, chunks, top_k=30, alpha=0.5):
    pairs = [(query, chunk["text"]) for chunk in chunks]
    scores = reranker.predict(pairs)

    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[i])

    # Normalize both scores to [0, 1] then combine
    raw_scores = [c["score"] for c in chunks]
    rerank_scores = [c["rerank_score"] for c in chunks]

    def normalize(values):
        min_v, max_v = min(values), max(values)
        if max_v == min_v:
            return [1.0] * len(values)
        return [(v - min_v) / (max_v - min_v) for v in values]

    norm_raw = normalize(raw_scores)
    norm_rerank = normalize(rerank_scores)

    for i, chunk in enumerate(chunks):
        chunk["hybrid_score"] = alpha * norm_rerank[i] + (1 - alpha) * norm_raw[i]

    ranked = sorted(chunks, key=lambda x: x["hybrid_score"], reverse=True)
    return ranked[:top_k]


def merge_results(semantic_results, keyword_results):
    import json

    combined = {}

    #Semantic
    for row in semantic_results:
        chunk_id = row[0]
        resume_id = row[1]
        text = row[2]
        metadata = row[3]

        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        combined[chunk_id] = {
            "chunk_id": chunk_id,
            "resume_id": str(resume_id),
            "text": text,
            "metadata": metadata,
            "score": 1.0
        }

    #Keyword
    for row in keyword_results:
        chunk_id = row[0]
        resume_id = row[1]
        text = row[2]
        metadata = row[3]

        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        if chunk_id in combined:
            combined[chunk_id]["score"] += 1.0
        else:
            combined[chunk_id] = {
                "chunk_id": chunk_id,
                "resume_id": str(resume_id),
                "text": text,
                "metadata": metadata,
                "score": 1.0
            }

    return list(combined.values())


def hybrid_search(query, selected_resume_ids=None, top_k=100):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if "contact" in query:
            query = query + " Email Phone Mobile Address Location"

        print("qurieeeeeeeeeeeeeeee```````````````",query)
        query_embedding = get_query_embedding(query)

        # -------------------   
        # Semantic Search
        # -------------------
        if selected_resume_ids:
            cursor.execute("""
            SELECT chunk_id, resume_id, chunk_text, metadata,
                embedding <=> %s::vector AS distance
            FROM chunks
            WHERE resume_id = ANY(%s::uuid[])
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, (
            query_embedding,
            selected_resume_ids,
            query_embedding,
            top_k
        ))
        else:
            cursor.execute("""
                SELECT chunk_id, resume_id, chunk_text, metadata,
                    embedding <=> %s::vector AS distance
                FROM chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (
                query_embedding,
                query_embedding,
                top_k
            ))

        semantic_results = cursor.fetchall()

        print("semantic_results```````````````````````````````````",semantic_results)

        # -------------------
        # Keyword Search
        # -------------------
        if selected_resume_ids:
            cursor.execute("""
                SELECT chunk_id, resume_id, chunk_text, metadata,
                    ts_rank(tsv, websearch_to_tsquery(%s)) AS rank
                FROM chunks
                WHERE tsv @@ websearch_to_tsquery(%s)
                AND resume_id = ANY(%s::uuid[])
                ORDER BY rank DESC
                LIMIT %s;
            """, (
                query,
                query,
                selected_resume_ids,
                top_k
            ))
        else:
            cursor.execute("""
                SELECT chunk_id, resume_id, chunk_text, metadata,
                    ts_rank(tsv, websearch_to_tsquery(%s)) AS rank
                FROM chunks
                WHERE tsv @@ websearch_to_tsquery(%s)
                ORDER BY rank DESC
                LIMIT %s;
            """, (
                query,
                query,
                top_k
            ))

        keyword_results = cursor.fetchall()

        print("keyword_results`````````````````````````````````````````````````````````",keyword_results)

        cursor.close()
        conn.close()

        return semantic_results, keyword_results
    finally:
        cursor.close()
        release_connection(conn)

def generate_answer(question, chunks):

    if not chunks:
        return "No relevant candidates found.", []

    # -----------------------------
    # 1. Group chunks by resume_id
    # -----------------------------
    grouped = defaultdict(list)

    for c in chunks:
        resume_id = c.get("resume_id")
        grouped[resume_id].append(c)

    # -----------------------------
    # 2. Build structured context
    # -----------------------------
    context_blocks = []

    for resume_id, candidate_chunks in grouped.items():

        metadata = candidate_chunks[0].get("metadata", {})
        candidate_name = metadata.get("candidate_name", "Unknown")

        combined_text = "\n".join([
            f"[{c['metadata'].get('section', '')}] {c['text']}"
            for c in candidate_chunks
        ])

        context_blocks.append(f"""
        Candidate Name: {candidate_name}
        Resume ID: {resume_id}

        Details:
        {combined_text}
        """)

    # limit number of candidates (NOT chunks)
    context = "\n\n".join(context_blocks[:50])

    # -----------------------------
    # 3. Strong Prompt
    # -----------------------------
    prompt = f"""
    You are an expert HR recruiter assistant.

    Your task:
    Evaluate candidates based on the question.

    Question:
    {question}

    Candidate Data:
    {context}

    =====================
    INTENT CLASSIFICATION (MANDATORY)
    =====================
    Classify the query into ONE of the following:

    1. "recruitment" → hiring, resumes, candidates, skills, experience
    2. "greeting" → hi, hello, hey, good morning, etc.
    3. "general" → unrelated questions (weather, jokes, personal chat, etc.)

    =====================
    GUARDRAILS (CRITICAL)
    =====================
    - If intent = "greeting":
    → Return a polite greeting response
    → DO NOT evaluate candidates
    → candidates = []

    - If intent = "general":
    → Return a response as "I'm designed to assist with recruitment-related queries only."
    → DO NOT evaluate candidates
    → candidates = []

    - If intent = "recruitment":
    → Proceed with full evaluation logic

    - DO NOT hallucinate candidates
    - DO NOT use data outside provided context
    - Output MUST be valid JSON ONLY

    Instructions:
    - Understand the intent of the question
    - Consider related skills (e.g., frontend includes React, Angular, UI)
    - Evaluate each candidate carefully
    - Give a score (0–10) and score should be either too low or too high, there should not be medium score 
    - If no relevant keyword or any irrelevant semantic sentences then score should be too low
    - Provide reasoning
    - Final decision: Shortlist or Reject

    Rules:
    1. Understand the user's query and extract filters such as skills, experience, role, etc.
    2. Experience should always be handled in months.

    3. Interpret experience-related keywords:
    - "fresher", "freshers", "entry-level", "no experience" → experience = 0 months
    - "experienced", "experienced candidates", "working professionals" → experience > 0 months
    - "senior" → experience >= 60 months (5+ years)
    - "junior" → experience between 6 and 24 months

    4. If experience range is mentioned:
    - Convert to months and apply range filtering

    5. If user says "experienced candidates resume":
    - Apply filter: experience_months > 0

    6. If no experience-related keyword is present:
    - Do not apply experience filter

    Examples:
    - "List all fresher candidates" → experience = 0
    - "List experienced candidates" → experience > 0
    - "Candidates with 2 years experience" → experience = 24 months

     7. LOCATION FILTER (CRITICAL):

    STEP 1 — Detect location context type from the query:
    Check if the user explicitly mentions a location in the context of:
        a) Residential / Home address      → e.g., "candidates living in Chennai", "based in Bangalore"
        b) Education institution           → e.g., "studied in Chennai", "college in Bangalore", "university in Hyderabad"
        c) Training institute              → e.g., "trained in Pune", "training from Delhi"
        d) Internship                      → e.g., "interned in Mumbai", "internship in Hyderabad"
        e) Company / Employer             → e.g., "worked in Chennai", "company in Bangalore", "currently working in Pune"

    STEP 2 — Apply the correct location filter based on detected context:
        - If context = (a) residential    → match candidates whose permanent/current home address contains the location
        - If context = (b) education      → match candidates whose college, university, or school city contains the location
        - If context = (c) training       → match candidates whose training institute location contains the location
        - If context = (d) internship     → match candidates whose internship location contains the location
        - If context = (e) company        → match candidates whose past or current employer location contains the location

    STEP 3 — Default behavior (no explicit context mentioned):
        - If the user mentions only a location/city with no context clue
        → match ONLY against the candidate's residential/permanent address
        → DO NOT infer location from education, training, internship, or company fields

    STEP 4 — STRICT CROSS-CONTEXT RULE:
        - NEVER use a location field that was NOT explicitly requested
        - e.g., if user asks "candidates who worked in Chennai" → do NOT match candidates who only live or studied in Chennai
        - e.g., if user asks "candidates from Chennai" (no context) → do NOT match candidates who only worked or studied in Chennai

    8. CURRENTLY STUDYING FILTER (CRITICAL):
    Today's date is: {today_date}

    A candidate is considered "currently studying" if ANY of the following is true:

    CASE 1 — Future end date explicitly present:
        - Education duration/end date is a future month and year (e.g., "May, 2027", "2026")
        - Degree is marked as "Pursuing", "Ongoing", "Present", "Expected: <future date>"

    CASE 2 — End date is missing or not mentioned:
        - If the Duration field is empty, cut off, or not present at all
        → ASSUME the candidate is currently studying
        → DO NOT reject or skip them

    CASE 3 — Explicitly completed:
        - Only exclude a candidate if the end date is clearly in the PAST (e.g., "May, 2023", "2022")
        - If the degree is marked as "Completed", "Graduated", "Passed Out" with a past date
        → candidate is NOT currently studying

    PRIORITY ORDER:
        1. Past end date explicitly present → NOT currently studying
        2. Future end date explicitly present → currently studying
        3. End date missing/unclear → ASSUME currently studying

    9. CONTACT DETAILS:
    - If user ask about contact details, give the email address, phone number, address and residential location

    Return ONLY valid JSON:

    {{
    "answer": "",
    "candidates": [
        {{
        "resume_id": "",
        "candidate_name": "",
        "summary": "",
        "score": 0,
        "decision": ""
        }}
    ]
    }}
    """

    # -----------------------------
    # 4. Call LLM
    # -----------------------------
    raw_output = call_llm(prompt)

    # -----------------------------
    # 5. Safe JSON parsing
    # -----------------------------
    try:
        cleaned = clean_json(raw_output)
        parsed = json.loads(cleaned)
    except Exception as e:
        print("LLM parsing failed:", e)
        return raw_output, []

    return parsed.get("answer", ""), parsed.get("candidates", "")


def retrieve_final_chunks(query, selected_resume_ids=None):

    # Step 1: hybrid retrieval
    semantic, keyword = hybrid_search(query, selected_resume_ids)

    # Step 2: merge
    merged = merge_results(semantic, keyword)

    # Step 3: rerank
    top_chunks = rerank_chunks(query, merged, top_k=30)

    # -------------------
    # Step 4: Extract candidate_ids (IMPORTANT)
    # -------------------
    candidate_ids = list(set(chunk["resume_id"] for chunk in top_chunks))

    # -------------------
    # Step 5: Detect if contact is needed
    # -------------------
    contact_keywords = ["contact", "phone", "email", "mobile", "address"]
    need_contact = any(word in query.lower() for word in contact_keywords)

    contact_chunks = []

    if need_contact and candidate_ids:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT chunk_id, resume_id, chunk_text, metadata
            FROM chunks
            WHERE resume_id = ANY(%s::uuid[])
            AND metadata->>'section' = 'contact';
        """, (candidate_ids,))

        rows = cursor.fetchall()

        for row in rows:
            metadata = row[3]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            contact_chunks.append({
                "chunk_id": row[0],
                "resume_id": str(row[1]),
                "text": row[2],
                "metadata": metadata,
                "score": 0.5  # lower than main relevance
            })

        cursor.close()
        release_connection(conn)

    # -------------------
    # Step 6: Merge contact chunks
    # -------------------
    final_chunks = top_chunks + contact_chunks

    return final_chunks
