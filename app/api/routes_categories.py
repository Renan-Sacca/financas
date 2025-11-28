from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.database import get_session
from app.schemas import CategoryCreate, CategoryResponse
from app import crud
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/categories", tags=["categories"])

@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(category: CategoryCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return crud.create_category(session, category, current_user.id)

@router.get("/", response_model=List[CategoryResponse])
def list_categories(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return crud.get_categories(session, current_user.id)

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    updated_category = crud.update_category(session, category_id, category, current_user.id)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category

@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if not crud.delete_category(session, category_id, current_user.id):
        raise HTTPException(status_code=404, detail="Category not found")
    return None