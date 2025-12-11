# backend/run.py
# Simple script to run the FastAPI server with uvicorn
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting KABS Design Tool API on http://{host}:{port}")
    print(f"📝 Environment: {os.getenv('NODE_ENV', 'development')}")
    print(f"🔗 CORS enabled for: {os.getenv('CORS_ORIGIN', 'http://localhost:5173')}")
    print("")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

