from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text

from models.categorygroups import CategoryGroups
from models.orgparents import OrgParents
from .BaseRepository import BaseRepository

class CategoryGroupRepository(BaseRepository[CategoryGroups]):
    def __init__(self):
        super().__init__(CategoryGroups)

    def get_company_categories(
        self,
        db: Session,
        company_uuid: str
    ) -> List[CategoryGroups]:
        """Get categories for a company"""
        return db.query(self.model)\
            .filter(self.model.category_groups_list.ilike(f"%{company_uuid}%"))\
            .order_by(desc(self.model.rank))\
            .all()

    def search_categories(
        self,
        db: Session,
        category_name: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[CategoryGroups]:
        """Search categories by name"""
        return db.query(self.model)\
            .filter(self.model.name.ilike(f"%{category_name}%"))\
            .order_by(desc(self.model.rank))\
            .offset(skip).limit(limit).all()

    def get_by_type(
        self,
        db: Session,
        category_type: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[CategoryGroups]:
        """Get categories by type"""
        return db.query(self.model)\
            .filter(self.model.type == category_type)\
            .order_by(desc(self.model.rank))\
            .offset(skip).limit(limit).all()

    def get_category_companies(
        self,
        db: Session,
        category_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[str]:
        """Get company UUIDs in a category"""
        category = self.get_by_uuid(db, category_uuid)
        if not category or not category.category_groups_list:
            return []
            
        # Parse the category_groups_list which contains company UUIDs
        company_uuids = category.category_groups_list.split(',')
        return company_uuids[skip:skip + limit]

