from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class Ipos(Base):
    __tablename__ = 'ipos'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(DOUBLE_PRECISION)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    org_uuid = Column(Text)
    org_name = Column(Text)
    org_cb_url = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    stock_exchange_symbol = Column(Text)
    stock_symbol = Column(Text)
    went_public_on = Column(Text)
    share_price_usd = Column(DOUBLE_PRECISION)
    share_price = Column(DOUBLE_PRECISION)
    share_price_currency_code = Column(Text)
    valuation_price_usd = Column(DOUBLE_PRECISION)
    valuation_price = Column(DOUBLE_PRECISION)
    valuation_price_currency_code = Column(Text)
    money_raised_usd = Column(DOUBLE_PRECISION)
    money_raised = Column(DOUBLE_PRECISION)
    money_raised_currency_code = Column(Text)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
