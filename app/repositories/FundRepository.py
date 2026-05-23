from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.funds import Funds
from .BaseRepository import BaseRepository

class FundRepository(BaseRepository[Funds]):
    def __init__(self):
        super().__init__(Funds)
    
    def get_funds(
        self,
        db: Session,
        entity_type: Optional[str] = None,
        min_amount: Optional[float] = None,
        limit: int = 100
    ) -> List[Funds]:
        query = db.query(self.model)
        
        if entity_type:
            query = query.filter(self.model.entity_type == entity_type)
        if min_amount:
            query = query.filter(self.model.raised_amount_usd >= min_amount)
            
        return query.order_by(desc(self.model.announced_on)).limit(limit).all()