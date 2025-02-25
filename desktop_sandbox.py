from e2b_desktop import Sandbox
import io
from PIL import Image
from dotenv import load_dotenv
import asyncio

load_dotenv()


class DesktopManager:
    _instance = None
    _sandbox = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DesktopManager, cls).__new__(cls)
        return cls._instance

    @property
    def is_running(self):
        """Check if the sandbox is running"""
        return self._sandbox is not None

    async def start(self):
        """Start the sandbox if it's not already running"""
        if not self.is_running:
            loop = asyncio.get_event_loop()
            self._sandbox = await loop.run_in_executor(
                None, lambda: Sandbox(timeout=3_600)
            )

    async def stop(self):
        """Stop the sandbox if it's running"""
        if self.is_running:
            await self.cleanup()

    async def restart(self):
        """Restart the sandbox"""
        await self.stop()
        await self.start()

    @property
    def sandbox(self):
        if not self.is_running:
            raise RuntimeError("Sandbox is not running. Call start() first.")
        return self._sandbox

    def get_screen_size(self):
        """Get the current screen size from the sandbox.

        Returns:
            tuple: A tuple containing (width, height) of the screen.
        """
        return self._sandbox.get_screen_size()

    async def move_mouse(self, x: int, y: int):
        """Move mouse to specified coordinates"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._sandbox.move_mouse(x, y))

    async def left_click(self):
        """Perform left click"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sandbox.left_click)

    async def right_click(self):
        """Perform right click"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sandbox.right_click)

    async def middle_click(self):
        """Perform middle click"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sandbox.middle_click)

    async def double_click(self):
        """Perform double click"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sandbox.double_click)

    async def scroll(self, amount: int):
        """Scroll by specified amount"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._sandbox.scroll(amount))

    async def write(self, text: str):
        """Write text"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._sandbox.write(text))

    async def press(self, key: str):
        """Press a special key"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._sandbox.press(key))

    async def hotkey(self, *keys: str):
        """Press hotkey combination"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._sandbox.hotkey(*keys))

    async def take_screenshot(self):
        """Take a screenshot and return it as bytes"""
        loop = asyncio.get_event_loop()
        screenshot_bytes = await loop.run_in_executor(
            None, self._sandbox.take_screenshot
        )
        image = Image.open(io.BytesIO(screenshot_bytes))

        # Convert to JPEG for smaller size
        output = io.BytesIO()
        await loop.run_in_executor(
            None, lambda: image.save(output, format="JPEG", quality=85)
        )
        return output.getvalue()

    async def cleanup(self):
        """Cleanup the sandbox when needed"""
        if self._sandbox:
            await asyncio.get_event_loop().run_in_executor(None, self._sandbox.close)
            self._sandbox = None
