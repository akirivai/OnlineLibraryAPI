#main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, Book, FavoriteBooks, Genre, Author
from sqlalchemy import update
from fastapi.security import OAuth2PasswordBearer
import csv
from typing import List
from models import User
from jose import JWTError, jwt
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "3AD44098746C2D9A2E106AB0737AF1FC"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Опціональна змінна, щоб зберегти інформацію про scopes
OAUTH2_SCOPES = {
    "token": "Get an authentication token",
}

# ...

# Dependency to get the current user based on the provided token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login", 
    scopes=OAUTH2_SCOPES
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

# Route for user registration
@app.post("/register")
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=email, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully"}

from fastapi import Depends, HTTPException

from fastapi.security import OAuth2PasswordRequestForm

@app.post("/login", description="Get the authentication token", response_model=dict)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # вам може знадобитися перейменувати email на username або як ви називаєте поле в формі
    user = db.query(User).filter(User.email == form_data.username, User.password == form_data.password).first()
    if user:
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/books", response_model=List[dict])
def get_books(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    books = db.query(Book).all()
    return [{"id": book.id, "title": book.title} for book in books]

# Route for adding a book to favorites
@app.post("/add_to_favorites/{book_id}")
def add_to_favorites(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        favorite = FavoriteBooks(user_id=current_user.id, book_id=book_id)
        db.add(favorite)
        db.commit()
        return {"message": "Book added to favorites successfully"}
    raise HTTPException(status_code=404, detail="Book not found")

# Route for removing a book from favorites
@app.delete("/remove_from_favorites/{book_id}")
def remove_from_favorites(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(FavoriteBooks).filter(FavoriteBooks.user_id == current_user.id, FavoriteBooks.book_id == book_id).delete()
    db.commit()
    return {"message": "Book removed from favorites successfully"}


from fastapi import HTTPException, Form


@app.post("/add_book", response_model=dict)
def add_book(
    title: str = Form(...),
    genres: List[int] = Form(...),
    authors: List[int] = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    # Перевірка ролі користувача
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You don't have permission to add books. Admin role required.")

    # Створення нової книги та додавання її до бази даних
    new_book = Book(title=title)
    for genre_id in genres:
        genre = db.query(Genre).filter(Genre.id == genre_id).first()
        if genre:
            new_book.genres.append(genre)

    for author_id in authors:
        author = db.query(Author).filter(Author.id == author_id).first()
        if author:
            new_book.authors.append(author)

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return {"message": "Book added successfully", "book_id": new_book.id}


# Route for removing a book (requires login and admin role)
@app.delete("/remove_book/{book_id}")
def remove_book(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action.")
    
    db.query(Book).filter(Book.id == book_id).delete()
    db.commit()
    return {"message": "Book removed successfully"}

# Route for exporting the list of books to CSV format (requires admin role)
@app.get("/export_books_csv")
def export_books_csv(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action.")
    
    books = db.query(Book).all()

    with open("books.csv", mode="w", newline="") as csvfile:
        fieldnames = ["id", "title"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for book in books:
            writer.writerow({"id": book.id, "title": book.title})

    return {"message": "Books exported to CSV successfully"}