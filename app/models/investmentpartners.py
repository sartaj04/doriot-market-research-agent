from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class InvestmentPartners(Base):
    __tablename__ = 'investment_partners'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    funding_round_uuid = Column(Text)
    funding_round_name = Column(Text)
    investor_uuid = Column(Text)
    investor_name = Column(Text)
    partner_uuid = Column(Text)
    partner_name = Column(Text)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
