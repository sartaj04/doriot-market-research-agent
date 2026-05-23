from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, Date, BIGINT, INTEGER, TIMESTAMP, Date

from sqlalchemy.dialects.postgresql import UUID, DOUBLE_PRECISION

from sqlalchemy.orm import relationship

from core.database import Base


class CategoryGroups(Base):
    __tablename__ = 'category_groups'
    uuid = Column(Integer, primary_key=True, index=True)

    name = Column(Text)
    type = Column(Text)
    permalink = Column(Text)
    cb_url = Column(Text)
    rank = Column(DOUBLE_PRECISION)
    created_at = Column(Text)
    updated_at = Column(Text)
    category_groups_list = Column(Text)



    # Relationships
    pass  # No relationships defined

    # Model methods
    pass  # No methods defined
