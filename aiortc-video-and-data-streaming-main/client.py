import argparse
import asyncio
import logging
import os
import platform
import json
import cv2  # OpenCV kütüphanesi eklendi
import websockets
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay

ROOT = os.path.dirname(__file__)

relay = None
webcam = None

def create_local_tracks():
    global relay, webcam

    options = {
        "framerate": "30",
        "video_size": "640x480",
    }
    if relay is None:
        if platform.system() == "Darwin":
            webcam = MediaPlayer("default:none", format="avfoundation", options=options)
        elif platform.system() == "Windows":
            webcam = MediaPlayer("video=Integrated Camera", format="dshow", options=options)
        else:
            webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
        relay = MediaRelay()
    return None, relay.subscribe(webcam.video)

async def consume_video_track(track):
    """
    Gelen video akışını tüket ve OpenCV penceresinde göster.
    """
    print("Started consuming video track")
    while True:
        try:
            frame = await track.recv()
            print("Frame received")
            img = frame.to_ndarray(format="bgr24")  # aiortc çerçevesini OpenCV formatına çevir
            cv2.imshow("Received Video", img)  # OpenCV penceresinde göster

            # 'q' tuşuna basıldığında pencereyi kapat
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Error consuming video track: {e}")
            break

    cv2.destroyAllWindows()
    print("Stopped consuming video track")

async def send_data(channel):
    """
    DataChannel üzerinden sürekli olarak "Hello World" mesajı gönderir.
    """
    while True:
        if channel.readyState == "open":
            channel.send("Hello World")
            print("Sent: Hello World")
            await asyncio.sleep(0.1)  # 100 milisaniyede bir mesaj gönder
        else:
            print(f"Channel state: {channel.readyState}")
            await asyncio.sleep(1)  # Kanalın açılmasını bekle

async def run(pc, signaling, role):
    await signaling.connect()
    print(f"Signaling connected as {role}")

    if role == "offer":
        # create an offer
        data_channel = pc.createDataChannel("chat")

        @data_channel.on("open")
        def on_open():
            print("Data channel opened")
            asyncio.ensure_future(send_data(data_channel))

        @data_channel.on("message")
        def on_message(message):
            print(f"Received: {message}")

        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)
        print("Offer sent")

        # wait for answer
        answer = await signaling.receive()
        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer["sdp"], type=answer["type"]))
        print("Answer received and set")

    else:
        # wait for offer
        offer = await signaling.receive()
        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer["sdp"], type=offer["type"]))
        print("Offer received and set")

        # create an answer
        await pc.setLocalDescription(await pc.createAnswer())
        await signaling.send(pc.localDescription)
        print("Answer sent")

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("open")
            def on_open():
                print("Data channel opened")
                asyncio.ensure_future(send_data(channel))

            @channel.on("message")
            def on_message(message):
                print(f"Received: {message}")

    # handle incoming media
    @pc.on("track")
    async def on_track(track):
        print(f"Track received: {track.kind}")

        if track.kind == "video":
            print("Starting to consume video track")
            asyncio.ensure_future(consume_video_track(track))

        @track.on("ended")
        async def on_ended():
            print("Track ended")

    # keep the program running
    await asyncio.Future()

class WebSocketSignaling:
    def __init__(self, uri):
        self._uri = uri
        self._websocket = None

    async def connect(self):
        self._websocket = await websockets.connect(self._uri)
        print("WebSocket connected")

    async def send(self, message):
        if isinstance(message, RTCSessionDescription):
            message = {
                "type": message.type,
                "sdp": message.sdp
            }
        await self._websocket.send(json.dumps(message))
        print(f"Sent: {message}")

    async def receive(self):
        message = await self._websocket.recv()
        print(f"Received: {message}")
        return json.loads(message)

    async def close(self):
        await self._websocket.close()
        print("WebSocket closed")

async def main():
    parser = argparse.ArgumentParser(description="WebRTC client")
    parser.add_argument("role", choices=["offer", "answer"])
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument("--ws-url", default="ws://localhost:8765", help="WebSocket server URL")
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    signaling = WebSocketSignaling(args.ws_url)
    pc = RTCPeerConnection()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()

    # create media source
    if args.role == "offer":
        # Only the "offer" role creates the media source
        audio, video = create_local_tracks()
        if video:
            pc.addTrack(video)
            print("Added video track")

    await run(pc, signaling, args.role)

if __name__ == "__main__":
    asyncio.run(main())

