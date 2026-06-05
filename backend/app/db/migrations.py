import logging
from sqlalchemy import text
from app.db.database import engine

logger = logging.getLogger(__name__)

# (table, column, ALTER TABLE statement)
_MIGRATIONS = [
    ("findings", "rule_id",
     "ALTER TABLE findings ADD COLUMN rule_id INTEGER REFERENCES review_rules(id)"),
    ("merge_review_runs", "repository_full_name",
     "ALTER TABLE merge_review_runs ADD COLUMN repository_full_name VARCHAR(500)"),
    ("merge_review_runs", "raw_agent_response_json",
     "ALTER TABLE merge_review_runs ADD COLUMN raw_agent_response_json TEXT"),
    ("merge_review_runs", "started_at",
     "ALTER TABLE merge_review_runs ADD COLUMN started_at DATETIME"),
    ("merge_review_runs", "gate_status",
     "ALTER TABLE merge_review_runs ADD COLUMN gate_status VARCHAR(50) DEFAULT 'pending'"),
    ("merge_review_runs", "gate_reason",
     "ALTER TABLE merge_review_runs ADD COLUMN gate_reason TEXT"),
    ("merge_review_runs", "revert_status",
     "ALTER TABLE merge_review_runs ADD COLUMN revert_status VARCHAR(50) DEFAULT 'not_required'"),
    ("merge_review_runs", "revert_pr_url",
     "ALTER TABLE merge_review_runs ADD COLUMN revert_pr_url VARCHAR(1000)"),
    ("merge_review_runs", "revert_branch_name",
     "ALTER TABLE merge_review_runs ADD COLUMN revert_branch_name VARCHAR(500)"),
    ("merge_review_runs", "revert_error_message",
     "ALTER TABLE merge_review_runs ADD COLUMN revert_error_message TEXT"),
    ("merge_review_runs", "reverted_at",
     "ALTER TABLE merge_review_runs ADD COLUMN reverted_at DATETIME"),
]


def run_migrations() -> None:
    with engine.connect() as conn:
        for table, column, sql in _MIGRATIONS:
            try:
                rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                existing = {row[1] for row in rows}
                if column not in existing:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"DB migration applied: {table}.{column}")
                else:
                    logger.debug(f"DB migration skipped (exists): {table}.{column}")
            except Exception as exc:
                logger.warning(f"DB migration error ({table}.{column}): {exc}")
