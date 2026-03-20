"""
Entry Point - Cremas Inventory

Uso:
    python main.py
    
O con uvicorn:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import uvicorn

from src.api.main import app


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
