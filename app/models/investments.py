from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Text, Float, 
    Boolean, Date, BIGINT, INTEGER, TIMESTAMP, TypeDecorator, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from sqlalchemy.orm import relationship
from core.database import Base
from decimal import Decimal

class MoneyType(TypeDecorator):
    """Custom type to handle PostgreSQL money values"""
    impl = String
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Remove currency symbol and other characters
        try:
            # Handle money format like '$1,234.56'
            cleaned = value.replace('$', '').replace(',', '')
            return Decimal(cleaned)
        except (ValueError, TypeError, AttributeError):
            return None

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

class Investments(Base):
    __tablename__ = 'investments'
    
    # Primary Key
    investment_uuid = Column(UUID, primary_key=True, index=True)
    
    
    # Investment Details
    funding_round_uuid = Column(Text, ForeignKey('funding_rounds.uuid')) 
    investment_round = Column(Text)
    announced_on = Column(Date)
    raised_amount = Column(MoneyType)
    investor_count = Column(Integer)
    total_funding = Column(MoneyType)
    
    
    # Investor Information
    investor_uuid = Column(Text, ForeignKey('investors.uuid'))  # Changed to reference investors table
    investor_name = Column(Text)
    investor_type = Column(Text)
    is_lead_investor = Column(Boolean)
    
    # Organization Details
    org_name = Column(Text)
    roles = Column(Text)
    country_code = Column(Text)
    region = Column(Text)
    category_list = Column(Text)
    category_groups_list = Column(Text)
    
    # Metrics
    num_funding_rounds = Column(Integer)
    total_funding_usd = Column(MoneyType)

    # Relationships
    investor = relationship(
        "Investors",
        back_populates="investments",
        foreign_keys=[investor_uuid]
    )

    funding_round = relationship(
        "FundingRounds",
        back_populates="investments",
        foreign_keys=[funding_round_uuid]
    )

    def __repr__(self):
        return f"<Investment(uuid={self.investment_uuid}, " \
               f"investor={self.investor_name}, " \
               f"round={self.investment_round})>"