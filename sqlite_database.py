from database import Base, engine
import models


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database and tables created")


if __name__ == "__main__":
    create_tables()
