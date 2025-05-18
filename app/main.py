import logging
from fastapi import FastAPI, HTTPException, Request
from db_main import get_conn
from db_queryes import get_records, move_record
from models import MoveRecord
from logger import logger

app = FastAPI()
 
@app.get('/records')
async def read_records(request: Request, limit: int = 100, offset: int = 0):
    
    logger.info(f'GET /records - limit={limit}, offset={offset}',
                extra = {
                 'client_ip': request.client.host,
                 'method': request.method  
                })
    
    try:
        conn = await get_conn()
        records = await get_records(conn, limit, offset)
        return records
    except Exception as e:
        logger.exception('Failed to fetch records', 
                         extra = {
                            'client_ip': request.client.host,
                            'method': request.method  
                         })
        raise HTTPException(status_code=500, detail='Error fetching records')
    finally:
        if conn:
            await conn.close()        

@app.post('/records/move')
async def move(request: Request):
    data = await request.json()
    logger.info(f'GET /records - data {data}',
                extra = {
                 'client_ip': request.client.host,
                 'method': request.method  
                })
    try:
        record = MoveRecord(**data)
        conn = await get_conn()
        result = await move_record(conn, record)
        return result
        
    except Exception as err:
        logger.exception('Failed to fetch records', 
                         extra = {
                            'client_ip': request.client.host,
                            'method': request.method  
                         })
        raise HTTPException(status_code = 400, detail = (str(err)))
        
        
        
        