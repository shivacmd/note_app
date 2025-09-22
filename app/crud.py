from sqlalchemy.orm import Session
import app.models as models
import app.schemas as schemas
import app.auth as auth

# User functions
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_in: schemas.UserCreate, role: str = "user"):
    hashed_pw = auth.hash_password(user_in.password)
    db_user = models.User(username=user_in.username, email=user_in.email, password=hashed_pw, role=role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if user and auth.verify_password(password, user.password):
        return user
    return None

# Note functions
def create_note(db: Session, note_in: schemas.NoteCreate, user_id: int):
    db_note = models.Note(**note_in.dict(), owner_id=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def get_note(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()

def update_note(db: Session, note_id: int, data: schemas.NoteUpdate):
    note = get_note(db, note_id)
    if note:
        note.title = data.title
        note.content = data.content
        db.commit()
        db.refresh(note)
    return note

def delete_note(db: Session, note_id: int):
    note = get_note(db, note_id)
    if note:
        db.delete(note)
        db.commit()
        return True
    return False

def get_notes_by_user(db: Session, user_id: int, search: str = None, offset: int = 0, limit: int = 10):
    q = db.query(models.Note).filter(models.Note.owner_id == user_id)
    if search:
        q = q.filter(models.Note.title.like(f"%{search}%"))
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return total, items



def get_all_notes(db: Session, search: str = None, offset: int = 0, limit: int = 10):
    q = db.query(models.Note)
    if search:
        q = q.filter(models.Note.title.like(f"%{search}%"))
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return total, items



import secrets
from datetime import datetime, timedelta

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)

def create_password_reset_token(db: Session, email: str):
    """Create a password reset token for the user"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    # Delete any existing tokens for this user
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id
    ).delete()
    db.commit()
    
    # Create new token
    token = models.PasswordResetToken(
        user_id=user.id,
        token=generate_reset_token(),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token

def validate_reset_token(db: Session, token: str):
    """Validate password reset token and return user if valid"""
    token_record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token,
        models.PasswordResetToken.expires_at > datetime.utcnow(),
        models.PasswordResetToken.used == 0
    ).first()
    
    if not token_record:
        return None
    
    # Mark token as used
    token_record.used = 1
    db.commit()
    
    return token_record.user

def reset_user_password(db: Session, user_id: int, new_password: str):
    """Reset user's password"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False
    
    # Delete all tokens for this user
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user_id
    ).delete()
    
    # Hash and update password
    hashed_pw = auth.hash_password(new_password)
    user.password = hashed_pw
    db.commit()
    return True
