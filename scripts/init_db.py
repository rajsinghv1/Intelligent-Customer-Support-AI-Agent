
from app.database.db import init_database


def main():
    init_database()
    print("SQLite database initialized successfully.")
    print("Tables: conversations, messages")


if __name__ == "__main__":
    main()
