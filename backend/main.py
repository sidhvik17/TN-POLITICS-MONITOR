from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from database import get_db, init_db
from models import User, AuditLog
from auth import verify_password, create_access_token, get_current_user
from routers import alerts, posts, analytics, admin, reports
from config import COLLECTION_ENABLED, COLLECTION_INTERVAL_SECONDS
from services.collectors import run_collection_cycle

app = FastAPI(
    title="TN Politics Monitor API",
    description="Tamil Nadu Politics Social Listening System - Election Commission",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(alerts.router)
app.include_router(posts.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(reports.router)


async def _collector_background_loop():
    """
    Background task that periodically pulls REAL external data
    (e.g. news RSS) into the database. No synthetic posts are
    generated here.
    """
    while True:
        try:
            created = run_collection_cycle()
            # Optional: could log created count here.
        except Exception:
            # Swallow exceptions so the loop keeps running.
            pass
        await asyncio.sleep(COLLECTION_INTERVAL_SECONDS)


@app.on_event("startup")
async def on_startup():
    init_db()
    if COLLECTION_ENABLED:
        asyncio.create_task(_collector_background_loop())


# ---- Auth endpoints ----
@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(data={"sub": user.username, "role": user.role})
    user.last_login = datetime.utcnow()

    db.add(AuditLog(
        user_id=user.id, username=user.username,
        action="LOGIN", resource_type="auth",
        details={"method": "password"}
    ))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone
        }
    }


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "phone": current_user.phone,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


# ---- WebSocket for real-time alerts ----
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or handle commands
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/health")
def health():
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
