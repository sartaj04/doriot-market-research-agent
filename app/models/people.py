from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class People(Base):
    __tablename__ = 'people'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(BIGINT)
    created_at = Column(Text)
    updated_at = Column(Text)
    first_name = Column(Text)
    last_name = Column(Text)
    gender = Column(Text)
    country_code = Column(Text)
    state_code = Column(Text)
    region = Column(Text)
    city = Column(Text)
    featured_job_organization_uuid = Column(Text)
    featured_job_organization_name = Column(Text)
    featured_job_title = Column(Text)
    facebook_url = Column(Text)
    linkedin_url = Column(Text)
    twitter_url = Column(Text)
    logo_url = Column(Text)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
