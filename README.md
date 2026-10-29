# Campus Lost & Found Portal — MongoDB + Redis

A beginner-friendly NoSQL project. One FastAPI web application connects to two NoSQL databases that have different purposes:

- **MongoDB:** permanent storage for lost/found reports.
- **Redis:** temporary cache of the report list (60-second expiry) so repeat page loads can be faster.

Frontend: HTML + CSS. Backend: Python FastAPI.

## 1. Create the two databases

### MongoDB Atlas
1. Open https://www.mongodb.com/atlas/database and create a free account/cluster.
2. In **Database Access**, create a database user and password.
3. In **Network Access**, add your current IP address. For a short classroom demo only, `0.0.0.0/0` allows access from anywhere; remove it after the demo.
4. Open **Connect → Drivers → Python** and copy the connection string.
5. Replace the username, password, and cluster placeholder. If your password has special characters, URL-encode them.
6. The app creates the `campus_lost_found` database and `items` collection when the first report is saved.

### Redis Cloud
1. Open https://redis.io/try-free/ and create a free database/account.
2. Open your database's connection details and copy the Redis URL/endpoint, port, and password.
3. Build/paste the URL in this format: `rediss://default:PASSWORD@HOST:PORT` (use the exact URL shown by Redis Cloud when available).

Keep both connection URLs private. Do not share your `.env` file or upload it to GitHub.

## 2. Install Python
Install Python 3.11 or newer from https://www.python.org/downloads/ . On Windows, tick **Add Python to PATH** during installation.

## 3. Open the project
1. Extract the ZIP file.
2. Open the extracted `campus_lost_found_nosql` folder in VS Code.
3. In the VS Code terminal, create a virtual environment:

   Windows:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt terminal:
   ```bat
   .venv\Scripts\activate.bat
   ```

4. Install the dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

## 4. Configure the database connections
1. Copy `.env.example` and rename the copy to `.env`.
2. Open `.env` and paste your real MongoDB and Redis connection details.
3. Save the file. Never put real credentials in screenshots or public GitHub repositories.

## 5. Run the application
In the VS Code terminal, run:
```bash
uvicorn main:app --reload
```
Open http://127.0.0.1:8000 in your browser.

## 6. Test both databases
1. Submit a sample lost or found report. The record is saved permanently in MongoDB.
2. Reload the page. The app first checks Redis for a cached report list; if there is no cache, it reads MongoDB and stores a copy in Redis for 60 seconds.
3. Add or resolve a report. The app deletes the old Redis cache so the next page load fetches fresh data from MongoDB.
4. Open http://127.0.0.1:8000/health . It should show `"mongodb": "connected"` and `"redis": "connected"`.

## How the two databases have different purposes
- MongoDB is the **source of truth**: create and update item reports here.
- Redis is a **cache**: it temporarily stores the list of reports to reduce repeated MongoDB reads.
- Redis cache is disposable. If Redis is unavailable, the app attempts to continue reading/writing item data using MongoDB; the health endpoint will show Redis as disconnected.

## Common problems
- **MONGODB_URI missing:** ensure `.env` is named exactly `.env`, in the same folder as `main.py`, and contains the variable.
- **MongoDB connection fails:** check Atlas IP access, username/password, cluster address, and URL-encode special characters in the password.
- **Redis connection fails:** use the exact Redis Cloud connection URL and verify its TLS scheme (`rediss://` for TLS).
- **Form errors:** ensure dependencies installed successfully; `python-multipart` is required for HTML forms.
- **Port in use:** run `uvicorn main:app --reload --port 8001`, then open http://127.0.0.1:8001.

## Suggested viva explanation
"My project is a Campus Lost & Found Portal. It connects one application to two NoSQL databases. MongoDB stores the permanent item reports because it supports document-based records. Redis is used as a temporary cache for the report list, so repeated page loads can be faster. When a report is added or updated, the cache is cleared to avoid showing stale information. FastAPI connects the frontend to both databases."
