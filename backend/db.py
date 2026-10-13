# backend/db.py
# Auto-creates tables, migrates columns, creates default admin.
# Safe to run on every restart — fully idempotent.

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()


def _col_exists(conn, table, col):
    r = conn.execute(
        text("SELECT COUNT(*) FROM information_schema.columns "
             "WHERE table_name=:t AND column_name=:c AND table_schema=DATABASE()"),
        {"t": table, "c": col}
    )
    return r.scalar() > 0


def _table_exists(conn, table):
    r = conn.execute(
        text("SELECT COUNT(*) FROM information_schema.tables "
             "WHERE table_name=:t AND table_schema=DATABASE()"),
        {"t": table}
    )
    return r.scalar() > 0


def _add_col(conn, table, col, definition):
    if not _col_exists(conn, table, col):
        conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{col}` {definition}"))
        print(f"  ✅ Added    {table}.{col}")
    else:
        print(f"  ✔  Exists   {table}.{col}")


def _widen_col(conn, table, col, new_len=500):
    """Widen an existing VARCHAR column to new_len if it's currently smaller."""
    r = conn.execute(
        text("SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.columns "
             "WHERE table_name=:t AND column_name=:c AND table_schema=DATABASE()"),
        {"t": table, "c": col}
    )
    row = r.fetchone()
    if row and row[0] and row[0] < new_len:
        conn.execute(text(f"ALTER TABLE `{table}` MODIFY COLUMN `{col}` VARCHAR({new_len}) NULL"))
        print(f"  📐 Widened  {table}.{col}  ({row[0]}→{new_len})")


def _add_fk(conn, table, col, ref_table, ref_col, on_delete="SET NULL"):
    if not _col_exists(conn, table, col):
        return
    r = conn.execute(
        text("SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE "
             "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:t AND COLUMN_NAME=:c "
             "AND REFERENCED_TABLE_NAME IS NOT NULL"),
        {"t": table, "c": col}
    )
    if r.scalar() == 0:
        fk = f"fk_{table}_{col}"
        conn.execute(text(
            f"ALTER TABLE `{table}` ADD CONSTRAINT `{fk}` "
            f"FOREIGN KEY (`{col}`) REFERENCES `{ref_table}`(`{ref_col}`) ON DELETE {on_delete}"
        ))
        print(f"  ✅ FK added {table}.{col} → {ref_table}.{ref_col}")


def _run_migrations(conn):
    """All ALTER TABLE migrations — idempotent, safe to call multiple times."""
    if conn.dialect.name != "mysql":
        return

    # ── team_members ──────────────────────────────────────────────
    if _table_exists(conn, "team_members"):
        _add_col(conn, "team_members", "is_former", "TINYINT(1) NOT NULL DEFAULT 0")
        _add_col(conn, "team_members", "cloudinary_public_id", "VARCHAR(500) NULL")
        _widen_col(conn, "team_members", "image_file")

    # ── projects ─────────────────────────────────────────────────
    if _table_exists(conn, "projects"):
        _add_col(conn, "projects", "status", "VARCHAR(20) NOT NULL DEFAULT 'ongoing'")
        _add_col(conn, "projects", "lead_id", "INT NULL DEFAULT NULL")
        _add_fk(conn, "projects", "lead_id", "team_members", "id", "SET NULL")
        _add_col(conn, "projects", "cloudinary_public_id", "VARCHAR(500) NULL")
        _widen_col(conn, "projects", "image_file")

    # ── project_members join table ────────────────────────────────
    if not _table_exists(conn, "project_members"):
        conn.execute(text("""
            CREATE TABLE `project_members` (
                `project_id` INT NOT NULL,
                `member_id`  INT NOT NULL,
                PRIMARY KEY (`project_id`, `member_id`),
                CONSTRAINT `fk_pm_project`
                    FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE CASCADE,
                CONSTRAINT `fk_pm_member`
                    FOREIGN KEY (`member_id`) REFERENCES `team_members`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        print("  ✅ Created table project_members")

    # ── gallery_images ────────────────────────────────────────────
    if _table_exists(conn, "gallery_images"):
        _add_col(conn, "gallery_images", "cloudinary_public_id", "VARCHAR(500) NULL")
        _widen_col(conn, "gallery_images", "image_file")

    # ── events ───────────────────────────────────────────────────
    if _table_exists(conn, "events"):
        _add_col(conn, "events", "cloudinary_public_id", "VARCHAR(500) NULL")
        _widen_col(conn, "events", "brochure_file")

    # ── cert_templates ────────────────────────────────────────────
    if _table_exists(conn, "cert_templates"):
        _add_col(conn, "cert_templates", "cloudinary_public_id", "VARCHAR(500) NULL")
        _widen_col(conn, "cert_templates", "ppt_template_file")

    # ── candidates ────────────────────────────────────────────────
    if _table_exists(conn, "candidates"):
        _add_col(conn, "candidates", "cloudinary_public_id", "VARCHAR(500) NULL")
        _widen_col(conn, "candidates", "resume_file")


def init_db(app):
    with app.app_context():
        print("\n🔧 InnoSphere DB init…")

        # 1. Apply column migrations FIRST (for existing tables)
        # Then create_all handles brand new tables
        try:
            with db.engine.begin() as conn:
                _run_migrations(conn)
        except Exception as e:
            print(f"  ⚠️  Pre-migration error: {e}")

        # 2. Create any tables that don't exist yet
        try:
            db.create_all()
            print("  ✅ db.create_all() OK")
        except Exception as e:
            print(f"  ⚠️  db.create_all(): {e}")

        # 3. Run migrations again for any tables just created (idempotent)
        try:
            with db.engine.begin() as conn:
                _run_migrations(conn)
        except Exception as e:
            print(f"  ⚠️  Post-migration error: {e}")

        # 4. Default admin
        try:
            from backend.auth import create_admin_if_not_exists
            create_admin_if_not_exists()
        except Exception as e:
            print(f"  ⚠️  Admin check: {e}")

        print("🟢 DB init complete.\n")
