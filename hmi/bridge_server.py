#!/usr/bin/env python3
"""
OpenClaw HMI Bridge Server
Connects web UI to OpenClaw Gateway via WebSocket
"""

import asyncio
import websockets
import websockets.client
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Configuration
HMI_WS_PORT = 8091  # WebSocket port for HMI
HTTP_PORT = 8090     # HTTP port for serving UI
GATEWAY_URL = "ws://127.0.0.1:18789"
GATEWAY_TOKEN = "aE4HVWIzWoYOPK48iALheEFWMgWKsa1P"
AGENT_ID = "main"

# Store active connections
hmi_clients = set()
gateway_ws = None

async def connect_to_gateway():
    """Connect to OpenClaw Gateway"""
    global gateway_ws
    try:
        # Connect to OpenClaw Gateway with auth
        gateway_ws = await websockets.client.connect(
            f"{GATEWAY_URL}?token={GATEWAY_TOKEN}"
        )
        print(f"✓ Connected to OpenClaw Gateway at {GATEWAY_URL}")
        
        # Authenticate
        auth_msg = {
            "type": "auth",
            "agentId": AGENT_ID,
            "token": GATEWAY_TOKEN
        }
        await gateway_ws.send(json.dumps(auth_msg))
        
        return gateway_ws
    except Exception as e:
        print(f"✗ Failed to connect to Gateway: {e}")
        return None

async def gateway_listener():
    """Listen for messages from OpenClaw Gateway and forward to HMI clients"""
    global gateway_ws
    while True:
        try:
            if gateway_ws:
                message = await gateway_ws.recv()
                data = json.loads(message)
                
                # Forward to all HMI clients
                if hmi_clients:
                    response = {
                        "type": "response",
                        "data": data
                    }
                    websockets.broadcast(hmi_clients, json.dumps(response))
                    
        except Exception as e:
            print(f"Gateway connection error: {e}")
            gateway_ws = None
            await asyncio.sleep(5)
            gateway_ws = await connect_to_gateway()

async def hmi_handler(websocket, path):
    """Handle HMI WebSocket connections"""
    print(f"HMI client connected from {websocket.remote_address}")
    hmi_clients.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "system",
            "message": "Connected to Lara via HMI Bridge"
        }))
        
        # Handle messages from HMI
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data.get("type") == "chat":
                    # Forward chat message to OpenClaw
                    if gateway_ws:
                        openclaw_msg = {
                            "type": "chat",
                            "text": data.get("text"),
                            "session": "hmi-session",
                            "userId": "1590967509"
                        }
                        await gateway_ws.send(json.dumps(openclaw_msg))
                        
                        # Send acknowledgment to HMI
                        await websocket.send(json.dumps({
                            "type": "status",
                            "message": "Message sent to Lara"
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Gateway not connected"
                        }))
                        
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        hmi_clients.remove(websocket)
        print(f"HMI client disconnected")

async def main():
    """Start bridge server"""
    print("=" * 50)
    print("Lara HMI Bridge Server")
    print("=" * 50)
    
    # Connect to OpenClaw Gateway
    global gateway_ws
    gateway_ws = await connect_to_gateway()
    
    # Start gateway listener
    asyncio.create_task(gateway_listener())
    
    # Start HMI WebSocket server
    hmi_server = await websockets.serve(
        hmi_handler,
        "0.0.0.0",
        HMI_WS_PORT,
        ping_interval=20,
        ping_timeout=10
    )
    
    print(f"✓ HMI WebSocket server running on ws://0.0.0.0:{HMI_WS_PORT}")
    print(f"✓ HTTP server running on http://0.0.0.0:{HTTP_PORT}")
    print("=" * 50)
    
    await asyncio.Future()  # Run forever

def start_http_server():
    """Start HTTP server for serving UI"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(("0.0.0.0", HTTP_PORT), SimpleHTTPRequestHandler)
    print(f"HTTP server started on port {HTTP_PORT}")
    server.serve_forever()

if __name__ == "__main__":
    # Start HTTP server in background thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Start WebSocket bridge
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
