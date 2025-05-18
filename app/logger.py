import logging
import json
import asyncpg
import asyncio
from db_main import URL_PG
from typing import Optional

class AsyncPostgresHandler(logging.Handler):
    def __init__(self, dsn: str):
        super().__init__()
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def init(self):
        if not self._initialized:
            async with self._init_lock:
                if not self._initialized:
                    self.pool = await asyncpg.create_pool(dsn=self.dsn)
                    self._initialized = True

    async def _write_log(self, record: logging.LogRecord):
        await self.init()

        query = getattr(record, "query", None)
        params = getattr(record, "params", None)
        error = getattr(record, "error", None)

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO query_logs (level, message, query, params, error)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    record.levelname,
                    record.getMessage(),
                    query,
                    json.dumps(params) if params else None,
                    error
                )
        except Exception as e:
            print(f"[Logger] Failed to write log: {e}")

    def emit(self, record):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._write_log(record))
        except RuntimeError:
            asyncio.run(self._write_log(record))

pg_handler = AsyncPostgresHandler(URL_PG)

logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
logger.addHandler(pg_handler)