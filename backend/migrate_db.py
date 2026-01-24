from backend.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        print("Migrating database schema to support Google OAuth...")
        try:
            # users table modifications
            conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN mobile_number DROP NOT NULL"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN date_of_birth DROP NOT NULL"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN time_of_birth DROP NOT NULL"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN location DROP NOT NULL"))
            
            # These might already be nullable depending on initial creation, but good to ensure
            conn.execute(text("ALTER TABLE users ALTER COLUMN latitude DROP NOT NULL"))
            conn.execute(text("ALTER TABLE users ALTER COLUMN longitude DROP NOT NULL"))
            
            conn.commit()
            print("Successfully updated 'users' table schema.")
        except Exception as e:
            print(f"Error during migration (columns might already be nullable): {e}")

if __name__ == "__main__":
    run_migration()
