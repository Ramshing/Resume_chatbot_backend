from src.database.db_connections import get_connection, release_connection

def insert_resume(candidate_name, text, skills, experience):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO resumes (candidate_name, full_text, skills, experience_years)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (candidate_name, text, skills, experience))

        resume_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return resume_id
    finally:
        release_connection(conn)