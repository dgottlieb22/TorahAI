from sqlalchemy import Column, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector


from app.config import settings


class Base(DeclarativeBase):
    pass


class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    ref = Column(Text, unique=True, nullable=False)
    book = Column(Text)
    category = Column(Text)
    text_he = Column(Text)
    text_en = Column(Text)
    embedding_text = Column(Text)
    embedding_text_hash = Column(Text)
    embedding_status = Column(Text, default="pending")
    embedding_error = Column(Text)
    last_embedded_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class SourceEmbedding(Base):
    __tablename__ = "source_embeddings"

    chunk_id = Column(UUID(as_uuid=True), ForeignKey("source_chunks.id"), primary_key=True)
    embedding_model = Column(Text, primary_key=True)
    embedding = Column(Vector(settings.embedding_dim))
    embedding_text_hash = Column(Text)

    __table_args__ = (
        Index("ix_source_embeddings_embedding", embedding, postgresql_using="ivfflat", postgresql_with={"lists": 100}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    )
