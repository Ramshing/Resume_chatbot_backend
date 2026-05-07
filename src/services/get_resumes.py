from src.database.db_connections import get_connection, release_connection

def get_all_resumes():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, candidate_name
        FROM resumes
        ORDER BY candidate_name ASC;
    """
    cursor.execute(query)

    rows = cursor.fetchall()

    result = [
        {
            "id": str(row[0]),
            "candidate_name": row[1]
        }
        for row in rows
    ]

    cursor.close()
    release_connection(conn)

    return result