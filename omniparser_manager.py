import os
import io
from typing import List, Dict, Any, Optional
from PIL import Image
import asyncio
from ultralytics import YOLO
from huggingface_hub import hf_hub_download


class OmniParserManager:
    _instance = None
    _model = None
    _model_path = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OmniParserManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the OmniParser manager."""
        self._model = None
        self._model_path = None
        self._lock = asyncio.Lock()

    async def get_model(self) -> YOLO:
        """Get or load the OmniParser model."""
        async with self._lock:
            if self._model is None:
                try:
                    self._model_path = hf_hub_download(
                        repo_id="microsoft/OmniParser-v2.0",
                        filename="icon_detect/model.pt",
                        repo_type="model",
                    )
                    self._model = YOLO(self._model_path)
                except Exception as e:
                    raise

            return self._model

    async def analyze_image(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Analyze an image using OmniParser."""
        try:
            # Get model (will load if not loaded)
            model = await self.get_model()

            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Run inference
            results = model(image, verbose=False)

            # Process results
            detections = []
            for r in results:
                for box in r.boxes:
                    detection = {
                        "confidence": float(box.conf.item()),
                        "coordinates": box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                        "class": r.names[int(box.cls.item())],
                    }
                    detections.append(detection)

            return detections

        except Exception as e:
            raise

    async def cleanup(self):
        """Cleanup resources."""
        self._model = None
        if self._model_path and os.path.exists(self._model_path):
            try:
                os.remove(self._model_path)
                self._model_path = None
            except Exception as e:
                pass
