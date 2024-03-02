# change_user_role.py
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal, engine
import sys

def display_user_details(user):
    print(f"User ID: {user.id}, Email: {user.email}, Old Role: {user.role}")

def change_user_role(session: Session, user_id: int, new_role: str):
    user = session.query(User).filter(User.id == user_id).first()
    
    if not user:
        print(f"User with ID {user_id} not found.")
        return

    print("User details before the role change:")
    display_user_details(user)

    old_role = user.role
    user.role = new_role
    session.commit()

    # Fetch the user again to get the updated information
    updated_user = session.query(User).filter(User.id == user_id).first()

    print("User role updated successfully.")
    print("User details after the role change:")
    display_user_details(updated_user)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python change_user_role.py <user_id> <new_role>")
        sys.exit(1)

    user_id = int(sys.argv[1])
    new_role = sys.argv[2]

    db_session = SessionLocal()

    try:
        change_user_role(db_session, user_id, new_role)
    finally:
        db_session.close()