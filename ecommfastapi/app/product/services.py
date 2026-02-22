from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.product.models import Product, Category
from app.product.schemas import CategoryCreate, CategoryOut
from typing import List
from fastapi import HTTPException, status

async def create_category(session: AsyncSession, category: CategoryCreate) -> CategoryOut:
    category = Category(name=category.name)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category

async def get_all_category(session: AsyncSession) -> List[CategoryOut]:
    stmt = select(Category)
    result = await session.execute(stmt)
    return result.scalars().all()

async def delete_category(session: AsyncSession, category_id: int):
    category = await session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await session.delete(category)
    await session.commit()
    return True