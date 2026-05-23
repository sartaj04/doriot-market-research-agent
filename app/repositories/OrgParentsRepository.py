from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func, text

from models.orgparents import OrgParents
from .BaseRepository import BaseRepository


class OrgParentsRepository(BaseRepository[OrgParents]):
    def __init__(self):
        super().__init__(OrgParents)

    def get_parent_companies(
        self,
        db: Session,
        company_uuid: str
    ) -> List[OrgParents]:
        """Get parent companies of a company"""
        return db.query(self.model)\
            .filter(self.model.uuid == company_uuid)\
            .order_by(desc(self.model.rank))\
            .all()
    


    def get_company_relationships_by_name(
        self,
        db: Session,
        company_name: str,
        *,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get both parent and subsidiary relationships by company name"""
        # Find company by name
        company = db.query(self.model)\
            .filter(self.model.name.ilike(f"%{company_name}%"))\
            .first()
            
        if not company:
            return {"parent_companies": [], "subsidiaries": []}
            
        # Get parents
        parents = db.query(self.model)\
            .filter(self.model.uuid == company.uuid)\
            .order_by(desc(self.model.rank))\
            .limit(limit)\
            .all()
        
        # Get subsidiaries
        subsidiaries = db.query(self.model)\
            .filter(self.model.parent_uuid == company.uuid)\
            .order_by(desc(self.model.rank))\
            .limit(limit)\
            .all()
            
        return {
            "parent_companies": [
                {
                    "name": p.parent_name,
                    "relationship_type": p.relationship_type or "Parent",
                    "rank": p.rank
                } for p in parents
            ],
            "subsidiaries": [
                {
                    "name": s.name,
                    "relationship_type": s.relationship_type or "Subsidiary",
                    "rank": s.rank
                } for s in subsidiaries
            ]
        }

    def get_full_org_structure_by_name(
        self,
        db: Session,
        company_name: str
    ) -> Dict[str, Any]:
        """Get complete organizational structure by company name"""
        # Find company by name
        root_company = db.query(self.model)\
            .filter(self.model.name.ilike(f"%{company_name}%"))\
            .first()
            
        if not root_company:
            return {}
            
        def get_children(parent_uuid: str, processed: set) -> List[Dict[str, Any]]:
            if parent_uuid in processed:  # Avoid cycles
                return []
                
            processed.add(parent_uuid)
            children = self.get_subsidiaries(db, parent_uuid)
            
            return [
                {
                    "name": child.name,
                    "relationship_type": child.relationship_type or "Subsidiary",
                    "children": get_children(child.uuid, processed)
                }
                for child in children
            ]

        processed = set()
        return {
            "name": root_company.name,
            "children": get_children(root_company.uuid, processed)
        }

    def get_subsidiaries(
        self,
        db: Session,
        parent_uuid: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrgParents]:
        """Get subsidiaries of a parent company"""
        return db.query(self.model)\
            .filter(self.model.parent_uuid == parent_uuid)\
            .order_by(desc(self.model.rank))\
            .offset(skip).limit(limit).all()

    def get_company_relationships(
        self,
        db: Session,
        company_uuid: str
    ) -> Dict[str, List[str]]:
        """Get both parent and subsidiary relationships"""
        # Get parents
        parents = db.query(self.model)\
            .filter(self.model.uuid == company_uuid)\
            .all()
        
        # Get subsidiaries
        subsidiaries = db.query(self.model)\
            .filter(self.model.parent_uuid == company_uuid)\
            .all()
            
        return {
            "parent_companies": [
                {
                    "uuid": p.parent_uuid,
                    "name": p.parent_name,
                    "rank": p.rank
                } for p in parents
            ],
            "subsidiaries": [
                {
                    "uuid": s.uuid,
                    "name": s.name,
                    "rank": s.rank
                } for s in subsidiaries
            ]
        }

    def get_full_org_structure(
        self,
        db: Session,
        root_company_uuid: str
    ) -> Dict[str, Any]:
        """Get complete organizational structure"""
        def get_children(parent_uuid: str, processed: set) -> List[Dict[str, Any]]:
            if parent_uuid in processed:  # Avoid cycles
                return []
                
            processed.add(parent_uuid)
            children = self.get_subsidiaries(db, parent_uuid)
            
            return [
                {
                    "uuid": child.uuid,
                    "name": child.name,
                    "children": get_children(child.uuid, processed)
                }
                for child in children
            ]

        # Start with root company
        root_company = db.query(self.model)\
            .filter(self.model.uuid == root_company_uuid)\
            .first()
            
        if not root_company:
            return {}
            
        processed = set()
        return {
            "uuid": root_company.uuid,
            "name": root_company.name,
            "children": get_children(root_company_uuid, processed)
        }