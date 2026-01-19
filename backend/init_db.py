# init_db.py - Script to initialize the database
# Run this script once to create the database and tables

from backend.database import engine, Base
from backend.models import User, ChartData

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("\nMake sure PostgreSQL is running and the database 'lifepath_db' exists.")
    print("You can create it using: CREATE DATABASE lifepath_db;")


