import sqlite3
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Kishkindha Praja Dal API")

# Target voices to unlock the poster
TARGET_WISHES = 30

DB_FILE = "campaign_feedback.db"

def init_db():
    """Creates the SQLite database and feedback table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citizen_name TEXT NOT NULL,
            issue TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Run database initialization on startup
init_db()

class WishSubmission(BaseModel):
    citizen_name: str
    issue: str

@app.get("/api/status")
async def get_status():
    """Returns the current count of submissions and unlock status."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM feedbacks")
    count = cursor.fetchone()[0]
    conn.close()
    
    is_unlocked = count >= TARGET_WISHES
    
    return {
        "current_wishes": count,
        "target_wishes": TARGET_WISHES,
        "is_unlocked": is_unlocked
    }

@app.post("/api/submit_wish")
async def submit_wish(wish: WishSubmission):
    """Saves the citizen's feedback to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Insert new record
    cursor.execute(
        "INSERT INTO feedbacks (citizen_name, issue) VALUES (?, ?)", 
        (wish.citizen_name, wish.issue)
    )
    conn.commit()
    
    # Get updated count
    cursor.execute("SELECT COUNT(*) FROM feedbacks")
    count = cursor.fetchone()[0]
    conn.close()
    
    is_unlocked = count >= TARGET_WISHES
    
    return {
        "status": "success",
        "current_wishes": count,
        "target_wishes": TARGET_WISHES,
        "is_unlocked": is_unlocked
    }

# Ensure the static directory exists (this is where index.html and the image go)
os.makedirs("static", exist_ok=True)

@app.get("/")
async def serve_frontend():
    """Serves the main HTML file when users visit the root URL."""
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse(status_code=404, content={"message": "Frontend not found. Please place index.html in the 'static' folder."})

# Mount the entire static folder to serve images like IMG-20260527-WA0018.jpg
app.mount("/", StaticFiles(directory="static"), name="static")
@app.get("/admin/feedbacks")
async def view_feedbacks():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # This formats the output nicely
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        
        # Return all rows as a JSON list
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Run the server locally on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)