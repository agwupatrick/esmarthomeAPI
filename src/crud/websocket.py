import asyncio
from typing import List, Tuple
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.schemas import schemas

# initialize the classifier that we will use
cascade_classifier = cv2.CascadeClassifier()

async def receive(websocket: WebSocket, queue: asyncio.Queue):
    """
    This is the asynchronous function that will be used to receive 
    websocket connections from the web page.
    """
    received_bytes = await websocket.receive_bytes()
    try:
        queue.put_nowait(received_bytes)
    except asyncio.QueueFull:
        pass  # Optionally, log that the queue is full and the data was not added.

async def detect(websocket: WebSocket, queue: asyncio.Queue):
    """
    This function takes the received request and sends it to the classifier
    which detects the presence of human faces. It returns the location of 
    faces from the continuous stream of visual data as a list of tuples, 
    each representing the four sides of a rectangle.
    """
    while True:
        received_bytes = await queue.get()
        data = np.frombuffer(received_bytes, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)

        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = cascade_classifier.detectMultiScale(gray)

            if len(faces) > 0:
                faces_output = schemas.Faces(faces=faces.tolist())
            else:
                faces_output = schemas.Faces(faces=[])

            await websocket.send_json(faces_output.dict())
        else:
            await websocket.send_json({"error": "Invalid image data"})
