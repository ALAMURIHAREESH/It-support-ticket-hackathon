from database.db import engine

columns = {
    "similarity": "FLOAT",
    "issue_status": "VARCHAR(100)",
    "explanation": "TEXT"
}

with engine.begin() as connection:
    existing = {
        row[1] for row in
        connection.exec_driver_sql("PRAGMA table_info(tickets)")
    }

    for column, data_type in columns.items():
        if column not in existing:
            connection.exec_driver_sql(
                f"ALTER TABLE tickets ADD COLUMN {column} {data_type}"
            )
            print("Added:", column)
        else:
            print("Already exists:", column)

print("Database migration completed.")