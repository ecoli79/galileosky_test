import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db_main import get_conn

# fake data
fake_records = [
    {'id': 1, 'sort_order': 1000, 'record_name': 'Record 1'},
    {'id': 2, 'sort_order': 1001, 'record_name': 'Record 2'},  
    {'id': 3, 'sort_order': 1002, 'record_name': 'Record 3'}, 
    {'id': 4, 'sort_order': 2000, 'record_name': 'Record 4'}
]

fake_move_result = {'status': 'success', 'moved_id': 1}


@pytest.mark.asyncio
async def test_read_records(mocker):
    # Мокаем зависимости
    mock_conn = mocker.AsyncMock()
    mock_conn.close = mocker.AsyncMock()
    mocker.patch('app.main.get_conn', return_value=mock_conn)
    mocker.patch('app.main.get_records', return_value=[
       fake_records[0]
    ])

    transport = ASGITransport(app=app, raise_app_exceptions=True)

    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/records?limit=1&offset=0')

    assert response.status_code == 200
    assert response.json()[0] == {'id': 1, 'sort_order': 1000,  'record_name': 'Record 1'}


@pytest.mark.asyncio
async def test_move_record(mocker):
    mock_conn = mocker.AsyncMock()
    mocker.patch('app.main.get_conn', return_value=mock_conn)
    mocker.patch('app.main.move_record', return_value={'status': 'ok'})

    payload = {
        'record_id': 2,
        'before_id': 1,
        'after_id': 3
    }

    transport = ASGITransport(app=app, raise_app_exceptions=True)

    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.post('/records/move', json = payload)

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}