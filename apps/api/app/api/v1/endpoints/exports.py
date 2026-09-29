from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.models.export import Export
from app.models.page import Page
from app.schemas.export import ExportResponse
from app.services.pdf_service import get_pdf_service
from app.services.storage_service import get_storage_service

router = APIRouter()

@router.post("/pdf", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
def create_pdf_export(
    project_id: str,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    pages = db.query(Page).filter(Page.project_id == project_id).all()
    if not pages:
        raise HTTPException(status_code=400, detail="No pages found to export.")

    pdf_service = get_pdf_service()
    try:
        pdf_key = pdf_service.export_study_pack(project, pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    storage = get_storage_service()

    # Save export record
    import uuid
    export_id = f"exp-{uuid.uuid4().hex[:10]}"
    export = Export(
        id=export_id,
        project_id=project_id,
        format="pdf",
        storage_key=pdf_key,
        status="COMPLETED"
    )
    db.add(export)
    db.commit()
    db.refresh(export)

    return ExportResponse(
        id=export.id,
        project_id=export.project_id,
        format=export.format,
        storage_key=export.storage_key,
        url=storage.get_url(export.storage_key),
        status=export.status,
        created_at=export.created_at
    )

@router.get("", response_model=List[ExportResponse])
def list_exports(
    project_id: str,
    db: Session = Depends(get_db)
):
    exports = db.query(Export).filter(Export.project_id == project_id).all()
    storage = get_storage_service()

    resp = []
    for ex in exports:
        resp.append(ExportResponse(
            id=ex.id,
            project_id=ex.project_id,
            format=ex.format,
            storage_key=ex.storage_key,
            url=storage.get_url(ex.storage_key) if ex.storage_key else None,
            status=ex.status,
            created_at=ex.created_at
        ))
    return resp
