from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class Jobs(Base):
    __tablename__ = 'jobs'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    person_uuid = Column(Text)
    person_name = Column(Text)
    org_uuid = Column(Text)
    org_name = Column(Text)
    started_on = Column(Text)
    ended_on = Column(Text)
    is_current = Column(Boolean)
    title = Column(Text)
    job_type = Column(Text)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
