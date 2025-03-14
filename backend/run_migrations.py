import os
import sys
from pathlib import Path

def run_migrations():
    # Add the backend directory to Python path
    backend_dir = Path(__file__).parent.absolute()
    sys.path.append(str(backend_dir))
    
    # Import and run Alembic commands
    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    run_migrations() 