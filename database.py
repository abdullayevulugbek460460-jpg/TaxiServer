import os
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "")


@contextmanager
def get_connection():
    """
    PostgreSQL connection.
    psycopg3 production muhitida ishlatiladi.
    """
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL sozlanmagan")

    try:
        import psycopg
    except ImportError:
        raise RuntimeError(
            "psycopg PostgreSQL driver o‘rnatilmagan"
        )

    conn = psycopg.connect(DATABASE_URL)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    phone VARCHAR(30) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    phone VARCHAR(30) UNIQUE NOT NULL,
                    login VARCHAR(80) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    car_model VARCHAR(120) DEFAULT '',
                    car_number VARCHAR(40) DEFAULT '',
                    approved BOOLEAN DEFAULT FALSE,
                    online BOOLEAN DEFAULT FALSE,
                    balance NUMERIC(12,2) DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS driver_locations (
                    driver_id BIGINT PRIMARY KEY REFERENCES drivers(id)
                        ON DELETE CASCADE,
                    latitude DOUBLE PRECISION NOT NULL,
                    longitude DOUBLE PRECISION NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id BIGSERIAL PRIMARY KEY,
                    passenger_id BIGINT REFERENCES users(id),
                    driver_id BIGINT REFERENCES drivers(id),
                    pickup_lat DOUBLE PRECISION NOT NULL,
                    pickup_lng DOUBLE PRECISION NOT NULL,
                    destination_lat DOUBLE PRECISION NOT NULL,
                    destination_lng DOUBLE PRECISION NOT NULL,
                    estimated_distance_km NUMERIC(10,2) DEFAULT 0,
                    estimated_price NUMERIC(12,2) DEFAULT 0,
                    status VARCHAR(40) NOT NULL DEFAULT 'NEW',
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(80) PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            cur.execute("""
                INSERT INTO settings (key, value)
                VALUES
                    ('start_price', '5000'),
                    ('price_per_km', '2000'),
                    ('minimum_price', '10000'),
                    ('commission_percent', '10')
                ON CONFLICT (key) DO NOTHING
            """)

    return True
