# from psycopg2.pool import SimpleConnectionPool

# pool = SimpleConnectionPool(
#     1, 10,
#     dbname="Resume-Shortlist-RAG",
#     user="postgres",
#     password="1234",
#     host="192.168.1.2",
#     port="5432"
# )

# def get_connection():
#     return pool.getconn()

# def release_connection(conn):
#     pool.putconn(conn)

#````````````````````Render DB Connection``````````````````````````````

import os
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
    sslmode="require"
)

def get_connection():
    return pool.getconn()

def release_connection(conn):
    pool.putconn(conn)