from src.database.db_connections import get_connection, release_connection
from src.utils.llm_groq import call_llm
import json
import re
from psycopg2.extras import RealDictCursor

mapping = {
    # Frontend Frameworks & Libraries
    "react": ["frontend", "ui", "ui/ux design", "javascript"],
    "angular": ["frontend", "ui", "ui/ux design", "typescript"],
    "vue": ["frontend", "ui", "ui/ux design", "javascript"],
    "svelte": ["frontend", "ui", "ui/ux design", "javascript"],
    "next.js": ["frontend", "ssr", "react"],
    "nuxt": ["frontend", "ssr", "vue"],
    "gatsby": ["frontend", "static site generation"],

    # Core Web
    "html": ["frontend", "web"],
    "css": ["frontend", "web"],
    "javascript": ["frontend", "scripting"],
    "typescript": ["frontend", "javascript"],
    "sass": ["frontend", "css"],
    "tailwind": ["frontend", "css", "ui"],
    "bootstrap": ["frontend", "css", "ui"],

    # Backend Frameworks
    "node": ["backend", "javascript"],
    "express": ["backend", "node", "api"],
    "django": ["backend", "python", "web"],
    "flask": ["backend", "python", "api"],
    "fastapi": ["backend", "python", "api"],
    "spring": ["backend", "java"],
    "laravel": ["backend", "php"],
    "rails": ["backend", "ruby"],
    "asp.net": ["backend", "c#", ".net"],
    "nest.js": ["backend", "node", "typescript"],

    # Languages
    "python": ["backend", "scripting"],
    "java": ["backend", "oop"],
    "c#": ["backend", "oop", ".net"],
    "c++": ["systems", "oop"],
    "go": ["backend", "systems"],
    "rust": ["systems", "backend"],
    "php": ["backend", "web"],
    "ruby": ["backend", "scripting"],
    "kotlin": ["mobile", "android", "jvm"],
    "swift": ["mobile", "ios"],
    "dart": ["mobile", "flutter"],
    "scala": ["backend", "jvm", "data"],
    "r": ["data science", "statistics"],

    # Databases
    "mysql": ["database", "sql", "relational"],
    "postgresql": ["database", "sql", "relational"],
    "sqlite": ["database", "sql"],
    "mongodb": ["database", "nosql"],
    "redis": ["database", "nosql", "caching"],
    "cassandra": ["database", "nosql", "distributed"],
    "elasticsearch": ["database", "search", "nosql"],
    "firebase": ["database", "nosql", "cloud"],
    "dynamodb": ["database", "nosql", "aws"],
    "oracle": ["database", "sql", "relational"],
    "mssql": ["database", "sql", "relational"],

    # Cloud & DevOps
    "aws": ["cloud", "devops"],
    "azure": ["cloud", "devops"],
    "gcp": ["cloud", "devops"],
    "docker": ["devops", "containerization"],
    "kubernetes": ["devops", "containerization", "orchestration"],
    "terraform": ["devops", "infrastructure as code"],
    "ansible": ["devops", "automation"],
    "jenkins": ["devops", "ci/cd"],
    "github actions": ["devops", "ci/cd"],
    "gitlab ci": ["devops", "ci/cd"],
    "nginx": ["devops", "web server"],
    "linux": ["devops", "systems"],

    # Data & AI/ML
    "pandas": ["data science", "python"],
    "numpy": ["data science", "python"],
    "scikit-learn": ["machine learning", "python"],
    "tensorflow": ["deep learning", "machine learning"],
    "pytorch": ["deep learning", "machine learning"],
    "keras": ["deep learning", "machine learning"],
    "spark": ["big data", "distributed computing"],
    "hadoop": ["big data", "distributed computing"],
    "tableau": ["data visualization", "analytics"],
    "power bi": ["data visualization", "analytics"],
    "opencv": ["computer vision", "machine learning"],
    "nlp": ["machine learning", "ai", "genai", "generativeai"],
    "llm": ["ai", "machine learning", "nlp", "genai", "generativeai"],

    # Mobile
    "react native": ["mobile", "frontend", "javascript"],
    "flutter": ["mobile", "dart"],
    "android": ["mobile", "java", "kotlin"],
    "ios": ["mobile", "swift"],

    # Tools & Misc
    "git": ["version control", "devops"],
    "graphql": ["api", "backend", "frontend"],
    "rest": ["api", "backend"],
    "websocket": ["backend", "real-time"],
    "kafka": ["backend", "messaging", "distributed"],
    "rabbitmq": ["backend", "messaging"],
    "microservices": ["backend", "architecture"],
    "agile": ["project management", "methodology"],
    "scrum": ["project management", "agile"],
    }

def parse_query_llm(user_query: str):

    # prompt = f"""
    # You are an intelligent HR query parser.

    # Your task is to analyze the user query and return structured JSON with:
    # 1. intent: one of ["download", "filter", "qa"]
    # 2. filters:
    #     - skills (list)
    #     - experience:
    #         - min (number in months, nullable)
    #         - max (number in months, nullable)

    # ----------------------------------
    # CORE UNDERSTANDING RULES
    # ----------------------------------

    # You must understand the USER'S INTENT, not just keywords.

    # There are 3 types of queries:

    # 1. FILTER (Candidate Search)
    # - User wants to FIND candidates based on attributes
    # - If user explicitly asks only about skills or experience then return as filter intent otherwise return as "QA" intent

    # Examples:
    # - "python developers with 2 years experience"
    # - "show candidates skilled in AI"
    # - "filter frontend developers"
    # - "list freshers"

    # These queries target PEOPLE (candidates)

    # ---

    # 2. DOWNLOAD (Resume Retrieval)
    # → User explicitly asks for resumes

    # Examples:
    # - "give me resume"
    # - "download resume of Arun"
    # - "get CV of candidate"

    # ---

    # 3. QA (Information / Relationship / Context Queries)
    # → User is asking about:
    # - projects
    # - work done
    # - relationships (who worked on what)
    # - candidate details
    # - general questions

    # Examples:
    # - "what skills does Arun have"
    # - "who worked on NLP projects"
    # - "list projects related to computer vision and by whom"
    # - "what projects has Rahul done"

    # These queries target INFORMATION, not filtering

    # ----------------------------------
    # CRITICAL DISAMBIGUATION RULES
    # ----------------------------------

    # 1. DO NOT treat every keyword as a filter

    # Example:
    # "projects related to computer vision"
    # → "computer vision" is NOT a filter
    # → It is CONTEXT for a project query
    # → intent = "qa"

    # ---

    # 2. Skills should ONLY be extracted when user clearly wants to filter candidates

    # Example:
    # "python developers"
    # → skills = ["python"]

    # BUT:

    # "projects using python"
    # → skills = [] (this is QA, not filter)

    # ---

    # 3. Project-related queries

    # If query includes:
    # - "projects"
    # - "worked on"
    # - "built"
    # - "developed"
    # - "by whom"

    # → ALWAYS:
    # intent = "qa"
    # skills = []

    # ---

    # 4. Experience extraction rules

    # - "fresher", "freshers", "entry-level", "no experience"
    # → min = 0, max = 0

    # - "experienced", "working professionals"
    # → min = 1, max = null

    # - "X years experience"
    # → min = X * 12, max = X * 12

    # - "above X years", "more than X years"
    # → min = X * 12, max = null

    # - "below X years", "less than X years"
    # → min = null, max = X * 12

    # - "between X and Y years"
    # → min = X * 12, max = Y * 12

    # - If no experience mentioned:
    # → min = null, max = null

    # ---

    # 5. Skills extraction rules

    # - Extract ONLY when intent = "filter"
    # - Always return lowercase list
    # - If none → []

    # ---

    # ----------------------------------
    # INTENT DECISION LOGIC
    # ----------------------------------

    # - If user explicitly asks for resumes
    # → intent = "download"

    # - Else if user is searching/filtering candidates by attributes
    # → intent = "filter"

    # - Else
    # → intent = "qa"

    # ----------------------------------
    # OUTPUT RULES
    # ----------------------------------

    # - Always return ONLY valid JSON
    # - Always include "skills" and "experience"
    # - Do NOT return extra fields
    # - Do NOT return explanations

    # ----------------------------------
    # EXAMPLES
    # ----------------------------------

    # Query: give me resume
    # Output:
    # {{
    # "intent": "download",
    # "filters": {{
    #     "skills": [],
    #     "experience": {{ "min": null, "max": null }}
    # }}
    # }}

    # Query: python developer with 2 years
    # Output:
    # {{
    # "intent": "filter",
    # "filters": {{
    #     "skills": ["python"],
    #     "experience": {{ "min": 24, "max": 24 }}
    # }}
    # }}

    # Query: show candidates below 3 years
    # Output:
    # {{
    # "intent": "filter",
    # "filters": {{
    #     "skills": [],
    #     "experience": {{ "min": null, "max": 36 }}
    # }}
    # }}

    # Query: what skills does Arun have
    # Output:
    # {{
    # "intent": "qa",
    # "filters": {{
    #     "skills": [],
    #     "experience": {{ "min": null, "max": null }}
    # }}
    # }}

    # Query: list projects related to computer vision and by whom
    # Output:
    # {{
    # "intent": "qa",
    # "filters": {{
    #     "skills": [],
    #     "experience": {{ "min": null, "max": null }}
    # }}
    # }}

    # Query: who worked on AI projects
    # Output:
    # {{
    # "intent": "qa",
    # "filters": {{
    #     "skills": [],
    #     "experience": {{ "min": null, "max": null }}
    # }}
    # }}

    # ----------------------------------

    # Query: {user_query}
    # """

    prompt = f"""
    You are an intelligent HR query parser.

    Your task is to analyze the user query and return structured JSON with:
    1. intent: one of ["download", "filter", "qa"]
    2. filters:
        - skills (list)
        - experience:
            - min (number in months, nullable)
            - max (number in months, nullable)

    ----------------------------------
    CORE UNDERSTANDING RULES
    ----------------------------------

    You must understand the USER'S INTENT, not just keywords.

    There are 3 types of queries:

    1. FILTER (Candidate Search)
    - User wants to FIND candidates based on ONLY skills or ONLY experience or BOTH
    - The query must be purely about filtering candidates by skills and/or experience
    - If the query involves anything beyond skills/experience (projects, names, context, etc.) → use "qa" intent

    Examples:
    - "python developers with 2 years experience"
    - "show candidates skilled in AI"
    - "filter frontend developers"
    - "list freshers"
    - "candidates with more than 3 years experience"

    These queries target PEOPLE (candidates) using ONLY skill/experience criteria

    2. DOWNLOAD (Resume Retrieval)
    → User explicitly asks for resumes

    Examples:
    - "give me resume"
    - "download resume of Arun"
    - "get CV of candidate"

    3. QA (Information / Relationship / Context Queries)
    → User is asking about anything beyond skills/experience filters:
    - projects
    - work done
    - relationships (who worked on what)
    - candidate details (by name or attribute)
    - general questions

    Examples:
    - "what skills does Arun have"
    - "who worked on NLP projects"
    - "list projects related to computer vision and by whom"
    - "what projects has Rahul done"

    These queries target INFORMATION, not filtering

    ----------------------------------
    CRITICAL DISAMBIGUATION RULES
    ----------------------------------

    1. DO NOT treat every keyword as a filter

    Example:
    "projects related to computer vision"
    → "computer vision" is NOT a filter
    → It is CONTEXT for a project query
    → intent = "qa"

    2. Skills should ONLY be extracted when user clearly wants to filter candidates

    Example:
    "python developers"
    → skills = ["python"]

    BUT:

    "projects using python"
    → skills = [] (this is QA, not filter)

    3. Project-related queries

    If query includes:
    - "projects"
    - "worked on"
    - "built"
    - "developed"
    - "by whom"

    → ALWAYS:
    intent = "qa"
    skills = []

    4. Experience extraction rules

    - "fresher", "freshers", "entry-level", "no experience"
    → min = 0, max = 0

    - "experienced", "working professionals"
    → min = 1, max = null

    - "X years experience"
    → min = X * 12, max = X * 12

    - "above X years", "more than X years"
    → min = X * 12, max = null

    - "below X years", "less than X years"
    → min = null, max = X * 12

    - "between X and Y years"
    → min = X * 12, max = Y * 12

    - If no experience mentioned:
    → min = null, max = null

    5. Skills extraction rules

    - Extract ONLY when intent = "filter"
    - Always return lowercase list
    - If none → []

    ----------------------------------
    INTENT DECISION LOGIC
    ----------------------------------

    Follow this priority order:

    1. If user explicitly asks for resumes or CVs
    → intent = "download"

    2. Else if the query is STRICTLY about filtering candidates using ONLY skills and/or experience
    (no project context, no names, no relationship questions)
    → intent = "filter"

    3. Else (anything involving projects, names, context, or information lookup)
    → intent = "qa"

    ----------------------------------
    OUTPUT RULES
    ----------------------------------

    - Always return ONLY valid JSON
    - Always include "skills" and "experience"
    - Do NOT return extra fields
    - Do NOT return explanations

    ----------------------------------
    EXAMPLES
    ----------------------------------

    Query: give me resume
    Output:
    {{
    "intent": "download",
    "filters": {{
        "skills": [],
        "experience": {{ "min": null, "max": null }}
    }}
    }}

    Query: python developer with 2 years
    Output:
    {{
    "intent": "filter",
    "filters": {{
        "skills": ["python"],
        "experience": {{ "min": 24, "max": 24 }}
    }}
    }}

    Query: show candidates below 3 years
    Output:
    {{
    "intent": "filter",
    "filters": {{
        "skills": [],
        "experience": {{ "min": null, "max": 36 }}
    }}
    }}

    Query: what skills does Arun have
    Output:
    {{
    "intent": "qa",
    "filters": {{
        "skills": [],
        "experience": {{ "min": null, "max": null }}
    }}
    }}

    Query: list projects related to computer vision and by whom
    Output:
    {{
    "intent": "qa",
    "filters": {{
        "skills": [],
        "experience": {{ "min": null, "max": null }}
    }}
    }}

    Query: who worked on AI projects
    Output:
    {{
    "intent": "qa",
    "filters": {{
        "skills": [],
        "experience": {{ "min": null, "max": null }}
    }}
    }}

    Query: {user_query}
    """

    response = call_llm(prompt)

    return safe_parse_llm(response)

def safe_parse_llm(content):
    try:
        # clean garbage
        content = re.sub(r"^[^{]*", "", content)
        content = re.sub(r"[^}]*$", "", content)

        data = json.loads(content)

        if not isinstance(data, dict):
            return {"intent": "qa", "filters": {}}

        return data

    except:
        return {"intent": "qa", "filters": {}}

def get_resumes_for_download(selected_resume_ids=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if selected_resume_ids:
        cursor.execute("""
            SELECT id, candidate_name, file_path, experience_months
            FROM resumes
            WHERE id = ANY(%s::uuid[])
        """, (selected_resume_ids,))
    else:
        cursor.execute("""
            SELECT id, candidate_name, file_path, experience_months
            FROM resumes
            LIMIT 20
        """)

    rows = cursor.fetchall()

    cursor.close()
    release_connection(conn)

    return rows

BASE_URL = "http://localhost:8000"

def format_download_response(resumes):

    if not resumes:
        return "No resumes found."

    response = "Here are the resumes:\n\n"

    for i, r in enumerate(resumes, 1):

        #correct extraction
        resume_id = r["id"]
        name = r["candidate_name"]
        file_path = r["file_path"]
        exp_months = r["experience_months"]

        #safe conversion
        try:
            exp_months = float(exp_months)
        except:
            exp_months = 0

        exp = round(exp_months / 12, 1)

        response += (
            f"{i}. {name} ({exp} years)\n"
            f"{BASE_URL}/api/download/{resume_id}\n\n"
        )

    return response

def expand_skills(skills, mapping):
    expanded = set(skills)

    for skill in skills:
        if skill in mapping:
            expanded.update(mapping[skill])

    return list(expanded)

def normalize_skills(skills, reverse_map):
    normalized = set()

    for skill in skills:
        skill = skill.lower().strip()

        if skill in reverse_map:
            normalized.update(reverse_map[skill])
        else:
            normalized.add(skill)

    return list(normalized)

#BUILD REVERSE MAPPING (VARIANT → CANONICAL)
def build_reverse_map(mapping):
    reverse = {}

    for main, values in mapping.items():
        # ensure canonical maps to itself
        reverse.setdefault(main, set()).add(main)

        for v in values:
            reverse.setdefault(v, set()).add(main)

    # convert sets to lists
    return {k: list(v) for k, v in reverse.items()}

reverse_map = build_reverse_map(mapping)
print("reverse_mapping`````````````````````````````````",reverse_map)

def search_resumes(filters: dict):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        base_query = """
            SELECT id, candidate_name, experience_months, file_path
            FROM resumes
        """

        conditions = []
        params = []

        # =========================
        # RESUME ID FILTER (NEW)
        # =========================
        resume_ids = filters.get("selected_resume_ids")

        if isinstance(resume_ids, list) and resume_ids and "all" not in resume_ids:
            placeholders = ",".join(["%s"] * len(resume_ids))
            conditions.append(f"id IN ({placeholders})")
            params.extend(resume_ids)

        # =========================
        # EXPERIENCE FILTER
        # =========================
        exp = filters.get("experience", {})

        if isinstance(exp, dict):
            min_exp = exp.get("min")
            max_exp = exp.get("max")

            if min_exp is not None:
                conditions.append("experience_months >= %s")
                params.append(min_exp)

            if max_exp is not None:
                conditions.append("experience_months <= %s")
                params.append(max_exp)

        # =========================
        # SKILLS FILTER
        # =========================
        skills = filters.get("skills")

        if isinstance(skills, list) and skills:
            normalized = normalize_skills(skills, reverse_map)
            expanded = expand_skills(normalized, mapping)

            conditions.append("skills ?| %s")
            params.append(expanded)

        # =========================
        # NAME FILTER
        # =========================
        name = filters.get("name")

        if isinstance(name, str) and name.strip():
            conditions.append("candidate_name ILIKE %s")
            params.append(f"%{name}%")

        # =========================
        # ROLE FILTER
        # =========================
        role = filters.get("role")

        if isinstance(role, str) and role.strip():
            conditions.append("role ILIKE %s")
            params.append(f"%{role}%")

        # =========================
        # BUILD FINAL QUERY
        # =========================
        if conditions:
            final_query = base_query + " WHERE " + " AND ".join(conditions)
        else:
            final_query = base_query

        final_query += " LIMIT 20"

        print("Final Query:", final_query)
        print("Params:", params)

        cursor.execute(final_query, params)
        results = cursor.fetchall()

        return results

    finally:
        cursor.close()
        release_connection(conn)