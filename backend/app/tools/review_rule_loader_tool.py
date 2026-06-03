from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.review_rule import ReviewRule


def load_rules(db: Session, tenant_id: int, integration_id: Optional[int] = None) -> List[ReviewRule]:
    query = db.query(ReviewRule).filter(ReviewRule.tenant_id == tenant_id, ReviewRule.is_enabled == True)
    if integration_id:
        query = query.filter(
            (ReviewRule.integration_id == integration_id) | (ReviewRule.integration_id == None)
        )
    return query.all()


def format_rules_for_prompt(rules: List[ReviewRule]) -> str:
    if not rules:
        return "No specific rules configured. Apply general best practices for security, quality, architecture, performance, and maintainability."
    lines = []
    for r in rules:
        lines.append(f"- [{r.severity.upper()}] {r.title} ({r.category}): {r.description or 'No description.'}")
    return "\n".join(lines)
