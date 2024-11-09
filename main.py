from typing import Optional
from fastapi import FastAPI
import threading
from fastapi.middleware.cors import CORSMiddleware
from src.routers import user_auth, sensordata, websocket,device

app = FastAPI()

# Configure CORS
origins = ["*"]  # Allow all origins; adjust for production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for health check or simple message."""
    return {"message": "esmart Api"}

#router endpoints
app.include_router(user_auth.router)
app.include_router(sensordata.router)
app.include_router(websocket.router)
app.include_router(device.router)

