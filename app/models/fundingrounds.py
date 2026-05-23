from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class FundingRounds(Base):
    __tablename__ = 'funding_rounds'
    uuid = Column(Integer, primary_key=True, index=True)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    investment_type = Column(Text)
    announced_on = Column(Text)
    raised_amount_usd = Column(DOUBLE_PRECISION)
    raised_amount = Column(DOUBLE_PRECISION)
    raised_amount_currency_code = Column(Text)
    post_money_valuation_usd = Column(DOUBLE_PRECISION)
    post_money_valuation = Column(DOUBLE_PRECISION)
    post_money_valuation_currency_code = Column(Text)
    investor_count = Column(DOUBLE_PRECISION)
    org_uuid = Column(Text, ForeignKey('companies.uuid'))
    org_name = Column(Text)
    lead_investor_uuids = Column(Text)



    # Relationships
    company = relationship(
        "Companies",
        back_populates="funding_rounds",
        foreign_keys=[org_uuid]
    )
    
    investments = relationship(
        "Investments",
        primaryjoin="FundingRounds.uuid==Investments.funding_round_uuid",
        back_populates="funding_round"
    )

    # Model methods
    @property
    def investment_summary(self):
        """Return funding round summary"""
        return {
            "type": self.investment_type,
            "amount": f"${self.raised_amount_usd:,.2f}" if self.raised_amount_usd else "Undisclosed",
            "date": self.announced_on,
            "investors": len(self.investments) if self.investments else 0
        }
