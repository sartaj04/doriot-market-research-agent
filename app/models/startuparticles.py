from sqlalchemy import Column, INTEGER, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import ARRAY,FLOAT
from pgvector.sqlalchemy import Vector
from sqlalchemy import Index
from core.database import Base

class StartupArticles(Base):
    __tablename__ = 'startup_articles'

    id = Column(INTEGER, primary_key=True, index=True)
    title = Column(Text)
    url = Column(Text)
    published_at = Column(TIMESTAMP)
    author = Column(Text)
    category = Column(Text)
    article_text = Column(Text)
    article_html = Column(Text)
    embedding = Column(Vector(1536), nullable=True)
    source = Column(Text)

    def __repr__(self):
        return f"<StartupArticle(id={self.id}, title={self.title})>"

    def to_dict(self, include_embedding: bool = False):
        model_dict = {
            column.name: getattr(self, column.name) 
            for column in self.__table__.columns 
            if column.name != 'embedding' or include_embedding
        }
        return model_dict

    def to_str_for_embedding(self):
        return f"Title: {self.title}\nContent: {self.article_text}"

# Define HNSW index for vector similarity search
index_embedding = Index(
    f"hnsw_index_for_cosine_techcrunch_startup_articles_embedding",
    StartupArticles.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)