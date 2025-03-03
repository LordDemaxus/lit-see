from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from pydantic import BaseModel
from pydantic import BaseModel, HttpUrl
from database import *
import analyzer, searcher
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.post("/upload_pg_book/")
async def upload_book_from_pg(search_term: str, db: Session = Depends(get_db)):
    book_path = searcher.search_book(search_term)
    if book_path:
        contents = searcher.extract_book_from_epub(book_path)
        new_book = Book(title=contents['title'], author=contents['author'], text=contents['text'])
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        os.remove(book_path)
        return {f"message: {contents['title']} by {contents['author']} has been uploaded"}
    else:
        raise HTTPException(status_code=404, detail="Book can't be found")

@app.post("/upload_book/")
async def upload_book(file: UploadFile=File(...), db: Session = Depends(get_db)):
    if file.content_type == 'application/epub+zip':
        contents = searcher.extract_book_from_epub(f"../../Downloads/{file.filename}")
        new_book = Book(title=contents['title'], author=contents['author'], text=contents['text'])
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return {f"message: {contents['title']} by {contents['author']} has been uploaded"}
    else:
        raise HTTPException(status_code=404, detail="Wrong file type sent")
    
@app.get("/books")
def get_all_books(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    return [{"title": book.title, "author": book.author} for book in books]

@app.get("/books/{book_id}")
def get_book(book_id: str, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book:
        return {"title": db_book.title, "author": db_book.author}
    else:
        raise HTTPException(status_code=404, detail="Book not found")
