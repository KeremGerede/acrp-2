from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.functional_test import FunctionalTestConfig
from app.schemas.functional_test import FunctionalTestConfigCreate, FunctionalTestConfigUpdate, FunctionalTestConfigResponse

router = APIRouter(prefix="/api/functional-test-configs", tags=["functional-test-configs"])


@router.get("", response_model=List[FunctionalTestConfigResponse])
def list_configs(tenant_id: Optional[int] = None, integration_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(FunctionalTestConfig)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(FunctionalTestConfig.id.desc()).all()


@router.post("", response_model=FunctionalTestConfigResponse, status_code=201)
def create_config(data: FunctionalTestConfigCreate, db: Session = Depends(get_db)):
    config = FunctionalTestConfig(**data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.patch("/{config_id}", response_model=FunctionalTestConfigResponse)
def update_config(config_id: int, data: FunctionalTestConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(FunctionalTestConfig).filter_by(id=config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(config, k, v)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=204)
def delete_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(FunctionalTestConfig).filter_by(id=config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    db.delete(config)
    db.commit()


@router.patch("/{config_id}/toggle", response_model=FunctionalTestConfigResponse)
def toggle_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(FunctionalTestConfig).filter_by(id=config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    config.is_enabled = not config.is_enabled
    db.commit()
    db.refresh(config)
    return config
