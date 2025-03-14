import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from app.db.base import Base
from app.db.session import engine

def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    drop_tables()
    print("Database tables dropped successfully.") 