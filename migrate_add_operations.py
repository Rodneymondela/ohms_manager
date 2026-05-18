r"""
Migration: Add multi-operation (tenant) support.

Safe to run multiple times - each step is wrapped in try/except and skips
if the change already exists. All existing data is preserved and assigned
to a default "Default Operation".

Run with:
    python migrate_add_operations.py
"""

from app import create_app, db
from sqlalchemy import text, inspect

app = create_app()

def col_exists(conn, table, column):
    """Check whether a column already exists in a table."""
    try:
        result = conn.execute(text(f'SELECT {column} FROM "{table}" LIMIT 1'))
        result.close()
        return True
    except Exception:
        return False


def add_column(conn, table, column, col_type, default=None):
    """Add a column to a table if it does not already exist."""
    if col_exists(conn, table, column):
        print(f"  SKIP  {table}.{column} already exists")
        return
    try:
        ddl = f'ALTER TABLE "{table}" ADD COLUMN {column} {col_type}'
        if default is not None:
            ddl += f' DEFAULT {default}'
        conn.execute(text(ddl))
        conn.commit()
        print(f"  OK    added {table}.{column}")
    except Exception as e:
        conn.rollback()
        print(f"  WARN  {table}.{column}: {e}")


with app.app_context():
    with db.engine.connect() as conn:

        # ── 1. Create operation table ─────────────────────────────────────────
        print("\n[1] Creating 'operation' table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS operation (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_name VARCHAR(120) NOT NULL,
                    code           VARCHAR(20)  NOT NULL UNIQUE,
                    location       VARCHAR(120),
                    status         VARCHAR(20)  NOT NULL DEFAULT 'active',
                    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
                    updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("  OK    operation table ready")
        except Exception as e:
            # PostgreSQL syntax
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS operation (
                        id             SERIAL PRIMARY KEY,
                        operation_name VARCHAR(120) NOT NULL,
                        code           VARCHAR(20)  NOT NULL UNIQUE,
                        location       VARCHAR(120),
                        status         VARCHAR(20)  NOT NULL DEFAULT 'active',
                        created_at     TIMESTAMP    DEFAULT NOW(),
                        updated_at     TIMESTAMP    DEFAULT NOW()
                    )
                """))
                conn.commit()
                print("  OK    operation table ready (postgres)")
            except Exception as e2:
                conn.rollback()
                print(f"  WARN  operation table: {e2}")

        # ── 2. Seed the default operation ─────────────────────────────────────
        print("\n[2] Seeding default operation...")
        try:
            result = conn.execute(text("SELECT id FROM operation WHERE code = 'DEFAULT'"))
            row = result.fetchone()
            if row:
                default_op_id = row[0]
                print(f"  SKIP  default operation already exists (id={default_op_id})")
            else:
                conn.execute(text("""
                    INSERT INTO operation (operation_name, code, location, status)
                    VALUES ('Default Operation', 'DEFAULT', 'Default Site', 'active')
                """))
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
            '"user"',
            'employee',
            'stressor',
            'heg',
            'sampling_schedule',
            'exposure_reading',
            'medical_record',
            'field_sheet',
        ]

        for tbl in tables:
            tbl_bare = tbl.strip('"')
            if col_exists(conn, tbl_bare, 'operation_id'):
                print(f"  SKIP  {tbl_bare}.operation_id already exists")
                continue
            try:
                conn.execute(text(
                    f'ALTER TABLE {tbl} ADD COLUMN operation_id INTEGER REFERENCES operation(id)'
                ))
                conn.commit()
                print(f"  OK    added {tbl_bare}.operation_id")
            except Exception as e:
                conn.rollback()
                print(f"  WARN  {tbl_bare}.operation_id: {e}")

        # ── 4. Assign all existing records to the default operation ───────────
        print(f"\n[4] Assigning existing records to operation id={default_op_id}...")

        for tbl in tables:
            try:
                conn.execute(text(
                    f'UPDATE {tbl} SET operation_id = {default_op_id} WHERE operation_id IS NULL'
                ))
                conn.commit()
                result = conn.execute(text(f'SELECT COUNT(*) FROM {tbl}'))
                count = result.fetchone()[0]
                print(f"  OK    {tbl.strip(chr(34))}: {count} row(s) assigned")
            except Exception as e:
                conn.rollback()
                print(f"  WARN  {tbl.strip(chr(34))}: {e}")

        # ── 5. Promote existing admin users to super_admin if no operation ────
        print("\n[5] Handling super_admin role for existing admin users...")
        try:
            # Check if there are any super_admin users already
            result = conn.execute(text("SELECT COUNT(*) FROM \"user\" WHERE role = 'super_admin'"))
            super_count = result.fetchone()[0]
            if super_count == 0:
                # Promote the first admin user to super_admin
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
        print("  The first admin user has been promoted to super_admin.")
        print("  All other records belong to the default operation.")
