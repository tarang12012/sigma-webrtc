import asyncio
import socketio
import cv2
import av

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack
)

# ---------------- SIGNALING SERVER ---------------- #

SERVER_URL = "https://sigma-webrtc.onrender.com"

# ---------------- SOCKET.IO ---------------- #

sio = socketio.AsyncClient()

# ---------------- CAMERA ---------------- #

camera = cv2.VideoCapture(0)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_FPS, 20)

# ---------------- VIDEO TRACK ---------------- #

class CameraTrack(VideoStreamTrack):

    async def recv(self):

        pts, time_base = await self.next_timestamp()

        ret, frame = camera.read()

        if not ret:
            return None

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        video_frame = av.VideoFrame.from_ndarray(
            frame,
            format="rgb24"
        )

        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

# ---------------- RTC CONNECTION ---------------- #

pc = RTCPeerConnection({

    "iceServers":[

        {
            "urls":[
                "stun:stun.l.google.com:19302"
            ]
        }
    ]
})

# ---------------- DATA CHANNEL ---------------- #

@pc.on("datachannel")
def on_datachannel(channel):

    print("Data channel connected")

    @channel.on("message")
    def on_message(message):

        print("Robot Command:", message)

        if message == "F":

            print("Moving Forward")

        elif message == "B":

            print("Moving Backward")

        elif message == "L":

            print("Turning Left")

        elif message == "R":

            print("Turning Right")

        elif message == "S":

            print("Stopping")

# ---------------- SOCKET CONNECT ---------------- #

@sio.event
async def connect():

    print("Connected to signaling server")

    await sio.emit(

        "register",

        {
            "type":"robot"
        }
    )

# ---------------- SIGNALS ---------------- #

@sio.event
async def signal(data):

    if data["type"] == "offer":

        print("Received offer")

        offer = RTCSessionDescription(

            sdp=data["sdp"],
            type=data["type"]
        )

        await pc.setRemoteDescription(offer)

        pc.addTrack(CameraTrack())

        answer = await pc.createAnswer()

        await pc.setLocalDescription(answer)

        await sio.emit(

            "signal",

            {
                "target":"browser",

                "type":"answer",

                "sdp":pc.localDescription.sdp
            }
        )

# ---------------- MAIN ---------------- #

async def main():

    await sio.connect(SERVER_URL)

    await sio.wait()

asyncio.run(main())
