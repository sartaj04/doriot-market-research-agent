from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class Companies(Base):

    __tablename__ = 'companies'

    uuid = Column(Integer, primary_key=True, index=True)
    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    legal_name = Column(Text)
    roles = Column(Text)
    domain = Column(Text)
    homepage_url = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    address = Column(Text)
    postal_code = Column(Text)
    status = Column(Text)
    short_description = Column(Text)
    category_list = Column(Text)
    category_groups_list = Column(Text)
    num_funding_rounds = Column(DOUBLE_PRECISION)
    total_funding_usd = Column(DOUBLE_PRECISION)
    total_funding = Column(DOUBLE_PRECISION)
    total_funding_currency_code = Column(Text)
    founded_on = Column(Text)
    last_funding_on = Column(Text)
    closed_on = Column(Text)
    employee_count = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    facebook_url = Column(Text)
    linkedin_url = Column(Text)
    twitter_url = Column(Text)
    logo_url = Column(Text)
    alias1 = Column(Text)
    alias2 = Column(Text)
    alias3 = Column(Text)
    primary_role = Column(Text)
    num_exits = Column(DOUBLE_PRECISION)



    # Relationships
    descriptions = relationship(
        "OrganizationDescriptions",
        back_populates="company",
        primaryjoin="Companies.uuid==OrganizationDescriptions.uuid"
    )
    funding_rounds = relationship(
        "FundingRounds",
        primaryjoin="Companies.uuid==FundingRounds.org_uuid",
        back_populates="company"
    )
    acquisitions_as_acquirer = relationship(
        "Acquisitions",
        primaryjoin="Companies.uuid==Acquisitions.acquirer_uuid",
        back_populates="acquirer",
        foreign_keys="Acquisitions.acquirer_uuid"
    )
    
    acquisitions_as_acquired = relationship(
        "Acquisitions",
        primaryjoin="Companies.uuid==Acquisitions.acquiree_uuid",
        back_populates="acquiree",
        foreign_keys="Acquisitions.acquiree_uuid"
    )

    # Model methods
    @property
    def total_funding_formatted(self):
        """Return formatted total funding in USD"""
        if self.total_funding_usd:
            return f"${self.total_funding_usd:,.2f}"
        return "No funding data"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "name": self.name,
            "description": self.short_description,
            "total_funding": self.total_funding_formatted,
            "category": self.category_list,
            "founded_on": self.founded_on,
            "location": f"{self.city}, {self.country_code}" if self.city else self.country_code
        }
