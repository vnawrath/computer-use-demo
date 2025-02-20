from e2b_desktop import Sandbox
import io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class DesktopManager:
    _instance = None
    _sandbox = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DesktopManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if self._sandbox is None:
            self._sandbox = Sandbox(video_stream=True)

    @property
    def sandbox(self):
        return self._sandbox

    def get_stream_url(self):
        return self._sandbox.get_video_stream_url()

    def take_screenshot(self):
        """Take a screenshot and return it as bytes"""
        screenshot_bytes = self._sandbox.take_screenshot()
        image = Image.open(io.BytesIO(screenshot_bytes))

        # Convert to JPEG for smaller size
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85)
        return output.getvalue()

    def cleanup(self):
        """Cleanup the sandbox when needed"""
        if self._sandbox:
            self._sandbox.close()
            self._sandbox = None
