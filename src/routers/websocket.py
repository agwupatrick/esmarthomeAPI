import asyncio
from src.crud.websocket import detect, receive, WebSocket, WebSocketDisconnect
from src.utils.commonImports import *

router = APIRouter(prefix="/websocket", tags=["websocket"])

@router.websocket("/face-detection")
async def face_detection(websocket: WebSocket):
    """
    This is the endpoint that will receive requests from the frontend.
    """
    await websocket.accept()
    queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=10)  # Explicit type hint for the queue
    detect_task = asyncio.create_task(detect(websocket, queue))

    try:
        while True:
            await receive(websocket, queue)
    except WebSocketDisconnect:
        print("WebSocket disconnected.")
        detect_task.cancel()
        await websocket.close()
    except asyncio.CancelledError:
        # Handle any cleanup if needed when the detect_task is canceled.
        print("Detect task was cancelled.")
    except Exception as e:
        # Generic error handling for unexpected issues
        print(f"An unexpected error occurred: {e}")
        await websocket.close()
