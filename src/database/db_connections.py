# from psycopg2.pool import SimpleConnectionPool

# pool = SimpleConnectionPool(
#     1, 10,
#     dbname="Resume-Shortlist-RAG",
#     user="postgres",
#     password="1234",
#     host="192.168.1.5",
#     port="5432"
# )

# def get_connection():
#     return pool.getconn()

# def release_connection(conn):
#     pool.putconn(conn)

#````````````````````Render DB Connection``````````````````````````````

import os

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

pool = None


def get_pool():
    global pool

    if pool is None:
        pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
            sslmode="require",
            connect_timeout=10,
        )

    return pool


def get_connection():
    return get_pool().getconn()


def release_connection(conn):
    if conn:
        get_pool().putconn(conn)