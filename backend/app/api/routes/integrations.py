import json
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.integration import ProjectIntegration
from app.schemas.integration import IntegrationCreate, IntegrationUpdate, IntegrationResponse
from app.providers.github_adapter import normalize_repository_full_name

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _derive_fields(payload: dict) -> dict:
    """
    Normalize repository_full_name to 'owner/repo' form, then auto-derive
    repository_owner, repository_name, and repository_url from it when they
    are not explicitly provided. Accepts full GitHub URLs and .git suffixes.
    """
    full_name = payload.get("repository_full_name") or ""
    if full_name:
        full_name = normalize_repository_full_name(full_name)
        payload["repository_full_name"] = full_name

    if full_name and "/" in full_name:
        owner, name = full_name.split("/", 1)
        if not payload.get("repository_owner"):
            payload["repository_owner"] = owner
        if not payload.get("repository_name"):
            payload["repository_name"] = name

    provider = payload.get("provider", "github")
    if full_name and not payload.get("repository_url"):
        if provider == "github":
            payload["repository_url"] = f"https://github.com/{full_name}"
        elif provider == "gitlab":
            payload["repository_url"] = f"https://gitlab.com/{full_name}"

    return payload


@router.get("", response_model=List[IntegrationResponse])
def list_integrations(tenant_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(ProjectIntegration)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    return q.order_by(ProjectIntegration.id.desc()).all()


@router.post("", response_model=IntegrationResponse, status_code=201)
def create_integration(data: IntegrationCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    recipients = payload.pop("notification_recipients", [])
    if not payload.get("webhook_secret"):
        payload["webhook_secret"] = secrets.token_hex(24)
    payload = _derive_fields(payload)
    integration = ProjectIntegration(**payload, notification_recipients=json.dumps(recipients or []))
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.get("/{integration_id}", response_model=IntegrationResponse)
def get_integration(integration_id: int, db: Session = Depends(get_db)):
    i = db.query(ProjectIntegration).filter_by(id=integration_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Integration not found")
    return i


@router.patch("/{integration_id}", response_model=IntegrationResponse)
def update_integration(integration_id: int, data: IntegrationUpdate, db: Session = Depends(get_db)):
    i = db.query(ProjectIntegration).filter_by(id=integration_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Integration not found")
    payload = data.model_dump(exclude_none=True)
    if "notification_recipients" in payload:
        payload["notification_recipients"] = json.dumps(payload["notification_recipients"])
    payload = _derive_fields(payload)
    for k, v in payload.items():
        setattr(i, k, v)
    db.commit()
    db.refresh(i)
    return i


@router.delete("/{integration_id}", status_code=204)
def delete_integration(integration_id: int, db: Session = Depends(get_db)):
    i = db.query(ProjectIntegration).filter_by(id=integration_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Integration not found")
    db.delete(i)
    db.commit()


@router.get("/{integration_id}/webhook-info")
def webhook_info(integration_id: int, db: Session = Depends(get_db)):
    i = db.query(ProjectIntegration).filter_by(id=integration_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {
        "webhook_url": f"{{your-ngrok-url}}/api/webhooks/{i.provider}/{i.id}",
        "webhook_secret": i.webhook_secret,
        "integration_id": i.id,
        "provider": i.provider,
        "instructions": [
            "1. Go to your GitHub repo → Settings → Webhooks → Add webhook.",
            f"2. Payload URL: https://YOUR-NGROK.ngrok.io/api/webhooks/{i.provider}/{i.id}",
            "3. Content type: application/json",
            f"4. Secret: {i.webhook_secret}",
            "5. Events: select 'Let me select individual events', then check BOTH:",
            "   - Pull requests  ← REQUIRED for automatic revert (provides PR node_id)",
            "   - Pushes         ← used as fallback if Pull request event is missing",
            "6. Save the webhook.",
            "",
            "NOTE: Automatic revert works best when the 'Pull requests' event is enabled.",
            "Without it, RevertAgent cannot resolve the merged pull request and will",
            "set revert_status=required instead of automatically reverting the merge.",
            "",
            "GitHub token required permissions (fine-grained PAT or classic token):",
            "  Contents: Read and Write",
            "  Pull Requests: Read and Write",
            "  Metadata: Read",
        ],
        "revert_note": (
            "Automatic revert requires the 'Pull requests' GitHub webhook event. "
            "Without it, revert_status will be set to 'required' and manual action is needed."
        ),
    }


@router.post("/{integration_id}/sync")
def sync_integration(integration_id: int, db: Session = Depends(get_db)):
    i = db.query(ProjectIntegration).filter_by(id=integration_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"status": "ok", "message": "Sync triggered (stub — not yet implemented)"}
