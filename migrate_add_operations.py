r"""
Migration: Add multi-operation (tenant) support.

Safe to run multiple times - each step is wrapped in try/except and skips
if the change already exists. All existing data is preserved and assigned
to a default "Default Operation".

Run with:
    python migrate_add_operations.py
"""

from app import create_app, db
from sqlalchemy import text

app = create_app()


def col_exists(conn, table, column):
    """Check whether a column exists using information_schema (safe for Postgres & SQLite)."""
    try:
        # information_schema works in both PostgreSQL and SQLite 3.37+
        result = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            f"WHERE table_name = '{table}' AND column_name = '{column}'"
        ))
        return result.fetchone() is not None
    except Exception:
        conn.rollback()
        # Fallback: try a direct SELECT (SQLite older versions)
        try:
            r = conn.execute(text(f'SELECT "{column}" FROM "{table}" LIMIT 0'))
            r.close()
            return True
        except Exception:
            conn.rollback()
            return False


def table_exists(conn, table):
    """Check whether a table exists."""
    try:
        result = conn.execute(text(
            f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table}'"
        ))
        if result.fetchone():
            return True
        return False
    except Exception:
        conn.rollback()
        # SQLite fallback
        try:
            r = conn.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            ))
            return r.fetchone() is not None
        except Exception:
            conn.rollback()
            return False


with app.app_context():
    with db.engine.connect() as conn:

        # ── 1. Create operation table ─────────────────────────────────────────
        print("\n[1] Creating 'operation' table...")
        if table_exists(conn, 'operation'):
            print("  SKIP  operation table already exists")
        else:
            # Try PostgreSQL SERIAL syntax first, then SQLite AUTOINCREMENT
            for ddl in [
                """CREATE TABLE IF NOT EXISTS operation (
                    id             SERIAL PRIMARY KEY,
                    operation_name VARCHAR(120) NOT NULL,
                    code           VARCHAR(20)  NOT NULL UNIQUE,
                    location       VARCHAR(120),
                    status         VARCHAR(20)  NOT NULL DEFAULT 'active',
                    created_at     TIMESTAMP    DEFAULT NOW(),
                    updated_at     TIMESTAMP    DEFAULT NOW()
                )""",
                """CREATE TABLE IF NOT EXISTS operation (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_name VARCHAR(120) NOT NULL,
                    code           VARCHAR(20)  NOT NULL UNIQUE,
                    location       VARCHAR(120),
                    status         VARCHAR(20)  NOT NULL DEFAULT 'active',
                    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
                    updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP
                )""",
            ]:
                try:
                    conn.execute(text(ddl))
                    conn.commit()
                    print("  OK    operation table created")
                    break
                except Exception as e:
                    conn.rollback()
                    if 'already exists' in str(e).lower():
                        print("  SKIP  operation table already exists")
                        break
            else:
                print("  WARN  could not create operation table — may already exist via db.create_all()")

        # ── 2. Seed the default operation ─────────────────────────────────────
        print("\n[2] Seeding default operation...")
        default_op_id = None
        try:
            result = conn.execute(text("SELECT id FROM operation WHERE code = 'DEFAULT'"))
            row = result.fetchone()
            if row:
                default_op_id = row[0]
                print(f"  SKIP  default operation already exists (id={default_op_id})")
            else:
                conn.execute(text(
                    "INSERT INTO operation (operation_name, code, location, status) "
                    "VALUES ('Default Operation', 'DEFAULT', 'Default Site', 'active')"
                ))
                conn.commit()
                result = conn.execute(text("SELECT id FROM operation WHERE code = 'DEFAULT'"))
                default_op_id = result.fetchone()[0]
                print(f"  OK    default operation created (id={default_op_id})")
        except Exception as e:
            conn.rollback()
            default_op_id = 1
            print(f"  WARN  could not seed default operation: {e}")

        # ── 3. Add operation_id to all relevant tables ────────────────────────
        print("\n[3] Adding operation_id columns...")

        tables = [
            'user',
            'employee',
            'stressor',
            'heg',
            'sampling_schedule',
            'exposure_reading',
            'medical_record',
            'field_sheet',
        ]

        for tbl in tables:
            if col_exists(conn, tbl, 'operation_id'):
                print(f"  SKIP  {tbl}.operation_id already exists")
                continue
            try:
                conn.execute(text(
                    f'ALTER TABLE "{tbl}" ADD COLUMN operation_id INTEGER REFERENCES operation(id)'
                ))
                conn.commit()
                print(f"  OK    added {tbl}.operation_id")
            except Exception as e:
                conn.rollback()
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print(f"  SKIP  {tbl}.operation_id (already exists)")
                else:
                    print(f"  WARN  {tbl}.operation_id: {e}")

        # ── 4. Assign all existing records to the default operation ───────────
        print(f"\n[4] Assigning existing records to operation id={default_op_id}...")

        for tbl in tables:
            try:
                result = conn.execute(text(
                    f'UPDATE "{tbl}" SET operation_id = {default_op_id} WHERE operation_id IS NULL'
                ))
                conn.commit()
                updated = result.rowcount
                print(f"  OK    {tbl}: {updated} row(s) assigned")
            except Exception as e:
                conn.rollback()
                print(f"  WARN  {tbl}: {e}")

        # ── 5. Promote first admin to super_admin ─────────────────────────────
        print("\n[5] Handling super_admin role for existing admin users...")
        try:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM \"user\" WHERE role = 'super_admin'"
            ))
            super_count = result.fetchone()[0]
            if super_count == 0:
                result = conn.execute(text(
                    "SELECT id, username FROM \"user\" WHERE role = 'admin' ORDER BY id LIMIT 1"
                ))
                admin = result.fetchone()
                if admin:
                    conn.execute(text(
                        f"UPDATE \"user\" SET role = 'super_admin', operation_id = NULL WHERE id = {admin[0]}"
                    ))
                    conn.commit()
                    print(f"  OK    promoted user '{admin[1]}' (id={admin[0]}) to super_admin")
                else:
                    print("  SKIP  no admin user found to promote")
            else:
                print(f"  SKIP  {super_count} super_admin user(s) already exist")
        except Exception as e:
            conn.rollback()
            print(f"  WARN  super_admin promotion: {e}")

        print("\nMigration complete. All existing data preserved.")
        print(f"  Default operation id = {default_op_id}")
