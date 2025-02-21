import os
import base64
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
from anthropic import Anthropic
from desktop_sandbox import DesktopManager
import asyncio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ComputerUseClient:
    _instance = None
    _initialized = False

    def __new__(cls, api_key: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(ComputerUseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Computer Use client with Claude and E2B desktop.

        Args:
            api_key: Anthropic API key. If not provided, will look for ANTHROPIC_API_KEY env var.
        """
        if self._initialized:
            return

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key must be provided or set in ANTHROPIC_API_KEY env var"
            )

        self.client = Anthropic(api_key=self.api_key)
        self.desktop = DesktopManager()
        self.message_history = []

        # Get actual screen dimensions
        width, height = self.desktop.get_screen_size()

        logger.info(f"Screen dimensions: {width}x{height}")

        # Default computer use tool configuration with actual dimensions
        self.default_tools = [
            {
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": width,
                "display_height_px": height,
                "display_number": 1,
            }
        ]

        self._initialized = True

    def _prepare_computer_tools(self) -> List[Dict[str, Any]]:
        """Prepare the computer use tools with current display dimensions."""
        # Return the tools with actual dimensions
        return self.default_tools

    async def _handle_computer_action(
        self,
        action: str,
        input_data: Dict[str, Any],
        message_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> List[Dict[str, Any]]:
        """Handle a computer action and return the tool response content.

        Args:
            action: The action to perform (e.g., 'mouse_move', 'left_click', etc.)
            input_data: The input data for the action
            message_callback: Optional callback for streaming updates

        Returns:
            List of response content items
        """
        tool_response_content = []
        logger.info(f"Handling computer action: {action}")

        try:
            if action == "screenshot":
                pass  # Screenshot will be taken after any action
            elif action == "mouse_move":
                coordinate = input_data["coordinate"]

                try:
                    if isinstance(coordinate, list):
                        x, y = coordinate[0], coordinate[1]
                    else:
                        x, y = coordinate["x"], coordinate["y"]
                except (KeyError, TypeError, IndexError) as e:
                    logger.error(f"Failed to extract x,y coordinates: {e}")
                    logger.error(f"Coordinate structure: {coordinate}")
                    raise

                logger.info(f"Moving mouse to ({x}, {y})")
                await self.desktop.move_mouse(x, y)
                tool_response_content.append(
                    {"type": "text", "text": f"Moved mouse to ({x}, {y})"}
                )
            elif action == "left_click":
                logger.info("Performing left click")
                await self.desktop.left_click()
                tool_response_content.append(
                    {"type": "text", "text": "Performed left click"}
                )
            elif action == "right_click":
                logger.info("Performing right click")
                await self.desktop.right_click()
                tool_response_content.append(
                    {"type": "text", "text": "Performed right click"}
                )
            elif action == "middle_click":
                logger.info("Performing middle click")
                await self.desktop.middle_click()
                tool_response_content.append(
                    {"type": "text", "text": "Performed middle click"}
                )
            elif action == "double_click":
                logger.info("Performing double click")
                await self.desktop.double_click()
                tool_response_content.append(
                    {"type": "text", "text": "Performed double click"}
                )
            elif action == "scroll":
                amount = input_data.get("amount", 0)
                logger.info(f"Scrolling by {amount}")
                await self.desktop.scroll(amount)
                tool_response_content.append(
                    {"type": "text", "text": f"Scrolled by {amount}"}
                )
            elif action == "type":
                text = input_data["text"]
                logger.info(f"Typing text: {text}")
                await self.desktop.write(text)
                tool_response_content.append(
                    {"type": "text", "text": f"Typed text: {text}"}
                )
            elif action == "key":
                # Handle both single key and hotkey combinations
                keys = input_data["text"].split("+")
                if len(keys) > 1:
                    logger.info(f"Pressing hotkey combination: {'+'.join(keys)}")
                    await self.desktop.hotkey(*keys)
                    tool_response_content.append(
                        {"type": "text", "text": f"Pressed hotkey: {'+'.join(keys)}"}
                    )
                else:
                    key = keys[0]
                    # Handle special keys
                    if key == "Return":
                        logger.info("Pressing enter key")
                        await self.desktop.press("enter")
                        tool_response_content.append(
                            {"type": "text", "text": "Pressed enter key"}
                        )
                    else:
                        logger.info(f"Pressing key: {key}")
                        await self.desktop.write(key)
                        tool_response_content.append(
                            {"type": "text", "text": f"Pressed key: {key}"}
                        )
            else:
                logger.warning(f"Unsupported action: {action}")
                tool_response_content.append(
                    {"type": "text", "text": f"Unsupported action: {action}"}
                )

            if message_callback:
                await message_callback(
                    {
                        "type": "tool_result",
                        "content": f"Performed action: {action}",
                        "metadata": input_data,
                    }
                )

        except Exception as e:
            error_msg = f"Error performing {action}: {str(e)}"
            logger.error(error_msg)
            tool_response_content.append({"type": "text", "text": error_msg})
            if message_callback:
                await message_callback(
                    {"type": "error", "content": error_msg, "metadata": {}}
                )

        # Take a screenshot after any action
        screenshot = await self.desktop.take_screenshot()
        screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")

        screenshot_content = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": screenshot_b64,
            },
        }
        tool_response_content.append(screenshot_content)

        if message_callback:
            await message_callback(
                {"type": "screenshot", "metadata": screenshot_content}
            )

        return tool_response_content

    async def send_instruction_async(
        self,
        instruction: str,
        system_message: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        max_iterations: int = 20,
        message_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        """Send an instruction to Claude with computer use capabilities asynchronously.

        Args:
            instruction: The instruction for Claude to execute
            system_message: Optional system message to guide Claude's behavior
            max_tokens: Maximum tokens in the response
            temperature: Temperature for response generation
            max_iterations: Maximum number of tool call iterations
            message_callback: Optional callback for streaming updates

        Returns:
            Claude's final response message
        """
        if system_message is None:
            system_message = """You are a helpful AI assistant with access to computer controls.
            Follow the user's instructions carefully and use the computer interface when needed.
            Always explain what you're doing before taking actions."""

        # Start with the user's instruction
        messages = self.message_history.copy()
        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": instruction}],
        }

        # Take a screenshot before sending to Claude
        screenshot = await self.desktop.take_screenshot()
        screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")

        # Add screenshot to the message
        user_message["content"].append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": screenshot_b64,
                },
            }
        )

        messages.append(user_message)
        iteration = 0

        while iteration < max_iterations:
            try:
                response = self.client.beta.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    betas=["computer-use-2024-10-22"],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message,
                    messages=messages,
                    tools=self._prepare_computer_tools(),
                )

                # Process the response immediately since it's already resolved
                logger.info("Received response from Claude API")

                # Convert Claude's response to a message
                try:
                    assistant_message = {"role": "assistant", "content": []}

                    for block in response.content:
                        content_block = {"type": block.type}

                        if block.type == "text":
                            content_block["text"] = block.text
                        elif block.type == "tool_use":
                            content_block["name"] = block.name
                            content_block["input"] = block.input
                            content_block["id"] = block.id

                        assistant_message["content"].append(content_block)

                    # Add assistant message to history
                    messages.append(assistant_message)

                except Exception as e:
                    logger.error(f"Error creating assistant_message: {e}")
                    logger.error(f"Error type: {type(e)}")
                    raise

                if message_callback:
                    for block in response.content:
                        if block.type == "text":
                            try:
                                await message_callback(
                                    {
                                        "type": "assistant",
                                        "content": block.text,
                                        "metadata": {},
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Error in message callback: {e}")
                                raise

                has_tool_call = False
                message_content = []

                for block in response.content:
                    logger.info(f"Processing block type: {block.type}")

                    if block.type == "tool_use":
                        has_tool_call = True
                        logger.info(f"Tool call: {block.name}")

                        if block.name == "computer":
                            try:
                                tool_response_content = (
                                    await self._handle_computer_action(
                                        block.input["action"],
                                        block.input,
                                        message_callback,
                                    )
                                )
                                # Add tool result to message content
                                message_content.append(
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": tool_response_content,
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Error in computer action: {e}")
                                raise

                if message_content:
                    # Add tool results as a user message
                    tool_result_message = {
                        "role": "user",
                        "content": message_content,
                    }
                    messages.append(tool_result_message)

                if not has_tool_call:
                    return response
                    break

                iteration += 1

            except Exception as e:
                logger.error(f"Error in tool call iteration {iteration}: {e}")
                if message_callback:
                    await message_callback(
                        {"type": "error", "text": f"Error: {str(e)}"}
                    )
                raise

        # Update message history
        self.message_history = messages

        if iteration == max_iterations:
            logger.warning("Max iterations reached without final response")
            return response

        return response

    def send_instruction(
        self,
        instruction: str,
        system_message: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        max_iterations: int = 10,
    ) -> Dict[str, Any]:
        """Synchronous version of send_instruction_async."""
        return asyncio.run(
            self.send_instruction_async(
                instruction,
                system_message,
                max_tokens,
                temperature,
                max_iterations,
            )
        )

    async def cleanup(self):
        """Cleanup resources."""
        await self.desktop.cleanup()


def main():
    """Example usage of the ComputerUseClient."""
    client = ComputerUseClient()

    try:
        # Example instruction
        response = client.send_instruction(
            "Please tell me what you see in the current screen."
        )

        # Print the response
        for content in response.content:
            if content.type == "text":
                print(content.text)
            elif content.type == "tool_use":
                print(f"Tool used: {content.name}")

    finally:
        client.cleanup()


if __name__ == "__main__":
    main()
