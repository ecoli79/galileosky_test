import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from typing import List, Dict, Any, Optional
from app.models import MoveRecord
from app.db_queryes import get_records, move_record, reindex_range

class Record(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)
        
    def get(self, key, default=None):
        return super().get(key, default)


class MockConnection:
    def __init__(self, mock_data: List[Dict[str, Any]] = None):
        self.data = mock_data or []
        self.fetch = AsyncMock()
        self.fetchrow = AsyncMock()
        self.execute = AsyncMock()
        self._setup_fetch_mocks()
        self._setup_fetchrow_mocks()
        self._setup_execute_mock()
    
    def _setup_fetch_mocks(self):
        async def mock_fetch(query, *args, **kwargs):
            if 'SELECT id, sort_order, record_name FROM records ORDER BY sort_order' in query:
                limit = args[0]
                offset = args[1]
                result = self.data[offset:offset+limit]
                return [Record(item) for item in result]
            elif 'SELECT id FROM records WHERE sort_order' in query:
                from_sort = args[0]
                to_sort = args[1]
                result = [r for r in self.data if from_sort <= r['sort_order'] <= to_sort]
                result.sort(key=lambda x: x['sort_order'])
                return [Record({'id': item['id']}) for item in result[:1000]]
            return []
            
        self.fetch.side_effect = mock_fetch
    
    def _setup_fetchrow_mocks(self):
        async def mock_fetchrow(query, *args, **kwargs):
            if 'SELECT id, sort_order, record_name FROM records WHERE id' in query:
                record_id = args[0]
                for record in self.data:
                    if record['id'] == record_id:
                        return Record(record)
                return None
            elif 'SELECT MIN(sort_order)' in query:
                if not self.data:
                    return Record({'min_order': None})
                min_order = min(r['sort_order'] for r in self.data)
                return Record({'min_order': min_order})
            elif 'SELECT MAX(sort_order)' in query:
                if not self.data:
                    return Record({'max_order': None})
                max_order = max(r['sort_order'] for r in self.data)
                return Record({'max_order': max_order})
            elif 'SELECT sort_order FROM records WHERE id' in query:
                record_id = args[0]
                for record in self.data:
                    if record['id'] == record_id:
                        return Record({'sort_order': record['sort_order']})
                return None
            return None
            
        self.fetchrow.side_effect = mock_fetchrow
    
    def _setup_execute_mock(self):
        async def mock_execute(query, *args, **kwargs):
            if 'UPDATE records SET sort_order' in query:
                new_order = args[0]
                record_id = args[1]
                for record in self.data:
                    if record['id'] == record_id:
                        record['sort_order'] = new_order
                        break
            return None
            
        self.execute.side_effect = mock_execute
        
    async def _fetch(self, query, from_sort, to_sort):
        return [row for row in self.data if from_sort <= row['sort_order'] <= to_sort]
    
    def update_mock_data(self, new_data):
        self.data = new_data
        self._setup_fetch_mocks()
        self._setup_fetchrow_mocks()
        self._setup_execute_mock()


@pytest.mark.asyncio
async def test_get_records_success():
    mock_data = [
        {'id': 1, 'sort_order': 1000, 'record_name': 'Record 1'},
        {'id': 2, 'sort_order': 2000, 'record_name': 'Record 2'},
        {'id': 3, 'sort_order': 3000, 'record_name': 'Record 3'},
        {'id': 4, 'sort_order': 4000, 'record_name': 'Record 4'},
        {'id': 5, 'sort_order': 5000, 'record_name': 'Record 5'}
    ]
    
    mock_conn = MockConnection(mock_data)
    
    result = await get_records(mock_conn, limit=3, offset=1)
    
    assert len(result) == 3
    assert result[0]['id'] == 2
    assert result[1]['id'] == 3
    assert result[2]['id'] == 4

    mock_conn.fetch.assert_awaited_once()
    args = mock_conn.fetch.call_args[0]
    assert 'SELECT id, sort_order, record_name FROM records ORDER BY sort_order' in args[0]
    assert args[1] == 3  # limit
    assert args[2] == 1  # offset


@pytest.mark.asyncio
async def test_get_records_empty():
    mock_conn = MockConnection([])
    result = await get_records(mock_conn, limit=10, offset=0)
    
    assert len(result) == 0

    mock_conn.fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_records_exception():
    mock_conn = MockConnection([])
    
    mock_conn.fetch.side_effect = Exception('Database error')
    
    result = await get_records(mock_conn, limit=10, offset=0)
    
    # must be will empty list
    assert len(result) == 0

    mock_conn.fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_move_record_wrong_input():
    mock_data = [
        {'id': 1, 'sort_order': 1000, 'record_name': 'Record 1'},
        {'id': 2, 'sort_order': 2000, 'record_name': 'Record 2'}
    ]
    mock_conn = MockConnection(mock_data)
  
    # wrong MoveRecord 
    move_req = MoveRecord(record_id=999, before_id=None, after_id=None)

    result = await move_record(mock_conn, move_req)

    assert result is None
    
    mock_conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_move_record_to_top():
    mock_data = [
        {'id': 1, 'sort_order': 1000, 'record_name': 'Record 1'},
        {'id': 2, 'sort_order': 2000, 'record_name': 'Record 2'},
        {'id': 3, 'sort_order': 3000, 'record_name': 'Record 3'}
    ]
    
    mock_conn = MockConnection(mock_data)
    
    # imitation right direction
    original_fetchrow = mock_conn.fetchrow.side_effect
    
    async def modified_fetchrow(query, *args, **kwargs):
        
        if 'SELECT id, sort_order, record_name FROM records WHERE id' in query and args[0] == 3:
            
            for record in mock_conn.data:
                if record['id'] == 3:
                    return [3, record['sort_order'], 'Record 3']
        return await original_fetchrow(query, *args, **kwargs)
    
    mock_conn.fetchrow.side_effect = modified_fetchrow
    
    # MoveRecord must will be set in first positon
    move_req = MoveRecord(record_id=3, before_id=None, after_id=1)
    
    result = await move_record(mock_conn, move_req)
    
    assert result['sort_order'] == 0
    
    assert mock_conn.fetchrow.call_count > 0
    
    mock_conn.execute.assert_awaited()
    

@pytest.mark.asyncio
async def test_move_record_to_bottom():
    mock_data = [
        {'id': 1, 'sort_order': 1000, 'record_name': 'Record 1'},
        {'id': 2, 'sort_order': 2000, 'record_name': 'Record 2'},
        {'id': 3, 'sort_order': 3000, 'record_name': 'Record 3'}
    ]
    
    mock_conn = MockConnection(mock_data)
    
    original_fetchrow = mock_conn.fetchrow.side_effect
    
    async def modified_fetchrow(query, *args, **kwargs):
        if 'SELECT id, sort_order, record_name FROM records WHERE id' in query and args[0] == 1:
            for record in mock_conn.data:
                if record['id'] == 1:
                    return [1, record['sort_order'], 'Record 1']
        return await original_fetchrow(query, *args, **kwargs)
    
    mock_conn.fetchrow.side_effect = modified_fetchrow
    
    move_req = MoveRecord(record_id=1, before_id=3, after_id=None)
    
    result = await move_record(mock_conn, move_req)
    assert result['sort_order'] == 4000

    assert mock_conn.fetchrow.call_count > 0
    
    mock_conn.execute.assert_awaited()


@pytest.mark.asyncio
async def test_move_record_between_records():
    mock_data = [
        {'id': 1, 'sort_order': 1000, 'record_name': 'Record 1'},
        {'id': 2, 'sort_order': 2000, 'record_name': 'Record 2'},
        {'id': 3, 'sort_order': 3000, 'record_name': 'Record 3'},
        {'id': 4, 'sort_order': 4000, 'record_name': 'Record 4'},
        {'id': 5, 'sort_order': 5000, 'record_name': 'Record 5'}
    ]
    
    mock_conn = MockConnection(mock_data)

    original_fetchrow = mock_conn.fetchrow.side_effect
    
    async def modified_fetchrow(query, *args, **kwargs):
        if 'SELECT id, sort_order, record_name FROM records WHERE id' in query and args[0] == 4:
            for record in mock_conn.data:
                if record['id'] == 4:
                    return [4, record['sort_order'], 'Record 4']
        return await original_fetchrow(query, *args, **kwargs)
    
    mock_conn.fetchrow.side_effect = modified_fetchrow
    
    move_req = MoveRecord(record_id=4, before_id=2, after_id=1)
    
    result = await move_record(mock_conn, move_req)
    assert result['sort_order'] == 1500
    
    assert mock_conn.fetchrow.call_count > 0
   
    mock_conn.execute.assert_awaited()


@pytest.mark.asyncio
async def test_reindex_range():
    mock_data = [
        {'id': 1, 'sort_order': 1000, 'record_name': 'Record 1'},
        {'id': 2, 'sort_order': 1001, 'record_name': 'Record 2'},  
        {'id': 3, 'sort_order': 1002, 'record_name': 'Record 3'}, 
        {'id': 4, 'sort_order': 2000, 'record_name': 'Record 4'}
    ]
    
    # save initial mock_data
    initial_data = [dict(record) for record in mock_data]
    
    mock_conn = MockConnection(mock_data)
    
    async def custom_fetch(query, *args, **kwargs):
        from_sort = args[0]
        to_sort = args[1]
        return [{'id': r['id']} for r in mock_data if from_sort <= r['sort_order'] <= to_sort]

    mock_conn.fetch.side_effect = custom_fetch
    
    async def custom_execute(query, *args, **kwargs):
        new_order = args[0]
        record_id = args[1]
        for r in mock_data:
            if r['id'] == record_id:
                r['sort_order'] = new_order
                break

    mock_conn.execute.side_effect = custom_execute
    
    await reindex_range(mock_conn, from_sort=1001, to_sort=1003)
    
    mock_conn.fetch.assert_awaited_once()
    assert mock_conn.execute.call_count == 2
    mock_data[2]['sort_order'] == 1001
    mock_data[3]['sort_order'] == 2001

