import hashlib
from sqlalchemy import create_engine, text

# 🔧 Update with your DB URL
DB_URL = "postgresql://postgres:Sid1998@localhost:5432/autodatapipe"

def get_engine():
    return create_engine(DB_URL)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_users_table():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """))
        conn.commit()

def signup_user(username: str, password: str) -> str:
    engine = get_engine()
    hashed = hash_password(password)

    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (username, password) VALUES (:u, :p)"),
                {"u": username, "p": hashed}
            )
            conn.commit()
        return "success"
    except Exception:
        return "exists"

def login_user(username: str, password: str) -> bool:
    engine = get_engine()
    hashed = hash_password(password)

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE username=:u AND password=:p"),
            {"u": username, "p": hashed}
        ).fetchone()

    return result is not None