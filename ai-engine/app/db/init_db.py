from app.db.database import engine
from app.db.models import Base


def init_database():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    print("Creating CureVerseAI database tables...")
    init_database()
    print("Database tables created successfully.")
