from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi_pagination import Page, add_pagination, paginate
from fastapi. security import OAuth2PasswordBearer , OAuth2PasswordRequestForm
from pydantic  import BaseModel
from typing import List, Optional
from uuid import uuid4

app = FastAPI()

#in-memory data storage

users_db = {}     # Fixed typo: was `users_ab`
tokens_db = {}    # Fixed typo: was `token_db`
books_db = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl= "login")

# models 
class UserCreate(BaseModel):
    username: str
    password: str 

class Book(BaseModel):
    title: str
    author: str
    description: str

class BookOut(Book):
    id: str

#helper functions  

def authenticate_user (username: str, password: str):
    user = users_db.get(username)
    if user and user ['password'] == password:
        return True
    return False

def get_current_user(token: str = Depends(oauth2_scheme)):
    username = tokens_db.get(token)
    if not username:
        raise HTTPException(status_code = 401, detail="Invalid token")
    return username

#Routes

@app.post("/singup")
def singup(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400,detail="Username already registered")
    users_db[user.username] = {"password": user.password}
    return {"message": "User created successfully"}

@app.post("/login")
def login(from_data:OAuth2PasswordBearer = Depends()):
    if authenticate_user(from_data.username,from_data.password):
        token = str(uuid4())
        tokens_db[token] = from_data.username
        return{"access_token": token,"token_type": "bearer"}
    raise HTTPException(status_code=401,detail="Invalid credentials")

@app.post("/books",response_model=BookOut)
def add_book(book: Book, username: str = Depends(get_current_user)):
    book_id = str(uuid4())
    books_db[book_id] = book.dict()
    return {**book.dict(),"id": book_id}

@app.get("/books", response_model = List[BookOut])
def get_all_books(username: str = Depends(get_current_user),search: Optional[str] = Query(None, alias="id"),
    sort: Optional[str] = Query(None)):
    filtered_books = [
        {"id": id_, **book}
        for id_, book in books_db.items()
        if (not search or search.lower() in book["title"].lower())
    ]

    if sort:
        reverse = sort.startswith("-")
        sort_field = sort.lstrip("-")
        if sort_field in Book.__fields__:
            filtered_books.sort(
                key=lambda x: x.get(sort_field), reverse=reverse
            )
    return paginate(filtered_books)
    #return [{"id": id_, **book} for id_, book in books_db.items()]

@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: str, username: str = Depends(get_current_user)):
    book = books_db.get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return{"id": book_id, **book} 

@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: str, book: Book, username: str = Depends(get_current_user)):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    books_db[book_id] = book.dict()
    return {"id": book_id,**book.dict()}

@app.delete("/books/{book_id} ")
def delete_book(book_id: str, username: str = Depends(get_current_user)):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    del books_db[book_id] 
    return {"message": "Book deleted"} 

add_pagination(app)

# python -m uvicorn prectice_project2:app --reload 