
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# def structure_to_documents(structured_data):
#     docs = []

#     name = structured_data.get("name", "")
#     contact_details = structured_data.get("contact_details", [])

#     #Helper: attach common metadata
#     def base_metadata(section):
#         return {
#             "section": section,
#             "candidate_name": name
#         }

#     #Name + Contact (VERY IMPORTANT)
#     if name or contact_details:
#         contact_text = f"Name: {name}\n"

#         for contact in contact_details:
#             contact_text += f"""
#             Email: {contact.get('email', '')}
#             Phone: {contact.get('phone_number', '')}
#             Location: {contact.get('location', '')}
#             Address: {contact.get('address', '')}
#             """

#         docs.append(
#             Document(
#                 page_content=contact_text.strip(),
#                 metadata=base_metadata("contact")
#             )
#         )

#     #Skills
#     if structured_data.get("skills"):
#         docs.append(
#             Document(
#                 page_content=", ".join(structured_data["skills"]),
#                 metadata=base_metadata("skills")
#             )
#         )

#     #Experience
#     for exp in structured_data.get("experience", []):
#         content = f"""
#         Role: {exp.get('role', '')}
#         Company: {exp.get('company', '')}
#         Duration: {exp.get('duration', '')}
#         {exp.get('description', '')}
#         """

#         docs.append(
#             Document(
#                 page_content=content.strip(),
#                 metadata={
#                     **base_metadata("experience"),
#                     "company": exp.get("company"),
#                     "role": exp.get("role")
#                 }
#             )
#         )

#     #Internship
#     for intern in structured_data.get("internship", []):
#         content = f"""
#         Role: {intern.get('role', '')}
#         Company: {intern.get('company', '')}
#         Duration: {intern.get('duration', '')}
#         {intern.get('description', '')}
#         """

#         docs.append(
#             Document(
#                 page_content=content.strip(),
#                 metadata={
#                     **base_metadata("internship"),
#                     "company": intern.get("company"),
#                     "role": intern.get("role")
#                 }
#             )
#         )

#     #Education
#     for edu in structured_data.get("education", []):
#         content = f"""
#         Institution: {edu.get('institution', '')}
#         Degree: {edu.get('degree', '')}
#         CGPA: {edu.get('cgpa', '')}
#         Duration: {edu.get('duration', '')}
#         """

#         docs.append(
#             Document(
#                 page_content=content.strip(),
#                 metadata=base_metadata("education")
#             )
#         )

#     #Projects
#     for proj in structured_data.get("projects", []):
#         content = f"""
#         Project: {proj.get('name', '')}
#         {proj.get('description', '')}
#         Skills: {", ".join(proj.get("skills", []))}
#         """

#         docs.append(
#             Document(
#                 page_content=content.strip(),
#                 metadata={
#                     **base_metadata("projects"),
#                     "project_name": proj.get("name")
#                 }
#             )
#         )

#     #Certifications
#     for cert in structured_data.get("certifications", []):
#         docs.append(
#             Document(
#                 page_content=cert,
#                 metadata=base_metadata("certifications")
#             )
#         )

#     #Training
#     for train in structured_data.get("training", []):
#         content = f"""
#         Title: {train.get('title', '')}
#         {train.get('description', '')}
#         """

#         docs.append(
#             Document(
#                 page_content=content.strip(),
#                 metadata=base_metadata("training")
#             )
#         )

#     return docs

def structure_to_documents(structured_data):
    docs = []

    name = structured_data.get("name", "")
    contact_details = structured_data.get("contact_details", [])

    # =========================
    # Helper: base metadata
    # =========================
    def base_metadata(section):
        return {
            "section": section,
            "candidate_name": name
        }

    # =========================
    # CONTACT SECTION (FIXED)
    # =========================
    if name or contact_details:
        contact_text = f"Name: {name}\n"

        emails = []
        phones = []
        locations = []
        addresses = []

        for contact in contact_details:
            email = contact.get("email", "")
            phone = contact.get("phone_number", "")
            location = contact.get("location", "")
            address = contact.get("address", "")

            if email:
                emails.append(email)
            if phone:
                phones.append(phone)
            if location:
                locations.append(location)
            if address:
                addresses.append(address)

            contact_text += f"""
            Email: {email}
            Phone: {phone}
            Location: {location}
            Address: {address}
            """

        docs.append(
            Document(
                page_content=contact_text.strip(),
                metadata={
                    **base_metadata("contact"),
                    "emails": emails,
                    "phones": phones,
                    "locations": locations,
                    "addresses": addresses,

                    # Normalized fields (important for filtering)
                    "locations_normalized": [loc.lower() for loc in locations]
                }
            )
        )

    # =========================
    # SKILLS
    # =========================
    skills = structured_data.get("skills", [])
    if skills:
        docs.append(
            Document(
                page_content=", ".join(skills),
                metadata={
                    **base_metadata("skills"),
                    "skills": skills,
                    "skills_normalized": [s.lower() for s in skills]
                }
            )
        )

    # =========================
    # EXPERIENCE
    # =========================
    for exp in structured_data.get("experience", []):
        content = f"""
        Role: {exp.get('role', '')}
        Company: {exp.get('company', '')}
        Duration: {exp.get('duration', '')}
        {exp.get('description', '')}
        """

        docs.append(
            Document(
                page_content=content.strip(),
                metadata={
                    **base_metadata("experience"),
                    "company": exp.get("company", ""),
                    "role": exp.get("role", ""),
                    "company_normalized": exp.get("company", "").lower(),
                    "role_normalized": exp.get("role", "").lower()
                }
            )
        )

    # =========================
    # INTERNSHIP
    # =========================
    for intern in structured_data.get("internship", []):
        content = f"""
        Role: {intern.get('role', '')}
        Company: {intern.get('company', '')}
        Duration: {intern.get('duration', '')}
        {intern.get('description', '')}
        """

        docs.append(
            Document(
                page_content=content.strip(),
                metadata={
                    **base_metadata("internship"),
                    "company": intern.get("company", ""),
                    "role": intern.get("role", ""),
                    "company_normalized": intern.get("company", "").lower(),
                    "role_normalized": intern.get("role", "").lower()
                }
            )
        )

    # =========================
    # EDUCATION
    # =========================
    for edu in structured_data.get("education", []):
        content = f"""
        Institution: {edu.get('institution', '')}
        Degree: {edu.get('degree', '')}
        CGPA: {edu.get('cgpa', '')}
        Duration: {edu.get('duration', '')}
        """

        docs.append(
            Document(
                page_content=content.strip(),
                metadata={
                    **base_metadata("education"),
                    "institution": edu.get("institution", ""),
                    "degree": edu.get("degree", ""),
                    "institution_normalized": edu.get("institution", "").lower(),
                    "degree_normalized": edu.get("degree", "").lower()
                }
            )
        )

    # =========================
    # PROJECTS
    # =========================
    for proj in structured_data.get("projects", []):
        skills = proj.get("skills", [])

        content = f"""
        Project: {proj.get('name', '')}
        {proj.get('description', '')}
        Skills: {", ".join(skills)}
        """

        docs.append(
            Document(
                page_content=content.strip(),
                metadata={
                    **base_metadata("projects"),
                    "project_name": proj.get("name", ""),
                    "skills": skills,
                    "skills_normalized": [s.lower() for s in skills]
                }
            )
        )

    # # =========================
    # # CERTIFICATIONS
    # # =========================
    # for cert in structured_data.get("certifications", []):
    #     docs.append(
    #         Document(
    #             page_content=cert,
    #             metadata=base_metadata("certifications")
    #         )
    #     )

    # =========================
    # CERTIFICATIONS
    # =========================
    for cert in structured_data.get("certifications", []):
        
        cert_name = cert.get("certifications", "")
        duration = cert.get("duration", "")

        content = f"Certification: {cert_name}\nDuration: {duration}"

        docs.append(
            Document(
                page_content=content,
                metadata=base_metadata("certifications")
            )
        )

    # =========================
    # TRAINING
    # =========================
    for train in structured_data.get("training", []):
        content = f"""
        Title: {train.get('title', '')}
        {train.get('description', '')}
        """

        docs.append(
            Document(
                page_content=content.strip(),
                metadata={
                    **base_metadata("training"),
                    "title": train.get("title", ""),
                    "title_normalized": train.get("title", "").lower()
                }
            )
        )

    return docs

def apply_semantic_chunking(documents):

    #Use SentenceTransformer via LangChain wrapper
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile"
    )

    final_docs = []

    for doc in documents:
        section = doc.metadata.get("section", "")

        #Apply only for large sections
        if section in ["experience", "projects"]:
            chunks = splitter.split_text(doc.page_content)

            for chunk in chunks:
                final_docs.append(
                    Document(
                        page_content=chunk,
                        metadata=doc.metadata
                    )
                )
        else:
            final_docs.append(doc)

    return final_docs

def normalize_skills(text):
    text = text.lower()

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

    #contact details
    "contact_details": ["email", "phone", "mobile", "contact", "address"],

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

    found = []

    for skill, tags in mapping.items():
        if skill in text:
            found.append(skill)
            found.extend(tags)

    return list(set(found))


def enrich_documents(documents):
    enriched_docs = []

    for doc in documents:
        skills = normalize_skills(doc.page_content)

        metadata = doc.metadata.copy()
        metadata["skills_normalized"] = skills

        enriched_docs.append(
            Document(
                page_content=doc.page_content,
                metadata=metadata
            )
        )

    return enriched_docs

def chunk_resume_pipeline(structured_data):
    # Step 1 → structure already done
    docs = structure_to_documents(structured_data)

    # Step 2 → semantic chunking
    docs = apply_semantic_chunking(docs)

    # Step 3 → enrichment
    docs = enrich_documents(docs)

    return docs