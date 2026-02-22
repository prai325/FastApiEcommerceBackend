from fastapi import APIRouter, Depends, HTTPException, status
from app.account.dep import require_admin
from app.account.models import User
from app.db.config import SessionDep
from app.product.schemas import CategoryCreate, CategoryOut
from app.product.services import create_category, get_all_category, delete_category
from app.account.utils import success_response
from typing import List
from pydantic import TypeAdapter


router = APIRouter()

@router.post("/category", response_model=CategoryOut)
async def category_create(session: SessionDep, category: CategoryCreate, admin_user: User = Depends(require_admin)):
    new_category = await create_category(session, category)
    category_out = CategoryOut.model_validate(new_category)
    return success_response(
        message="Category created successfully",
        data=category_out.model_dump(),
        status_code=201
    )

@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(session: SessionDep):
    categories = await get_all_category(session)
    # category_out = CategoryOut.model_validate(categories)
    adapter = TypeAdapter(List[CategoryOut])
    validated_data = adapter.validate_python(categories)
    return success_response(
        message="Successfully get all category",
        # data=category_out.model_dump(),
        data=[item.model_dump() for item in validated_data],
        status_code=200
    )

@router.delete("/delete-category/{category_id}")
async def category_delete(session: SessionDep, category_id: int, admin_user: User = Depends(require_admin)):
    await delete_category(session, category_id)
    return success_response(
        message="Category deleted successfully",
        data=None,
        status_code=200
    )