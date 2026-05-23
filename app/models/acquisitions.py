from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class Acquisitions(Base):
    __tablename__ = 'acquisitions'
    uuid = Column(Integer, primary_key=True, index=True)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    acquiree_uuid = Column(Text, ForeignKey('companies.uuid'))
    acquiree_name = Column(Text)
    acquiree_cb_url = Column(Text)
    acquiree_country_code = Column(Text)
    acquiree_state_code = Column(Text)
    acquiree_region = Column(Text)
    acquiree_city = Column(Text)
    acquirer_uuid = Column(Text, ForeignKey('companies.uuid'))
    acquirer_name = Column(Text)
    acquirer_cb_url = Column(Text)
    acquirer_country_code = Column(Text)
    acquirer_state_code = Column(Text)
    acquirer_region = Column(Text)
    acquirer_city = Column(Text)
    acquisition_type = Column(Text)
    acquired_on = Column(Text)
    price_usd = Column(DOUBLE_PRECISION)
    price = Column(DOUBLE_PRECISION)
    price_currency_code = Column(Text)



    acquirer = relationship(
        "Companies",
        foreign_keys=[acquirer_uuid],
        back_populates="acquisitions_as_acquirer"
    )
    
    acquiree = relationship(
        "Companies",
        foreign_keys=[acquiree_uuid],
        back_populates="acquisitions_as_acquired"
    )
