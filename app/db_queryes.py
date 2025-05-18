from models import MoveRecord
from logger import logger


async def get_records(conn, limit: int, offset: int):
    rows = []
    try:
        rows = await conn.fetch(
            'SELECT id, sort_order, record_name FROM records ORDER BY sort_order LIMIT $1 OFFSET $2', limit, offset
        )
    except Exception as ex:
        logger.error(f'While get records raise is error: {ex}')

    return [dict(row) for row in rows]


async def move_record(conn, move_record: MoveRecord):
    record = await conn.fetchrow('SELECT id, sort_order, record_name FROM records WHERE id = $1', move_record.record_id)
    if not record:
        return None   
    
    new_order = None
    
    # for case if not elements before 
    if move_record.before_id is None:
        min_order = await conn.fetchrow('SELECT MIN(sort_order) as min_order FROM records')
        if min_order and min_order['min_order'] is not None:
            new_order = min_order['min_order'] - 1000
        else:
            new_order = 1000  # if empty table
        
    # for case if not elements after
    elif move_record.after_id is None:
        max_order = await conn.fetchrow('SELECT MAX(sort_order) as max_order FROM records')
        if max_order and max_order['max_order'] is not None:
            new_order = max_order['max_order'] + 1000
        else:
            new_order = 100  # if empty table
    
    
    # for all other cases
    else:
        before_order = None
        after_order = None
        if move_record.before_id:
            before_row = await conn.fetchrow('SELECT sort_order FROM records WHERE id = $1', move_record.before_id)
            before_order = before_row['sort_order']
        if move_record.after_id:
            after_row = await conn.fetchrow('SELECT sort_order FROM records WHERE id = $1', move_record.after_id)
            after_order = after_row['sort_order']
        
        if before_order and after_order:
            new_order = (after_order + before_order) // 2
            
        if after_order is not None and abs(after_order - before_order) <= 1:
            reindex_range(conn, after_order, before_order)
            new_order = move_record(conn, move_record)['sort_order']
       
   
    await conn.execute('UPDATE records SET sort_order = $1 WHERE id = $2', new_order, move_record.record_id)
    logger.info(f'Updated sort_order for record_id: {move_record.record_id} to {new_order}')
       
    record_new = await conn.fetchrow('SELECT id, sort_order, record_name FROM records WHERE id = $1', move_record.record_id)
     
    return {'id': record_new[0], 'sort_order': record_new[1], 'record_name': record_new[2]}


async def reindex_range(conn, from_sort: int, to_sort: int):
    rows = await conn.fetch('''
        SELECT id FROM records
        WHERE sort_order BETWEEN $1 AND $2
        ORDER BY sort_order
        LIMIT 1000
    ''', from_sort, to_sort)

    for index, row in enumerate(rows):
        new_order = (((index + 1) * 1000) + 1)
        await conn.execute('UPDATE records SET sort_order = $1 WHERE id = $2', new_order, row['id'])
        logger.info(f'Reindexed records from {from_sort} to {to_sort}, was update is {len(rows)} rows')
