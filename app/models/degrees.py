from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class Degrees(Base):
    __tablename__ = 'degrees'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    type = Column(Text)
    permalink = Column(DOUBLE_PRECISION)
    cb_url = Column(DOUBLE_PRECISION)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    person_uuid = Column(Text)
    person_name = Column(Text)
    institution_uuid = Column(Text)
    institution_name = Column(Text)
    degree_type = Column(Text)
    subject = Column(Text)
    started_on = Column(Text)
    completed_on = Column(Text)
    is_completed = Column(Boolean)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
