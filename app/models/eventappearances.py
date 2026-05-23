from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class EventAppearances(Base):
    __tablename__ = 'event_appearances'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    event_uuid = Column(Text)
    event_name = Column(Text)
    participant_uuid = Column(Text)
    participant_name = Column(Text)
    participant_type = Column(Text)
    appearance_type = Column(Text)
    short_description = Column(Text)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
