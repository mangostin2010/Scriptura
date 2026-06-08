# view_db.py - read-only inspector for scriptura.db
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'scriptura.db')

# Columns whose values should be masked when printed.
SENSITIVE_COLUMNS = {'password_hash'}


def mask(column, value):
    if column in SENSITIVE_COLUMNS and value:
        return '***hidden***'
    return value


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run the app once to create it.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row['name'] for row in cur.fetchall()]

    if not tables:
        print("No tables found in the database.")
        conn.close()
        return

    print(f"Database: {DB_PATH}")
    print(f"Tables: {', '.join(tables)}\n")

    for table in tables:
        cur.execute(f'SELECT COUNT(*) AS n FROM "{table}"')
        count = cur.fetchone()['n']
        print("=" * 70)
        print(f"TABLE: {table}  ({count} row{'' if count == 1 else 's'})")
        print("=" * 70)

        cur.execute(f'SELECT * FROM "{table}"')
        rows = cur.fetchall()
        if not rows:
            print("  (empty)\n")
            continue

        columns = rows[0].keys()
        for i, row in enumerate(rows, 1):
            print(f"  Row {i}:")
            for col in columns:
                value = mask(col, row[col])
                print(f"    {col}: {value}")
            print()

    conn.close()


if __name__ == '__main__':
    main()
