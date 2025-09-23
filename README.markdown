# Notes App

A modern, secure web application for creating and managing notes, built with FastAPI and MySQL. Users can sign up, log in, create/edit/delete their own notes, and reset passwords via email. Admins with the `superadmin` role can view all notes, while regular users manage their personal notes. The app is deployed on Render with a Railway MySQL database for reliable performance and scalability.

## ✨ Features
- **Role-Based Access**:
  - **Users** (`role="user"`): Create, edit, delete, and view personal notes at `/notes/my`.
  - **Admins** (`role="superadmin"`): View all notes at `/notes/all` (read-only).
- **Secure Authentication**:
  - Signup, login, and logout with bcrypt-encrypted passwords.
  - Password reset via email using Gmail SMTP.
- **Efficient Note Management**:
  - Pagination, search, and filtering for notes.
  - Input validation for usernames, emails, and passwords (8+ chars, mixed case, numbers, special chars).
- **Deployment**:
  - Hosted on Render for the app, with MySQL on Railway for data persistence.
- **Responsive UI**:
  - Jinja2 templates with clean HTML/CSS/JS for a user-friendly experience.

## 🛠 Tech Stack
- **Backend**: FastAPI (Python 3.8+)
- **Database**: MySQL (Railway)
- **ORM**: SQLAlchemy
- **Authentication**: bcrypt
- **Frontend**: Jinja2 templates
- **Deployment**: Render (app), Railway (database)
- **Email**: Gmail SMTP for password reset

## 📋 Prerequisites
- Python 3.8+
- MySQL 8.0+ (local development)
- Git
- Render and Railway accounts
- Gmail account with an App Password

## 🚀 Local Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/notes-app.git
   cd notes-app
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Ensure `requirements.txt` includes:
   ```
   fastapi==0.103.2
   sqlalchemy==2.0.21
   pymysql==1.1.0
   bcrypt==4.0.1
   python-dotenv==1.0.0
   jinja2==3.1.2
   python-multipart==0.0.6
   ```

3. **Configure Environment Variables**:
   Create a `.env` file:
   ```env
   DATABASE_URL=mysql+pymysql://root:your-local-password@localhost:3306/note_app
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-gmail-app-password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   APP_URL=http://localhost:8000
   ```
   - Replace placeholders with your values.
   - Generate a Gmail App Password at [Google Account Settings](https://myaccount.google.com/security).

4. **Set Up Database**:
   - Start MySQL locally and create a `note_app` database:
     ```bash
     mysql -u root -p -e "CREATE DATABASE note_app;"
     ```
   - Run the app to create tables:
     ```bash
     uvicorn main:app --reload
     ```

5. **Launch the App**:
   ```bash
   uvicorn main:app --reload
   ```
   Access at `http://localhost:8000`.

## ☁️ Deployment (Render + Railway)

1. **Set Up Railway MySQL**:
   - In Railway Dashboard, create a MySQL database (New > Database > MySQL).
   - Attach a volume for data persistence.
   - Copy the public `DATABASE_URL` from Variables (e.g., `mysql+pymysql://root:your-pass@mysql.railway.app:3306/railway`).

2. **Deploy to Render**:
   - In Render Dashboard, create a Web Service (New > Web Service).
   - Connect your GitHub repo.
   - Set environment variables (Render > Environment):
     ```env
     DATABASE_URL=mysql+pymysql://root:your-pass@mysql.railway.app:3306/railway
     EMAIL_ADDRESS=your-email@gmail.com
     EMAIL_PASSWORD=your-gmail-app-password
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     APP_URL=https://your-app.onrender.com
     ADMIN_ACCOUNTS=[{"email":"admin@example.com","password":"@Admin123","username":"admin"}]
     ```
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Deploy and access at `https://your-app.onrender.com`.

3.
   - **Manual (Render Shell)**:
     - I created seed_admin file to create the superadmin. But when i deploy the code , i am not able to run this file.
     - Since I can not run it , and also to run it in the render shell , it is asking for subscriotion
     - So i added a row in the database for super admin.

## 📖 Usage
- **Signup**: `/signup` (creates `user` role).
- **Login**: `/login`.
- **Notes**:
  - Users: Manage notes at `/notes/my`.
  - Admins: View all notes at `/notes/all`.
- **Password Reset**: `/forgot-password` (sends email link).
- **Logout**: `/logout`.

## 🛠 Troubleshooting
- **Invalid Credentials**:
  - Ensure `users` table passwords are hashed:
    ```python
    import bcrypt
    print(bcrypt.hashpw("@Admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
    ```
  - Update in Railway > Data > `users`.
- **Database Connection**:
  - Verify `DATABASE_URL` matches Railway’s MySQL.
  - Test: `mysql -h mysql.railway.app -u root -p<your-password> -P 3306 railway`.
- **Email Issues**:
  - Confirm Gmail App Password and SMTP settings.
- **Logs**: Check Render/Railway logs for errors.

## 🔒 Security
- Change admin passwords via `/forgot-password` after creation.
- Use Railway’s internal networking (`mysql.railway.internal`) when possible.
- Never commit `.env` to Git (add to `.gitignore`).
- Remove `ADMIN_ACCOUNTS` after seeding admins.

## 🤝 Contributing
- Fork the repo, create a branch, and submit a PR.
- Add tests in `tests/` if implemented.

## 📄 License
MIT License
