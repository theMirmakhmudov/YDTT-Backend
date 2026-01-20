"""
WebSocket Connection Manager for Live Sessions.
Manages real-time connections between teachers and students.
"""
from typing import Dict, Set, Optional
import json
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.schemas.websocket_events import WSBaseEvent, WSEventType, WSPingPongEvent

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for live lesson sessions.
    Organizes connections into session-based rooms.
    """
    
    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
        # WebSocket -> user_id mapping for authentication
        self.connection_users: Dict[WebSocket, int] = {}
        
        # WebSocket -> session_id mapping for cleanup
        self.connection_sessions: Dict[WebSocket, int] = {}
    
    async def connect(self, websocket: WebSocket, session_id: int, user_id: int):
        """
        Accept a new WebSocket connection and add to session room.
        
        Args:
            websocket: The WebSocket connection
            session_id: The lesson session ID
            user_id: The authenticated user ID
        """
        await websocket.accept()
        
        # Initialize session room if not exists
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        # Add connection to session room
        self.active_connections[session_id].add(websocket)
        
        # Store user and session mapping
        self.connection_users[websocket] = user_id
        self.connection_sessions[websocket] = session_id
        
        logger.info(f"User {user_id} connected to session {session_id}. "
                   f"Total connections in session: {len(self.active_connections[session_id])}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection and clean up.
        
        Args:
            websocket: The WebSocket connection to remove
        """
        # Get session_id before cleanup
        session_id = self.connection_sessions.get(websocket)
        user_id = self.connection_users.get(websocket)
        
        if session_id and session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            # Clean up empty session rooms
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                logger.info(f"Session {session_id} room closed (no more connections)")
        
        # Clean up mappings
        self.connection_users.pop(websocket, None)
        self.connection_sessions.pop(websocket, None)
        
        if user_id and session_id:
            logger.info(f"User {user_id} disconnected from session {session_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            message: The message dictionary to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_session(
        self,
        session_id: int,
        message: dict,
        exclude: Optional[WebSocket] = None
    ):
        """
        Broadcast a message to all connections in a session room.
        
        Args:
            session_id: The session ID to broadcast to
            message: The message dictionary to send
            exclude: Optional WebSocket to exclude from broadcast (e.g., sender)
        """
        if session_id not in self.active_connections:
            logger.warning(f"Attempted to broadcast to non-existent session {session_id}")
            return
        
        disconnected = []
        
        for connection in self.active_connections[session_id]:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_all_except_sender(
        self,
        websocket: WebSocket,
        message: dict
    ):
        """
        Broadcast a message to all connections in sender's session except sender.
        
        Args:
            websocket: The sender's WebSocket connection
            message: The message dictionary to send
        """
        session_id = self.connection_sessions.get(websocket)
        if session_id:
            await self.broadcast_to_session(session_id, message, exclude=websocket)
    
    def get_session_connection_count(self, session_id: int) -> int:
        """
        Get the number of active connections in a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(session_id, set()))
    
    def get_user_id(self, websocket: WebSocket) -> Optional[int]:
        """
        Get the user ID associated with a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            User ID or None if not found
        """
        return self.connection_users.get(websocket)
    
    def is_user_connected(self, session_id: int, user_id: int) -> bool:
        """
        Check if a user is connected to a session.
        
        Args:
            session_id: The session ID
            user_id: The user ID
            
        Returns:
            True if user is connected, False otherwise
        """
        if session_id not in self.active_connections:
            return False
        
        for websocket in self.active_connections[session_id]:
            if self.connection_users.get(websocket) == user_id:
                return True
        
        return False


# Global connection manager instance
manager = ConnectionManager()
