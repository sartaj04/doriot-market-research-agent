from typing import TypeVar, Generic, List, Optional, Any, Dict, Union
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """
    Base repository with common database operations
    """
    def __init__(self, model: ModelType):
        self.model = model

    def get_by_id(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by_uuid(self, db: Session, uuid: str) -> Optional[ModelType]:
        """Get a record by UUID"""
        return db.query(self.model).filter(self.model.uuid == uuid).first()

    def get_all(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """Get all records with pagination and ordering"""
        query = db.query(self.model)
        
        if order_by:
            order_column = getattr(self.model, order_by)
            query = query.order_by(desc(order_column) if order_desc else asc(order_column))
            
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, data: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        data: Dict[str, Any]
    ) -> ModelType:
        """Update a record"""
        for field, value in data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: Any) -> Optional[ModelType]:
        """Delete a record"""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def count(self, db: Session) -> int:
        """Get total count of records"""
        return db.query(func.count(self.model.id)).scalar()

    def exists(self, db: Session, id: Any) -> bool:
        """Check if record exists"""
        return db.query(
            db.query(self.model).filter(self.model.id == id).exists()
        ).scalar()

    def filter_by(
        self,
        db: Session,
        filters: List[Dict[str, Any]],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """
        Generic filter method
        filters format: [
            {"field": "name", "op": "eq", "value": "example"},
            {"field": "age", "op": "gt", "value": 18},
        ]
        """
        query = db.query(self.model)
        
        for filter_item in filters:
            field = getattr(self.model, filter_item["field"])
            op = filter_item["op"].lower()
            value = filter_item["value"]
            
            if op == "eq":
                query = query.filter(field == value)
            elif op == "ne":
                query = query.filter(field != value)
            elif op == "gt":
                query = query.filter(field > value)
            elif op == "lt":
                query = query.filter(field < value)
            elif op == "ge":
                query = query.filter(field >= value)
            elif op == "le":
                query = query.filter(field <= value)
            elif op == "like":
                query = query.filter(field.like(f"%{value}%"))
            elif op == "ilike":
                query = query.filter(field.ilike(f"%{value}%"))
            elif op == "in":
                query = query.filter(field.in_(value))
            elif op == "notin":
                query = query.filter(~field.in_(value))
            elif op == "between":
                query = query.filter(field.between(value[0], value[1]))
            elif op == "isnull":
                query = query.filter(field.is_(None) if value else field.isnot(None))

        if order_by:
            order_column = getattr(self.model, order_by)
            query = query.order_by(desc(order_column) if order_desc else asc(order_column))

        return query.offset(skip).limit(limit).all()

    def search(
        self,
        db: Session,
        search_term: str,
        search_fields: List[str],
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """
        Search across multiple fields
        """
        conditions = []
        for field in search_fields:
            conditions.append(
                getattr(self.model, field).ilike(f"%{search_term}%")
            )
            
        query = db.query(self.model).filter(or_(*conditions))
        
        if order_by:
            order_column = getattr(self.model, order_by)
            query = query.order_by(desc(order_column) if order_desc else asc(order_column))
            
        return query.offset(skip).limit(limit).all()

    def get_recent(
        self,
        db: Session,
        days: int = 30,
        date_field: str = "created_at",
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get recent records"""
        date_column = getattr(self.model, date_field)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.query(self.model)\
            .filter(date_column >= cutoff_date)\
            .order_by(desc(date_column))\
            .offset(skip)\
            .limit(limit)\
            .all()

    def bulk_create(self, db: Session, items: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records"""
        db_objs = [self.model(**item) for item in items]
        db.add_all(db_objs)
        db.commit()
        for obj in db_objs:
            db.refresh(obj)
        return db_objs

    def bulk_update(
        self,
        db: Session,
        ids: List[Any],
        data: Dict[str, Any]
    ) -> List[ModelType]:
        """Update multiple records"""
        objs = db.query(self.model).filter(self.model.id.in_(ids)).all()
        for obj in objs:
            for field, value in data.items():
                setattr(obj, field, value)
        db.commit()
        return objs