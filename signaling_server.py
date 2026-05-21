from aiohttp import web
import socketio

sio = socketio.AsyncServer(
    cors_allowed_origins='*',
    async_mode='aiohttp'
)

app = web.Application()

sio.attach(app)

# ---------------- STORE CLIENTS ---------------- #

clients = {}

# ---------------- CONNECT ---------------- #

@sio.event
async def connect(sid, environ):

    print("Connected:", sid)

# ---------------- REGISTER ---------------- #

@sio.event
async def register(sid, data):

    clients[data["type"]] = sid

    print(f"{data['type']} registered")

# ---------------- SIGNALING ---------------- #

@sio.event
async def signal(sid, data):

    target = data["target"]

    if target in clients:

        await sio.emit(
            "signal",
            data,
            to=clients[target]
        )

# ---------------- DISCONNECT ---------------- #

@sio.event
async def disconnect(sid):

    print("Disconnected:", sid)

# ---------------- MAIN ---------------- #

if __name__ == '__main__':

    web.run_app(
        app,
        host='0.0.0.0',
        port=5000
    )
