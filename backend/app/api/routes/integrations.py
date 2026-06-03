import json
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.integration import ProjectIntegration
from app.schemas.integration import IntegrationCreate, IntegrationUpdate, IntegrationResponse
from app.core.config import settings

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


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
        "webhook_url": f"{{BASE_URL}}/api/webhooks/{i.provider}/{i.id}",
        "webhook_secret": i.webhook_secret,
        "instructions": [
            f"1. Go to your {i.provider.title()} repository settings > Webhooks.",
            "2. Add a new webhook.",
            f"3. Payload URL: {{your-public-url}}/api/webhooks/{i.provider}/{i.id}",
            "4. Content type: application/json",
            f"5. Secret: {i.webhook_secret}",
            "6. Events: Select 'Pull requests' and 'Pushes'.",
            "7. Save the webhook.",
        ],
    }


@router.post("/{integration_id}/sync")
def sync_integration(integration_id: int, db: Session = Depends(get_db)):
    i = db.query(ProjectIntegration).filter_by(id=integration_id).first()
    if not i:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"status": "ok", "message": "Sync triggered (stub — full sync not yet implemented for MVP)"}
