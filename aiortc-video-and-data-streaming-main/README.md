# WebRTC and aiortc Video Streaming Project

This project uses the WebRTC and aiortc libraries to facilitate real-time video streaming. It consists of two main components: a WebSocket server and a WebRTC client.

## Files

The project consists of the following files:

- `server.py`: Python script that starts the WebSocket server and manages inter-client messaging.
- `client.py`: Python script that uses aiortc to provide video streaming and establish a WebRTC connection.
- `index.html`: HTML file that displays the video stream in a web browser and establishes the WebRTC connection.

## server.py Description

`server.py` sets up a server for inter-client communication over the WebSocket protocol. This server routes the necessary signaling data for the WebRTC connection (offer, answer, candidate messages).

### Main Functions

- `handler(websocket, path)`: Called when a new WebSocket connection starts. Registers clients and processes incoming messages.
- `broadcast(message, sender)`: Forwards a message from one client to all other connected clients.

## client.py Description

`client.py` uses the aiortc library to communicate over video and data channels.

### Main Functions

- `create_local_tracks()`: Opens the video device and starts the media stream.
- `consume_video_track(track)`: Receives incoming video streams and visualizes them using OpenCV.
- `send_data(channel)`: Continuously sends messages over the data channel.
- `run(pc, signaling, role)`: Manages signal processing and WebRTC connections.

## index.html Description

This HTML file displays the video stream in a browser and establishes the WebRTC connection using JavaScript.

### JavaScript Functions

- `start()`: Initiates the signaling connection over WebSocket and processes WebRTC offers or answers.

## Setup and Execution

1. Install the required libraries:
   ```bash
   pip install websockets aiortc opencv-python-headless
