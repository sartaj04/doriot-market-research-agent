from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class Funds(Base):
    __tablename__ = 'funds'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    entity_uuid = Column(Text)
    entity_name = Column(Text)
    entity_type = Column(Text)
    announced_on = Column(Text)
    raised_amount_usd = Column(DOUBLE_PRECISION)
    raised_amount = Column(DOUBLE_PRECISION)
    raised_amount_currency_code = Column(Text)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
