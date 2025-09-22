from app.database import SessionLocal, engine, Base
from app import models, crud, schemas
import getpass

def create_tables_and_admin():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    username = input("Enter superadmin username: ")
    email = input("Enter superadmin email: ")
    password = getpass.getpass("Enter superadmin password: ")  # Input hidden

    admin = db.query(models.User).filter(models.User.email == email).first()
    if not admin:
        admin_in = schemas.UserCreate(username=username, email=email, password=password)
        crud.create_user(db, admin_in, role="superadmin")
        print(f"Created superadmin {email} / [hidden]")
    else:
        print("Admin already exists")
    db.close()

if __name__ == "__main__":
    create_tables_and_admin()
