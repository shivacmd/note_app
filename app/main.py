import os
from fastapi import FastAPI, Depends, Form, Request, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional

from app import models, crud, schemas, auth
from app.database import engine, SessionLocal, Base

from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = FastAPI()

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created!")

# Email configuration
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Create tables
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    try:
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        return user
    except ValueError:
        return None


@app.get("/", include_in_schema=False)
def root(request: Request):
    return RedirectResponse("/dashboard")

# Signup
@app.get("/signup")
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), email: str = Form(...), 
                 password: str = Form(...), db: Session = Depends(get_db)):
    
    if len(username) < 3:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "Username must be at least 3 characters long",
                "username": username,
                "email": email
            }
        )
    
    if len(password) < 8:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "Password must be at least 8 characters long",
                "username": username,
                "email": email
            }
        )
    
    if crud.get_user_by_email(db, email):
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "Email already registered",
                "username": username,
                "email": email
            }
        )
    
    # Create user
    user_in = schemas.UserCreate(username=username, email=email, password=password)
    crud.create_user(db, user_in)
    return RedirectResponse("/login?msg=Account+created+successfully!+Please+login", status_code=302)

# Login
@app.get("/login")
def login_form(request: Request, msg: Optional[str] = None):
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    resp = RedirectResponse("/dashboard", status_code=302)
    resp.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return resp

# Logout
@app.get("/logout")
def logout():
    resp = RedirectResponse("/login?msg=Logged out", status_code=302)
    resp.delete_cookie("user_id")
    return resp

# Dashboard 
@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?msg=Please+login")
    
    # Show dashboard template with user info
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

# My Notes page
@app.get("/notes/my")
def my_notes(request: Request, search: Optional[str] = Query(None), page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?msg=Please+login")
    
    limit = 10
    offset = (page - 1) * limit
    total, notes = crud.get_notes_by_user(db, user.id, search=search, offset=offset, limit=limit)
    total_pages = (total + limit - 1) // limit if total else 1
    
    return templates.TemplateResponse("my_notes.html", {
        "request": request, 
        "user": user, 
        "notes": notes, 
        "search": search, 
        "page": page, 
        "total_pages": total_pages
    })

# All Notes page - for superadmin only 
@app.get("/notes/all")
def all_notes(request: Request, search: Optional[str] = Query(None), page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "superadmin":
        return RedirectResponse("/dashboard?msg=Access+denied")
    
    limit = 10
    offset = (page - 1) * limit
    total, notes = crud.get_all_notes(db, search=search, offset=offset, limit=limit)
    total_pages = (total + limit - 1) // limit if total else 1
    
    return templates.TemplateResponse("all_notes.html", {
        "request": request, 
        "user": user, 
        "notes": notes, 
        "search": search, 
        "page": page, 
        "total_pages": total_pages
    })

# Create note
@app.get("/note/create")
def create_note_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?msg=Please+login")
    
    if user.role == "superadmin":
        raise HTTPException(403, "Superadmin cannot create notes")
    
    return templates.TemplateResponse("create_note.html", {"request": request, "user": user})

@app.post("/note/create")
def create_note(request: Request, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?msg=Please+login")
    
    if user.role == "superadmin":
        raise HTTPException(403, "Superadmin cannot create notes")
    
    note_in = schemas.NoteCreate(title=title, content=content)
    crud.create_note(db, note_in, user.id)
    return RedirectResponse("/notes/my?msg=Note+created", status_code=302)

@app.get("/note/{note_id}/edit")
def edit_note_form(note_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?msg=Please+login")
    
    if user.role == "superadmin":
        raise HTTPException(403, "Superadmin cannot edit notes")
    
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    
    if note.owner_id != user.id:
        raise HTTPException(403, "Not allowed")
    
    return templates.TemplateResponse("edit_note.html", {"request": request, "note": note})

@app.post("/note/{note_id}/edit")
def edit_note(note_id: int, request: Request, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?msg=Please+login")
    
    if user.role == "superadmin":
        raise HTTPException(403, "Superadmin cannot edit notes")
    
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    
    if note.owner_id != user.id:
        raise HTTPException(403, "Not allowed")
    
    updated = crud.update_note(db, note_id, schemas.NoteUpdate(title=title, content=content))
    return RedirectResponse("/notes/my?msg=Note+updated", status_code=302)

# Delete note
@app.get("/note/{note_id}/delete")
def delete_note(note_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?msg=Please+login")
    
    if user.role == "superadmin":
        raise HTTPException(403, "Superadmin cannot delete notes")
    
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    
    if note.owner_id != user.id:
        raise HTTPException(403, "Not allowed")
    
    crud.delete_note(db, note_id)
    return RedirectResponse("/notes/my?msg=Note+deleted", status_code=302)

# Note detail
@app.get("/note/{note_id}")
def note_detail(note_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    
    if user and user.role == "user" and note.owner_id != user.id:
        raise HTTPException(403, "Not allowed")
    
    can_modify = user and user.role == "user" and note.owner_id == user.id
    
    return templates.TemplateResponse("note_detail.html", {
        "request": request, 
        "note": note, 
        "user": user,
        "can_modify": can_modify
    })

# Email sending function
def send_reset_email(email: str, token: str, request: Request):
    """Send password reset email to user"""
    try:
        # Create reset URL
        app_url = os.getenv("APP_URL", f"{request.url.scheme}://{request.url.hostname}")
        # reset_url = f"{request.url.scheme}://{request.url.hostname}/reset-password/{token}"
        reset_url = f"{app_url}/reset-password/{token}"
        
        # Email content
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "🔐 Password Reset - Notes App"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">📝 Notes App</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <h2 style="color: #333; margin-top: 0;">Reset Your Password</h2>
                <p>Hi there,</p>
                <p>You've requested a password reset. Click the button below to create a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">Reset Password</a>
                </div>
                <p><em>This link will expire in 1 hour.</em></p>
                <p>If you didn't request this, you can safely ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 14px;">
                    Best regards,<br>
                    <strong>The Notes App Team</strong>
                </p>
            </div>
        </div>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        
        print(f"✅ Reset email sent to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

@app.get("/forgot-password")
def forgot_password_form(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password")
async def forgot_password(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    # Check if user exists 
    user = crud.get_user_by_email(db, email)
    
    if not user:
        return templates.TemplateResponse(
            "forgot_password.html",
            {"request": request, "message": "If this email exists, check your inbox for reset instructions."}
        )
    
    # Create reset token
    token = crud.create_password_reset_token(db, email)
    if not token:
        return templates.TemplateResponse(
            "forgot_password.html",
            {"request": request, "error": "Failed to generate reset token. Please try again."}
        )
    
    # Send email
    success = send_reset_email(email, token.token, request)
    if success:
        return templates.TemplateResponse(
            "forgot_password.html",
            {"request": request, "message": "Password reset email sent! Check your inbox (including spam folder)."}
        )
    else:
        return templates.TemplateResponse(
            "forgot_password.html",
            {"request": request, "error": "Failed to send email. Please try again later."}
        )

# Password Reset Routes
@app.get("/reset-password/{token}")
def reset_password_form(token: str, request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@app.post("/reset-password/{token}")
async def reset_password(request: Request, token: str, password: str = Form(...), 
                        confirm_password: str = Form(...), db: Session = Depends(get_db)):
    
    # Check if passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Passwords do not match!"}
        )
    
    # Validate token
    user = crud.validate_reset_token(db, token)
    if not user:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Invalid or expired reset token!"}
        )
    
    # Reset password
    success = crud.reset_user_password(db, user.id, password)
    if success:
        return RedirectResponse("/login?msg=Password+reset+successfully!+Please+login+with+your+new+password")
    else:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Failed to reset password. Please try again."}
        )