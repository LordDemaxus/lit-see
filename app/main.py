from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from database import *
import analyzer, searcher, security
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.post("/upload_pg_book/")
async def upload_book_from_pg(search_term: str, db: Session = Depends(get_db), user: str = Depends(security.get_current_user)):
    """"Upload a book from Project Gutenberg if it exists.

    NOTE: For now only supports the getting the first book found from Project Gutenberg for that search term
    """
    book_path = searcher.search_book(search_term)
    if book_path:
        contents = searcher.extract_book_from_epub(book_path)
        new_book = Book(title=contents['title'], author=contents['author'], text=contents['text'], tokens=contents['tokens'])
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        os.remove(book_path)
        return {f"message: {contents['title']} by {contents['author']} has been uploaded by {user}"}
    else:
        raise HTTPException(status_code=404, detail="Book can't be found")

@app.post("/upload_book/")
async def upload_book(file: UploadFile=File(...), db: Session = Depends(get_db), user: str = Depends(security.get_current_user)):
    """"Upload a book from local files.

    NOTE: For now only supports file upload from my Downloads folder
    """
    if file.content_type == 'application/epub+zip':
        contents = searcher.extract_book_from_epub(f"../../Downloads/{file.filename}")
        new_book = Book(title=contents['title'], author=contents['author'], text=contents['text'], tokens=contents['tokens'])
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return {f"message: {contents['title']} by {contents['author']} has been uploaded by {user}"}
    else:
        raise HTTPException(status_code=404, detail="Wrong file type sent")
    
@app.get("/books")
def get_all_books(db: Session = Depends(get_db)):
    """"View info for all books in the database."""
    books = db.query(Book).all()
    return [{"title": book.title, "author": book.author, "id": book.id} for book in books]

@app.get("/books/{book_id}")
def get_book(book_id: str, db: Session = Depends(get_db)):
    """"View info for a specific book using book id.

    TODO: Would be better to access books with book name rather than book id (need to account for multiple books with same name and multiple versions of the same book)
    """
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        return {"title": db_book.title, "author": db_book.author}
    else:
        raise HTTPException(status_code=404, detail="Book not found")


@app.get("/analyze/{book_id}")
async def analyze_book(book_id: str, db: Session = Depends(get_db)):
    """Analyze book text and add analyzed info to database.

    TODO: Add genre and archetype (for all characters maked important) classification and other types of NLP text analysis
    """
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        text = db_book.text
        #Analyze Sentiment
        sentiment_score = analyzer.sentiment_analyzer(text)
        db_book.sentiment_score = sentiment_score
        db.commit()
        db.refresh(db_book)
        #Analyze characters
        extract_characters = analyzer.extract_characters(text)
        characters = [Character(name=character, book_id=book_id, important=extract_characters[character]>0.1) for character in extract_characters]
        db.bulk_save_objects(characters)
        db.commit()
        db_characters = db.query(Character).filter(Character.book_id == book_id).all()
        return {"sentiment score": db_book.sentiment_score, "characters": ["IMPORTANT: " + character.name if character.important else character.name for character in db_characters]}
    else:
        raise HTTPException(status_code=404, detail="Book not found")

@app.get("/summarize/{book_id}")
async def summarize_book(book_id: str, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        text = db_book.text
        db_chunk = db.query(BookChunk).filter(BookChunk.book_id == db_book.id).first()
        if not db_chunk:
            res = analyzer.create_chunk_embeddings(text, db_book.tokens)
            book_chunks = [BookChunk(chunk=text, embedding=embedding, book_id=db_book.id) for text, embedding in res]
            db.bulk_save_objects(book_chunks)
            db.commit()
        return {f"summary: {analyzer.summarize_book(text)}"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")

@app.post("/signup")
def sign_up(username: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_password = security.hash_password(password)
    user = User(username=username, hashed_password=hashed_password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}

@app.post("/login")
def login(username: str = str, password: str = str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = security.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
