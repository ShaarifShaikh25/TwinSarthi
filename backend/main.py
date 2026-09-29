"""backend/main.py

Entry point importing production POLAR-TWIN FastAPI application.
Ensures both `uvicorn main:app` and `uvicorn app.main:app` operate seamlessly.
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
