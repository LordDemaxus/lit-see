from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pgvector.sqlalchemy import Vector

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Monkey12!@localhost:5432/lit_analysis"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(256), unique=True, index=True)
    hashed_password = Column(Text)

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), index=True)
    author = Column(String(256), index=True)
    text = Column(Text)
    sentiment_score = Column(Float, nullable=True)
    #Add keyword finder functionality
    keywords = Column(Text, nullable=True)
    tokens = Column(Integer)
    characters = relationship("Character", back_populates="book")
    chunks = relationship("BookChunk", back_populates="book")

class Character(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), index=True)
    #char_embedding = Column(Vector(768))
    book_id = Column(Integer, ForeignKey('books.id'), index=True)
    book = relationship("Book", back_populates="characters")
    aliases = Column(Text)
    important = Column(Boolean)

class BookChunk(Base):
    __tablename__ = 'chunks'
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id'), index=True)
    book = relationship("Book", back_populates="chunks")
    chunk = Column(Text)
    embedding = Column(Vector(768))

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_similar_chunks(query_embedding, book_id):
    db = SessionLocal()
    results = db.query(
        BookChunk.chunk,
        func.cosine_distance(BookChunk.embedding, query_embedding).label('similarity')).order_by('similarity').filter(Book.id == book_id).limit(10).all()
    return results