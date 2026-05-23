
from typing import Dict, Set, Optional
from fastapi import WebSocket, status
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class ChatWebSocket:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_times: Dict[WebSocket, datetime] = {}
        self.heartbeat_interval = 30  # seconds
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.connection_times[websocket] = datetime.now()
        asyncio.create_task(self._heartbeat(websocket))
        
    async def disconnect(self, websocket: WebSocket, user_id: str):
        try:
            if user_id in self.active_connections:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    
            # Add cleanup of associated resources
            if websocket in self.connection_times:
                del self.connection_times[websocket]
                
            # Notify other connected clients
            await self._notify_disconnect(user_id)
            
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")
            
    async def _notify_disconnect(self, user_id: str):
        if user_id in self.active_connections:
            message = {"type": "user_disconnected", "user_id": user_id}
            await self.broadcast(user_id, message)
            
    async def _heartbeat(self, websocket: WebSocket):
        while True:
            try:
                await websocket.send_json({"type": "ping"})
                await asyncio.sleep(self.heartbeat_interval)
            except Exception:
                break
                
    async def cleanup_stale_connections(self):
        """Cleanup connections that haven't received heartbeat"""
        stale_time = datetime.now() - timedelta(seconds=self.heartbeat_interval * 2)
        for user_id in list(self.active_connections.keys()):
            for ws in list(self.active_connections[user_id]):
                if self.connection_times.get(ws, datetime.now()) < stale_time:
                    await self.disconnect(ws, user_id)

    async def close_all(self):
        """Close all active WebSocket connections"""
        try:
            for user_id in list(self.active_connections.keys()):
                for websocket in list(self.active_connections[user_id]):
                    try:
                        await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
                        await self.disconnect(websocket, user_id)
                    except Exception as e:
                        logger.error(f"Error closing websocket: {str(e)}")
            
            # Clear all connections
            self.active_connections.clear()
            self.connection_times.clear()
            
        except Exception as e:
            logger.error(f"Error in close_all: {str(e)}")