# models.py
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="client")
    favorite_books = relationship("Book", secondary="favorite_books")

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genres = relationship("Genre", secondary="book_genre")
    authors = relationship("Author", secondary="book_author")

# association tables
book_genre = Table('book_genre', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('genre_id', Integer, ForeignKey('genres.id'))
)

book_author = Table('book_author', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('author_id', Integer, ForeignKey('authors.id'))
)

class FavoriteBooks(Base):
    __tablename__ = "favorite_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))