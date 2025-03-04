from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/lit_analysis"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=5, max_overflow=10)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), index=True)
    author = Column(String(256), index=True)
    text = Column(Text)
    sentiment_score = Column(Float, nullable=True)
    keywords = Column(Text, nullable=True)
    characters = relationship("Character", back_populates="book")

class Character(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), index=True)
    book_id = Column(Integer, ForeignKey('books.id'), index=True)
    book = relationship("Book", back_populates="characters")
    important = Column(Boolean)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
