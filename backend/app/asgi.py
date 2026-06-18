from socketio import ASGIApp
from app.main import app as fastapi_app
from app.core.websocket import sio

app = ASGIApp(sio, other_asgi_app=fastapi_app)
