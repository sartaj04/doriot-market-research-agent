from typing import List
from sqlalchemy.orm import Session
from models.investmentpartners import InvestmentPartners
from .BaseRepository import BaseRepository

class InvestmentPartnerRepository(BaseRepository[InvestmentPartners]):
    def __init__(self):
        super().__init__(InvestmentPartners)
    
    def get_partners_by_investor(
        self,
        db: Session,
        investor_uuid: str
    ) -> List[InvestmentPartners]:
        return db.query(self.model).filter(
            self.model.investor_uuid == investor_uuid
        ).all()
    
    def get_partners_by_investor_name(
        self,
        db: Session,
        investor_name: str
    ) -> List[InvestmentPartners]:
        return db.query(self.model).filter(
            self.model.investor_name.ilike(f"%{investor_name}%")
        ).all()

    def get_partners_by_name(
        self,
        db: Session,
        partner_name: str
    ) -> List[InvestmentPartners]:
        return db.query(self.model).filter(
            self.model.name.ilike(f"%{partner_name}%")
        ).all()

    def get_recent_partners(
        self,
        db: Session,
        limit: int = 10
    ) -> List[InvestmentPartners]:
        return db.query(self.model)\
            .order_by(self.model.created_at.desc())\
            .limit(limit)\
            .all()
        