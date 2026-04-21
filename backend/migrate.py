import sqlite3
import os

db_path = "rag.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("ALTER TABLE chat_sessions ADD COLUMN mode VARCHAR DEFAULT 'NORMAL';")
    print("Added mode column.")
except Exception as e:
    print("mode column failed:", e)

try:
    c.execute("ALTER TABLE chat_sessions ADD COLUMN topic VARCHAR;")
    print("Added topic column.")
except Exception as e:
    print("topic column failed:", e)

# The learning_states table will be created automatically by SQLAlchemy via main.py or similar,
# but we can also just run Create_all here to be safe.
from app.core.database import Base, engine
import app.models  # Ensures all models are loaded
try:
    Base.metadata.create_all(bind=engine)
    print("SQLAlchemy create_all complete.")
except Exception as e:
    print("create_all failed:", e)

conn.commit()
conn.close()
