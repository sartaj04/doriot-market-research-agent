from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.events import Events
from .BaseRepository import BaseRepository

class EventRepository(BaseRepository[Events]):
    def __init__(self):
        super().__init__(Events)
    
    def get_upcoming_events(
        self,
        db: Session,
        country_code: Optional[str] = None,
        limit: int = 100
    ) -> List[Events]:
        query = db.query(self.model).filter(self.model.ended_on >= func.now())
        
        if country_code:
            query = query.filter(self.model.country_code == country_code)
            
        return query.order_by(self.model.started_on).limit(limit).all()