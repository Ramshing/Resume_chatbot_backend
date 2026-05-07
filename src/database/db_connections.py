from psycopg2.pool import SimpleConnectionPool

pool = SimpleConnectionPool(
    1, 10,
    dbname="Resume-Shortlist-RAG",
    user="postgres",
    password="1234",
    host="192.168.1.3",
    port="5432"
)

def get_connection():
    return pool.getconn()

def release_connection(conn):
    pool.putconn(conn)