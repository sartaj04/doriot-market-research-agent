from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Text, Float, 
    Boolean, Date, BIGINT, INTEGER, TIMESTAMP, JSON
)
from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION, JSONB
from sqlalchemy.orm import relationship
from core.database import Base

class Investors(Base):
    __tablename__ = 'investors'

    # Primary Key
    uuid = Column(Text, primary_key=True, index=True)

    # Basic Information
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    description = Column(Text)
    email = Column(Text)

    # Timestamps
    created_at = Column(Text)
    updated_at = Column(Text)
    founded_on = Column(Text)
    closed_on = Column(Text)

    # Location Information
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)

    # Investment Details
    roles = Column(Text)
    investor_types = Column(Text)
    investment_count = Column(DOUBLE_PRECISION)
    total_investments = Column(Integer)

    # Financial Information
    total_funding_usd = Column(DOUBLE_PRECISION)
    total_funding = Column(DOUBLE_PRECISION)
    total_funding_currency_code = Column(Text)

    # Social Media & Web Presence
    domain = Column(Text)
    facebook_url = Column(Text)
    linkedin_url = Column(Text)
    twitter_url = Column(Text)
    logo_url = Column(Text)

    # JSON Fields
    combined_co_lead_list = Column(JSONB)
    competitors_list = Column(JSONB)
    top_3_series = Column(JSONB)
    top_3_categories = Column(JSONB)
    top_3_locations = Column(JSONB)

    # Relationships
    investments = relationship(
        "Investments",
        back_populates="investor"
    )

    def __repr__(self):
        return f"<Investor(name={self.name}, type={self.type}, investments={self.investment_count})>"