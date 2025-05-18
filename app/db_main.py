import asyncpg
import os

dbname = os.getenv('POSTGRES_DB')
user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')
host = os.getenv('POSTGRES_HOST')
port = os.getenv('POSTGRES_PORT')

URL_PG = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'

async def get_conn():
    conn = await asyncpg.connect(URL_PG) 
    return conn


