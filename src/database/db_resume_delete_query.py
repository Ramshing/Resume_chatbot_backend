from src.database.db_connections import get_connection, release_connection

def delete_resume_from_db(resume_id: str):
    try: 
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM resumes WHERE id = %s RETURNING id", (resume_id,))
        deleted = cursor.fetchone()

        conn.commit()
        cursor.close()
        conn.close()

        return deleted
    finally:
            release_connection(conn)