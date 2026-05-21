import cv2
import av
from serial8 import *
from aiohttp import web

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack
)

# ---------------- FRONT CAMERA ---------------- #

front_cam = cv2.VideoCapture(0)

# ---------------- BACK CAMERA ---------------- #

back_cam = cv2.VideoCapture(2)

# ---------------- CAMERA SETTINGS ---------------- #

# ---------------- FRONT CAMERA SETTINGS ---------------- #

front_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
front_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
front_cam.set(cv2.CAP_PROP_FPS, 20)

front_cam.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*'MJPG')
)

front_cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# ---------------- BACK CAMERA SETTINGS ---------------- #

back_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
back_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
back_cam.set(cv2.CAP_PROP_FPS, 10)

back_cam.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*'MJPG')
)

back_cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# ---------------- CHECK CAMERAS ---------------- #

if not front_cam.isOpened():

    print("Cannot access FRONT camera")
    exit()

if not back_cam.isOpened():

    print("Cannot access BACK camera")
    exit()

# ---------------- FRONT VIDEO TRACK ---------------- #

class FrontCameraTrack(VideoStreamTrack):

    async def recv(self):

        pts, time_base = await self.next_timestamp()

        ret, frame = front_cam.read()

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

# ---------------- BACK VIDEO TRACK ---------------- #

class BackCameraTrack(VideoStreamTrack):

    async def recv(self):

        pts, time_base = await self.next_timestamp()

        ret, frame = back_cam.read()

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

# ---------------- MAIN PAGE ---------------- #

async def index(request):

    return web.FileResponse("index.html")

# ---------------- FRONT OFFER ---------------- #

async def offer_front(request):

    params = await request.json()

    offer = RTCSessionDescription(
        sdp=params["sdp"],
        type=params["type"]
    )

    pc = RTCPeerConnection()

    @pc.on("datachannel")
    def on_datachannel(channel):

        @channel.on("message")
        def on_message(message):

            print("Command:", message)

            if message == "F":

                print("Moving Forward")
                send_2()

            elif message == "B":

                print("Moving Backward")
                send_8()

            elif message == "L":

                print("Turning Left")
                send_4()

            elif message == "R":

                print("Turning Right")
                send_6()

            elif message == "S":

                print("Stopping Robot")
                send_5()

    pc.addTrack(FrontCameraTrack())

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()

    await pc.setLocalDescription(answer)

    return web.json_response({

        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

# ---------------- BACK OFFER ---------------- #

async def offer_back(request):

    params = await request.json()

    offer = RTCSessionDescription(
        sdp=params["sdp"],
        type=params["type"]
    )

    pc = RTCPeerConnection()

    pc.addTrack(BackCameraTrack())

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()

    await pc.setLocalDescription(answer)

    return web.json_response({

        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

# ---------------- APP ---------------- #

app = web.Application()

app.router.add_get("/", index)

app.router.add_post(
    "/offer_front",
    offer_front
)

app.router.add_post(
    "/offer_back",
    offer_back
)

# ---------------- RUN ---------------- #

web.run_app(

    app,

    host="0.0.0.0",

    port=5000
)