from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.database import get_db
from app.models import Department, Location
from app.models.enums import UserRole
from app.schemas.common import DepartmentBase, DepartmentOut, LocationBase, LocationOut

router = APIRouter(tags=["references"])


@router.get("/api/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    return db.query(Department).all()


@router.post("/api/departments", response_model=DepartmentOut)
def create_department(payload: DepartmentBase, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    dep = Department(**payload.model_dump())
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.patch("/api/departments/{dep_id}", response_model=DepartmentOut)
def patch_department(dep_id: int, payload: DepartmentBase, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    dep = db.query(Department).filter(Department.id == dep_id).first()
    if not dep:
        raise HTTPException(404, "Цех не найден")
    for k, v in payload.model_dump().items():
        setattr(dep, k, v)
    db.commit()
    return dep


@router.get("/api/locations", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    return db.query(Location).all()


@router.post("/api/locations", response_model=LocationOut)
def create_location(payload: LocationBase, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    loc = Location(**payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.patch("/api/locations/{loc_id}", response_model=LocationOut)
def patch_location(loc_id: int, payload: LocationBase, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    loc = db.query(Location).filter(Location.id == loc_id).first()
    if not loc:
        raise HTTPException(404, "Локация не найдена")
    for k, v in payload.model_dump().items():
        setattr(loc, k, v)
    db.commit()
    return loc
