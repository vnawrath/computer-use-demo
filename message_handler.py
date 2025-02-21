import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Set, Optional
from websockets.server import WebSocketServerProtocol


class MessageHandler:
    def __init__(self):
        self.connections: Set[WebSocketServerProtocol] = set()
        self.active_instructions: Dict[str, asyncio.Event] = {}

    async def register(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket connection."""
        self.connections.add(websocket)

    async def unregister(self, websocket: WebSocketServerProtocol):
        """Unregister a WebSocket connection."""
        self.connections.remove(websocket)

    def create_message(
        self, content: str, msg_type: str, metadata: Optional[dict] = None
    ) -> dict:
        """Create a message object with metadata."""
        return {
            "id": str(uuid.uuid4()),
            "content": content,
            "type": msg_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.connections:
            return

        message_json = json.dumps(message)
        await asyncio.gather(
            *(connection.send(message_json) for connection in self.connections)
        )

    async def handle_instruction(self, instruction: str, computer_use_client) -> str:
        """Handle an instruction and stream updates to connected clients."""
        instruction_id = str(uuid.uuid4())
        completion_event = asyncio.Event()
        self.active_instructions[instruction_id] = completion_event

        try:
            # Send initial user message
            await self.broadcast(self.create_message(instruction, "user"))

            # Create a modified message handler for the computer use client
            async def message_callback(content_block):
                message = self.create_message(
                    content=content_block.get("content", content_block.get("text", "")),
                    msg_type=content_block.get("type", "assistant"),
                    metadata=content_block.get("metadata", {}),
                )
                await self.broadcast(message)

            # Send instruction to computer use client with streaming
            response = await computer_use_client.send_instruction_async(
                instruction, message_callback=message_callback
            )

            # Mark instruction as complete
            completion_event.set()
            return instruction_id

        except Exception as e:
            # Send error message
            error_message = self.create_message(
                f"Error processing instruction: {str(e)}", "error"
            )
            await self.broadcast(error_message)
            raise
        finally:
            self.active_instructions.pop(instruction_id, None)

    async def wait_for_instruction_completion(self, instruction_id: str):
        """Wait for an instruction to complete."""
        event = self.active_instructions.get(instruction_id)
        if event:
            await event.wait()
