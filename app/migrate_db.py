
import sqlite3

from app.database import DATABASE_URL


def migrate_db() -> None:
    # Extract the SQLite database path from the connection URL.
    database_path = DATABASE_URL.replace("sqlite:///", "")

    connection = sqlite3.connect(database_path)

    try:
        columns = connection.execute("PRAGMA table_info(jobs)").fetchall()
        existing_columns = {column[1] for column in columns}

        if not existing_columns:
            print("The jobs table does not exist yet. Run the app first.")
            return

        if "application_status" not in existing_columns:
            connection.execute(
                "ALTER TABLE jobs ADD COLUMN application_status "
                "VARCHAR(50) NOT NULL DEFAULT 'saved'"
            )
            print("Added application_status column.")

        if "application_notes" not in existing_columns:
            connection.execute(
                "ALTER TABLE jobs ADD COLUMN application_notes "
                "TEXT NOT NULL DEFAULT ''"
            )
            print("Added application_notes column.")

        connection.commit()
        print("Database migration completed successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_db()
