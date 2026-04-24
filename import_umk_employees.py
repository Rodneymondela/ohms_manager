"""
Import UMK employees from CSV directly into the SQLite database.
Usage: python import_umk_employees.py
"""
import csv
import sqlite3
import os

CSV_PATH = r"C:\Users\rodne\OneDrive\Documents\UMK\UMK Employee Lists_31 December 2025 (002).csv"
DB_PATH  = os.path.join(os.path.dirname(__file__), 'instance', 'ohms.db')


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: database not found at {DB_PATH}")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Read existing names to avoid duplicates
    cur.execute("SELECT LOWER(name) FROM employee WHERE is_active = 1")
    existing = {row[0] for row in cur.fetchall()}
    print(f"Existing active employees: {len(existing)}")

    rows_to_insert = []
    skipped = 0

    with open(CSV_PATH, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            name      = (row.get('Name')       or '').strip()
            job_title = (row.get('Job Title')  or '').strip()
            dept      = (row.get('Department') or '').strip()
            heg       = (row.get('HEG')        or '').strip() or None

            if not name or not job_title:
                skipped += 1
                continue

            if name.lower() in existing:
                skipped += 1
                continue

            rows_to_insert.append((name, job_title, dept or 'Unknown', heg, 1))
            existing.add(name.lower())  # prevent intra-file dupes

    print(f"Rows to import: {len(rows_to_insert)}  |  Skipped (blank/duplicate): {skipped}")

    if not rows_to_insert:
        print("Nothing to import.")
        return

    cur.executemany(
        "INSERT INTO employee (name, job_title, department, heg_number, is_active) VALUES (?, ?, ?, ?, ?)",
        rows_to_insert,
    )
    con.commit()
    con.close()

    print(f"Done — {len(rows_to_insert)} employees imported successfully.")


if __name__ == '__main__':
    main()
