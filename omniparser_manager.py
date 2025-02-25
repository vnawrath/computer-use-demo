import os
import io
from typing import List, Dict, Any, Tuple
from PIL import Image
import asyncio
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
import easyocr
import numpy as np


class OmniParserManager:
    _instance = None
    _model = None
    _model_path = None
    _ocr_reader = None
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
        self._ocr_reader = None
        self._lock = asyncio.Lock()

    async def get_ocr_reader(self) -> easyocr.Reader:
        """Get or initialize the OCR reader."""
        if self._ocr_reader is None:
            # Initialize EasyOCR with English language
            self._ocr_reader = easyocr.Reader(["en"])
        return self._ocr_reader

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

    def _convert_points_to_bbox(self, points: List[List[int]]) -> List[float]:
        """Convert OCR points to bounding box format [x1, y1, x2, y2]."""
        x_coords = [float(p[0]) for p in points]  # Convert to float
        y_coords = [float(p[1]) for p in points]  # Convert to float
        return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate Intersection over Union between two boxes."""
        x1 = max(float(box1[0]), float(box2[0]))  # Convert to float
        y1 = max(float(box1[1]), float(box2[1]))
        x2 = min(float(box1[2]), float(box2[2]))
        y2 = min(float(box1[3]), float(box2[3]))

        if x2 < x1 or y2 < y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        box1_area = (float(box1[2]) - float(box1[0])) * (
            float(box1[3]) - float(box1[1])
        )
        box2_area = (float(box2[2]) - float(box2[0])) * (
            float(box2[3]) - float(box2[1])
        )
        union = box1_area + box2_area - intersection

        return float(intersection / union if union > 0 else 0.0)

    async def detect_text_blocks(
        self, image: np.ndarray, confidence_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Detect text blocks in the image using OCR."""
        reader = await self.get_ocr_reader()
        text_blocks = reader.readtext(image)

        return [
            {
                "confidence": float(result[2]),  # Ensure float
                "coordinates": [
                    float(x) for x in self._convert_points_to_bbox(result[0])
                ],  # Convert to float
                "class": "text",
                "text": str(result[1]),  # Ensure string
            }
            for result in text_blocks
            if float(result[2]) >= confidence_threshold
        ]

    def _merge_detections(
        self,
        text_detections: List[Dict[str, Any]],
        icon_detections: List[Dict[str, Any]],
        iou_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Merge text and icon detections, handling overlaps."""
        merged = []
        used_text_indices = set()

        # First, process icon detections and find overlapping text
        for icon in icon_detections:
            icon_box = [float(x) for x in icon["coordinates"]]  # Convert to float
            best_text = None
            best_iou = 0
            best_text_idx = -1

            # Find best matching text for this icon
            for idx, text in enumerate(text_detections):
                if idx in used_text_indices:
                    continue

                text_box = [float(x) for x in text["coordinates"]]  # Convert to float
                iou = self._calculate_iou(icon_box, text_box)
                if iou > iou_threshold and iou > best_iou:
                    best_iou = iou
                    best_text = text
                    best_text_idx = idx

            if best_text:
                # Merge icon with text
                used_text_indices.add(best_text_idx)
                merged.append(
                    {
                        "confidence": float(icon["confidence"]),  # Ensure float
                        "coordinates": [
                            float(x) for x in icon["coordinates"]
                        ],  # Convert to float
                        "class": str(icon["class"]),  # Ensure string
                        "text": str(best_text["text"]),  # Ensure string
                        "text_confidence": float(
                            best_text["confidence"]
                        ),  # Ensure float
                    }
                )
            else:
                merged.append(
                    {
                        "confidence": float(icon["confidence"]),  # Ensure float
                        "coordinates": [
                            float(x) for x in icon["coordinates"]
                        ],  # Convert to float
                        "class": str(icon["class"]),  # Ensure string
                    }
                )

        # Add remaining text detections
        for idx, text in enumerate(text_detections):
            if idx not in used_text_indices:
                merged.append(
                    {
                        "confidence": float(text["confidence"]),  # Ensure float
                        "coordinates": [
                            float(x) for x in text["coordinates"]
                        ],  # Convert to float
                        "class": str(text["class"]),  # Ensure string
                        "text": str(text["text"]),  # Ensure string
                    }
                )

        return merged

    async def analyze_image(
        self,
        image_bytes: bytes,
        text_confidence_threshold: float = 0.5,
        iou_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Analyze an image using OmniParser and return detections."""
        try:
            # Get model (will load if not loaded)
            model = await self.get_model()

            # Convert bytes to PIL Image and numpy array
            image_pil = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(image_pil)

            # First, detect text blocks
            text_detections = await self.detect_text_blocks(
                image_np, confidence_threshold=text_confidence_threshold
            )

            # Run icon detection
            results = model(image_np, verbose=False)
            icon_detections = []

            for r in results:
                for box in r.boxes:
                    box_coords = [
                        float(x) for x in box.xyxy[0].tolist()
                    ]  # Convert to float
                    detection = {
                        "confidence": float(box.conf.item()),  # Convert to float
                        "coordinates": box_coords,
                        "class": str(r.names[int(box.cls.item())]),  # Convert to string
                    }
                    icon_detections.append(detection)

            # Merge detections
            merged_detections = self._merge_detections(
                text_detections, icon_detections, iou_threshold=iou_threshold
            )

            return merged_detections

        except Exception as e:
            raise

    async def cleanup(self):
        """Cleanup resources."""
        self._model = None
        self._ocr_reader = None
        if self._model_path and os.path.exists(self._model_path):
            try:
                os.remove(self._model_path)
            except Exception:
                pass
