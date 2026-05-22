import asyncio
import socketio
import cv2
import av

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
    VideoStreamTrack
)

# =========================================================
# SIGNALING SERVER URL
# =========================================================

SERVER_URL = "https://sigma-webrtc.onrender.com"

# Example:
# SERVER_URL = "https://sigma-webrtc.onrender.com"

# =========================================================
# SOCKET.IO CLIENT
# =========================================================

sio = socketio.AsyncClient()

# =========================================================
# FRONT CAMERA
# =========================================================

camera = cv2.VideoCapture(0)

# ---------------- CAMERA SETTINGS ---------------- #

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_FPS, 20)

camera.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*'MJPG')
)

camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# =========================================================
# CHECK CAMERA
# =========================================================

if not camera.isOpened():

    print("Cannot access camera")

    exit()

print("Camera started successfully")

# =========================================================
# VIDEO TRACK
# =========================================================

class CameraTrack(VideoStreamTrack):

    async def recv(self):

        pts, time_base = await self.next_timestamp()

        ret, frame = camera.read()

        if not ret:

            print("Frame read failed")

            return None

        # ---------------- COLOR FIX ---------------- #

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # ---------------- VIDEO FRAME ---------------- #

        video_frame = av.VideoFrame.from_ndarray(

            frame,

            format="rgb24"
        )

        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

# =========================================================
# RTC CONNECTION
# =========================================================

pc = RTCPeerConnection({

    "iceServers":[

        {
            "urls":[
                "stun:stun.l.google.com:19302"
            ]
        }
    ]
})

# =========================================================
# ICE CANDIDATES
# =========================================================

@pc.on("icecandidate")
async def on_icecandidate(candidate):

    if candidate:

        await sio.emit(

            "signal",

            {

                "target":"browser",

                "type":"candidate",

                "candidate":candidate.to_sdp(),

                "sdpMid":candidate.sdpMid,

                "sdpMLineIndex":candidate.sdpMLineIndex
            }
        )

# =========================================================
# CONNECTION STATE
# =========================================================

@pc.on("connectionstatechange")
async def on_connectionstatechange():

    print(
        "Connection State:",
        pc.connectionState
    )

# =========================================================
# DATA CHANNEL
# =========================================================

@pc.on("datachannel")
def on_datachannel(channel):

    print("Data channel connected")

    @channel.on("message")
    def on_message(message):

        print("Robot Command:", message)

        # =================================================
        # ROBOT CONTROLS
        # =================================================

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

# =========================================================
# SOCKET CONNECT
# =========================================================

@sio.event
async def connect():

    print("Connected to signaling server")

    await sio.emit(

        "register",

        {
            "type":"robot"
        }
    )

# =========================================================
# SIGNAL HANDLER
# =========================================================

@sio.event
async def signal(data):

    print("Signal Received:", data["type"])

    # =====================================================
    # OFFER
    # =====================================================

    if data["type"] == "offer":

        print("Received WebRTC Offer")

        offer = RTCSessionDescription(

            sdp=data["sdp"],

            type=data["type"]
        )

        await pc.setRemoteDescription(offer)

        # ---------------- ADD CAMERA TRACK ---------------- #

        pc.addTrack(CameraTrack())

        # ---------------- CREATE ANSWER ---------------- #

        answer = await pc.createAnswer()

        await pc.setLocalDescription(answer)

        # ---------------- SEND ANSWER ---------------- #

        await sio.emit(

            "signal",

            {

                "target":"browser",

                "type":"answer",

                "sdp":pc.localDescription.sdp
            }
        )

        print("Answer sent")

    # =====================================================
    # ICE CANDIDATE
    # =====================================================

    elif data["type"] == "candidate":

        print("Received ICE candidate")

        candidate = RTCIceCandidate(

            sdpMid=data["sdpMid"],

            sdpMLineIndex=data["sdpMLineIndex"],

            candidate=data["candidate"]
        )

        await pc.addIceCandidate(candidate)

# =========================================================
# SOCKET DISCONNECT
# =========================================================

@sio.event
async def disconnect():

    print("Disconnected from signaling server")

# =========================================================
# MAIN
# =========================================================

async def main():

    print("Starting Sigma Robot Client...")

    await sio.connect(SERVER_URL)

    await sio.wait()

# =========================================================
# START PROGRAM
# =========================================================

asyncio.run(main())