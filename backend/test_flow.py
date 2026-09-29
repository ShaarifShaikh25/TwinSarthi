import asyncio
import httpx
import websockets
import json

async def test_integration():
    print("Testing /simulate API...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://127.0.0.1:8000/simulate")
            print(f"API Response: {response.json()}")
        except Exception as e:
            print(f"Failed to call /simulate: {e}")
            return

    print("\nConnecting to WebSocket for real-time data...")
    try:
        async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
            print("Connected! Waiting for 3 simulation ticks...")
            for i in range(3):
                message = await ws.recv()
                data = json.loads(message)
                print(f"[{i+1}/3] Received Data:")
                print(json.dumps(data, indent=2))
            print("Successfully received data stream.")
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())
