# Hosting Guide for Phimed Embedded Portal

This project is now configured to use **SQLite** (`backend/phimed.db`). It is 100% self-contained and ready to host on any cloud platform with zero database setup.

---

## 🚀 Option 1: Free Cloud Hosting via Render (Recommended - 5 Minutes)

[Render.com](https://render.com) offers free hosting for web services.

1. **Push your code to GitHub / GitLab:**
   - Create a repository (e.g. `phimed-portal`) and push this project folder.
2. **Create a Web Service on Render:**
   - Sign up / Log in to [Render](https://render.com).
   - Click **New +** -> **Web Service**.
   - Connect your Git repository.
3. **Configure Settings:**
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. **Add Environment Variables:**
   Under **Environment Variables**, add:
   - `TENANT_ID`: `your-azure-tenant-id`
   - `CLIENT_ID`: `your-azure-client-id`
   - `CLIENT_SECRET`: `your-azure-client-secret`
5. **Deploy:**
   - Click **Create Web Service**.
   - Render will build and deploy your app. You'll get a live URL (e.g., `https://phimed-portal.onrender.com`) where both the frontend and backend run seamlessly together!

---

## 🚂 Option 2: Railway

1. Sign up on [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Railway automatically detects `requirements.txt` and `Procfile`.
4. Under **Variables**, add:
   - `TENANT_ID`
   - `CLIENT_ID`
   - `CLIENT_SECRET`
5. Click **Generate Domain** to get your public live URL.

---

## 🐳 Option 3: Docker (Any Server / VM / VPS)

You can run this container on any Linux/Windows VM, AWS EC2, or DigitalOcean Droplet:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t phimed-portal .
docker run -p 8000:8000 --env-file backend/.env phimed-portal
```

---

## 💻 Running Locally

You can continue to run locally at any time using:
- **`START_PHIMED.bat`**: Starts backend and frontend locally just like before.
- Or directly via uvicorn:
  ```bash
  backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload
  ```
  and visit `http://127.0.0.1:8000`.

---

## 🗄️ Database Management (SQLite)

- **Database File:** `backend/phimed.db`
- **Schema & Initial Data:** `backend/seed.sql`
- **Resetting Database:** Run `python backend/init_db.py` to recreate `phimed.db` fresh from `seed.sql`.
- **Switch back to SQL Server:** Add `DB_TYPE=mssql` to `backend/.env`.
