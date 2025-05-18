import os
import psycopg2
import time

MIGRATION_DIR = '/app/migrations/'

def create_conn():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT')
        )
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f'Failed to create connection to database: {e}')


def ensure_migrations_table():
    conn = create_conn()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255),
                applied_at TIMESTAMP DEFAULT now()
            )
        ''')
        conn.commit() 


def get_applied_migrations():
    conn = create_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT version FROM schema_migrations')
            rows = cur.fetchall()
            return {row[0] for row in rows}
    except Exception as e:
        print(f'Failed to retrieve applied migrations: {e}')
        

def apply_migration(version, sql):
    conn = create_conn()
    try:
        with conn.cursor() as cur:
            print(f'Applying migration {version}...')
            for statement in sql.split(';'):
                stripped = statement.strip()
                if stripped:
                    cur.execute(stripped)
            
            cur.execute('INSERT INTO schema_migrations (version) VALUES (%s)', (version,))
            conn.commit()
        print(f'Migration {version} applied.')
    except Exception as e:
        print(f'Failed to apply migration {version}: {e}')


def parse_migration_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()
        return sql
    except Exception as e:
        print(f'Failed to read migration file {filepath}: {e}')


def generate_data():
    conn = create_conn()
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM records')
        if cur.fetchone()[0] > 0:
            return
    
    print('Generating data...')
    batch_size = 100000
    total_rows = 100000000
    
    with conn.cursor() as cur:
        cur.execute('ALTER TABLE records SET (autovacuum_enabled = off)')
        
        for i in range(0, total_rows, batch_size):
            start_time = time.time()
            cur.execute(f'''
                INSERT INTO records (record_name, sort_order)
                SELECT left(md5((s::BIGINT + {i})::text), 12), (s::BIGINT + {i}) * 1000
                FROM generate_series(1, {batch_size}) AS s
            ''')
            conn.commit()
            elapsed = time.time() - start_time
            print(f'Inserted {i + batch_size:,} rows — batch time: {elapsed:.2f}s')

        cur.execute('CREATE INDEX idx_record_name ON records(record_name)')
        cur.execute('ANALYZE records')
        cur.execute('ALTER TABLE records SET (autovacuum_enabled = on)')
        cur.execute('VACUUM FULL ANALYZE records')
        cur.execute('INSERT INTO schema_migrations (version) VALUES (%s)', ('populate data in table records',))
        conn.commit()


def main():
    ensure_migrations_table()
    applied = get_applied_migrations()

    files = sorted(f for f in os.listdir(MIGRATION_DIR) if f.endswith('.sql'))

    for filename in files:
        version = filename
        if version in applied:
            print(f'Skipping already applied migration {version}')
            continue
        
        filepath = os.path.join(MIGRATION_DIR, filename)
        sql = parse_migration_file(filepath)
        apply_migration(version, sql)
        
    # for populate data in table records
    generate_data()

if __name__ == '__main__':
    main()
