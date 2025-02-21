# OmniParser Demo Implementation Plan

## Overview

Add a live demo of OmniParser V2 to the providers slide, which will analyze the current e2b desktop screenshot and display detected UI elements with bounding boxes.

## Required Dependencies

```
ultralytics==8.1.2
huggingface_hub==0.21.4
```

## New Files to Create

1. `omniparser_manager.py`

   - Singleton class to manage OmniParser model instance
   - Methods for model loading and inference
   - Caching mechanism for model to avoid reloading

2. `static/js/omniparser_demo.js`
   - JavaScript for handling the demo UI
   - Canvas overlay for drawing bounding boxes
   - Loading state management
   - WebSocket communication for real-time updates

## Files to Modify

1. `templates/slide_providers.html`

   - Add canvas overlay for bounding box visualization
   - Add "Analyze Screenshot" button
   - Add loading indicator
   - Update OmniParser section layout
   - Include new JavaScript file

2. `app.py`

   - Add new endpoint `/analyze-screenshot` for OmniParser inference
   - Add WebSocket endpoint for real-time analysis updates
   - Initialize OmniParser manager

3. `requirements.txt`
   - Add new dependencies

## API Design

### New Endpoints

1. POST `/analyze-screenshot`
   - Input: None (uses current desktop screenshot)
   - Output: JSON with detected elements
   ```json
   {
     "detections": [
       {
         "confidence": float,
         "coordinates": [x1, y1, x2, y2],
         "class": string
       }
     ]
   }
   ```

### WebSocket Events

1. Client -> Server

   - `analyze_request`: Request to analyze current screenshot

2. Server -> Client
   - `analysis_started`: Indicates analysis has begun
   - `analysis_complete`: Contains detection results
   - `analysis_error`: Contains error message if analysis fails

## Implementation Steps

1. Set up dependencies

   - Add new packages to requirements.txt
   - Install using uv

2. Create OmniParser Manager

   - Implement model loading and caching
   - Add inference methods
   - Add error handling

3. Update Frontend

   - Add canvas overlay system
   - Implement bounding box drawing
   - Add loading states
   - Style new elements

4. Add Backend Support

   - Implement new endpoints
   - Add WebSocket handlers
   - Connect to OmniParser manager

5. Testing
   - Test model loading
   - Test inference on different screenshots
   - Test WebSocket communication
   - Test UI responsiveness

## Security Considerations

1. Model Loading

   - Implement timeout for model loading
   - Add error handling for failed downloads
   - Cache model file securely

2. API Endpoints
   - Rate limiting for analysis requests
   - Validation of WebSocket messages
   - Error handling for all endpoints

## Performance Considerations

1. Model Optimization

   - Cache model in memory
   - Optimize inference for CPU usage
   - Handle concurrent requests efficiently

2. Frontend Performance
   - Optimize canvas rendering
   - Debounce analysis requests
   - Efficient WebSocket message handling
