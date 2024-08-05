import asyncio
import websockets
import json

clients = set()

async def handler(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'offer' or data['type'] == 'answer' or data['type'] == 'candidate':
                await broadcast(data, websocket)
    except Exception as e:
        print(f"Connection handler failed: {e}")
    finally:
        clients.remove(websocket)

async def broadcast(message, sender):
    for client in clients:
        if client != sender:
            await client.send(json.dumps(message))

start_server = websockets.serve(handler, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
