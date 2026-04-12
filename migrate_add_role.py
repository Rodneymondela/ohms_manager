"""Add role column to user table without dropping data."""
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE \"user\" ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'admin'"
            ))
            conn.commit()
            print("role column added")
        except Exception as e:
            conn.rollback()
            print(f"Skipped (may already exist): {e}")

        # Sync is_admin flag from role
        conn.execute(text(
            "UPDATE \"user\" SET is_admin = (role = 'admin')"
        ))
        conn.commit()
        print("is_admin synced from role")
