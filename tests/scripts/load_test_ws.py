import asyncio
import sys
import os
import json
import logging
from datetime import datetime

# Add app to path to import utils
sys.path.append(os.getcwd())

from app.core.security import create_access_token
from app.models.user import UserRole
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LoadTest")

async def simulate_student(client_id: int, session_id: int, token: str):
    uri = f"ws://localhost:8000/api/v1/ws/sessions/{session_id}?token={token}"
    try:
        async with websockets.connect(uri) as websocket:
            # logger.info(f"Client {client_id}: Connected")
            
            # Wait for join message (from self or broadcast)
            # data = await websocket.recv()
            
            # Send PING
            ping = {"type": "PING", "session_id": session_id, "timestamp": datetime.utcnow().isoformat()}
            await websocket.send(json.dumps(ping))
            
            # Wait for PONG
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get("type") == "PONG":
                    return True
            except asyncio.TimeoutError:
                logger.error(f"Client {client_id}: Timeout waiting for PONG")
                return False
                
    except Exception as e:
        logger.error(f"Client {client_id}: Connection failed - {e}")
        return False
    return True

async def main():
    concurrency = 50
    session_id = 1 # Assuming session 1 exists and is active (might need setup)
    
    # Generate token for a generic student (ID 2)
    # Note: In real load test, we should use different user IDs to mimic real users
    # But for concurrency check of the server handling connections, same user is okay (if logic permits)
    # Logic permits checking class_id.
    # To be safe, let's assume we are testing connection handling, not deep business logic per user.
    # However, connection manager stores by user_id?
    # manager.connect(ws, session_id, user_id).
    # If same user connects multiple times, manager might overwrite or append?
    # app/core/websocket.py: self.active_connections[session_id].append({'ws': websocket, 'uid': user_id})
    # So it supports multiple connections per user (e.g. multiple tabs).
    
    token = create_access_token(data={"sub": "2", "role": UserRole.STUDENT})
    
    logger.info(f"Starting load test with {concurrency} concurrent connections...")
    
    tasks = []
    for i in range(concurrency):
        tasks.append(simulate_student(i, session_id, token))
    
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    logger.info(f"Load Test Finished: {success_count}/{concurrency} successful connections.")
    
    if success_count == concurrency:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILURE")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
