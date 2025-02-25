class OmniParserDemo {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.ws = null;
    this.isAnalyzing = false;
    this.showFirstLabelOnly = false;
    this.setupUI();
    this.connectWebSocket();
  }

  setupUI() {
    // Create canvas overlay
    this.canvas = document.createElement("canvas");
    this.canvas.className = "detection-overlay";
    this.canvas.style.position = "absolute";
    this.canvas.style.top = "50%";
    this.canvas.style.left = "50%";
    this.canvas.style.width = "100%";
    this.canvas.style.height = "100%";
    this.canvas.style.pointerEvents = "none";

    // Create analyze button
    this.analyzeButton = document.createElement("button");
    this.analyzeButton.className = "analyze-button";
    this.analyzeButton.textContent = "Analyze Screenshot";
    this.analyzeButton.onclick = () => this.requestAnalysis();

    // Create toggle button for first label only
    this.toggleButton = document.createElement("button");
    this.toggleButton.className = "analyze-button toggle-button";
    this.toggleButton.textContent = "Show All Labels";
    this.toggleButton.style.right = "180px"; // Position to the left of analyze button
    this.toggleButton.onclick = () => {
      this.showFirstLabelOnly = !this.showFirstLabelOnly;
      this.toggleButton.textContent = this.showFirstLabelOnly
        ? "Show First Label"
        : "Show All Labels";
      // Redraw detections if we have any
      if (this.lastDetections) {
        this.drawDetections(this.lastDetections);
      }
    };

    // Create loading indicator
    this.loadingIndicator = document.createElement("div");
    this.loadingIndicator.className = "loading-indicator";
    this.loadingIndicator.textContent = "Analyzing...";
    this.loadingIndicator.style.display = "none";

    // Add elements to container
    this.container.style.position = "relative";
    this.container.appendChild(this.canvas);
    this.container.appendChild(this.analyzeButton);
    this.container.appendChild(this.toggleButton);
    this.container.appendChild(this.loadingIndicator);

    // Handle window resize
    window.addEventListener("resize", () => this.resizeCanvas());
    this.resizeCanvas();
  }

  resizeCanvas() {
    const sourceImage = this.container.querySelector("img");
    const containerWidth = this.container.offsetWidth;
    const containerHeight = this.container.offsetHeight;

    // Calculate the dimensions the image will actually display at
    // while maintaining aspect ratio
    const sourceAspectRatio = 1024 / 768;
    const containerAspectRatio = containerWidth / containerHeight;

    let displayedWidth, displayedHeight;
    let marginLeft = 0,
      marginTop = 0;

    if (containerAspectRatio > sourceAspectRatio) {
      // Container is wider than image aspect ratio
      displayedHeight = containerHeight;
      displayedWidth = containerHeight * sourceAspectRatio;
      marginLeft = (containerWidth - displayedWidth) / 2;
    } else {
      // Container is taller than image aspect ratio
      displayedWidth = containerWidth;
      displayedHeight = containerWidth / sourceAspectRatio;
      marginTop = (containerHeight - displayedHeight) / 2;
    }

    // Set canvas size to match the container
    this.canvas.width = containerWidth;
    this.canvas.height = containerHeight;

    // Store these values for use in drawDetections
    this.imageDisplayInfo = {
      displayedWidth,
      displayedHeight,
      marginLeft,
      marginTop,
    };
  }

  connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/omniparser`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.analyzeButton.disabled = false;
    };

    this.ws.onclose = () => {
      this.analyzeButton.disabled = true;
      setTimeout(() => this.connectWebSocket(), 5000);
    };

    this.ws.onerror = (error) => {
      this.analyzeButton.disabled = true;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        // Silently handle error
      }
    };
  }

  handleMessage(message) {
    console.log("[OmniParser] Received message:", message);
    switch (message.type) {
      case "analysis_started":
        this.showLoading(true);
        break;

      case "analysis_complete":
        console.log(
          "[OmniParser] Analysis complete with detections:",
          message.detections
        );
        this.showLoading(false);
        if (message.detections && message.detections.length > 0) {
          console.log("[OmniParser] Drawing detections...");
          this.drawDetections(message.detections);
        } else {
          console.log("[OmniParser] No detections to draw");
        }
        break;

      case "analysis_error":
        console.log("[OmniParser] Analysis error:", message.error);
        this.showLoading(false);
        this.showError(message.error);
        break;
    }
  }

  requestAnalysis() {
    if (this.isAnalyzing || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.clearCanvas();
    this.ws.send(
      JSON.stringify({
        type: "analyze_request",
      })
    );
  }

  drawDetections(detections) {
    this.lastDetections = detections; // Store detections for redrawing
    const ctx = this.canvas.getContext("2d");
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Get the dimensions of the source image - we know these are fixed
    const sourceWidth = 1024;
    const sourceHeight = 768;

    // Use the stored display information
    const { displayedWidth, displayedHeight, marginLeft, marginTop } =
      this.imageDisplayInfo;
    console.log("[OmniParser] Drawing with display info:", {
      displayedWidth,
      displayedHeight,
      marginLeft,
      marginTop,
      canvasWidth: this.canvas.width,
      canvasHeight: this.canvas.height,
    });

    // Calculate scale factors based on the actual displayed image size
    const scaleX = displayedWidth / sourceWidth;
    const scaleY = displayedHeight / sourceHeight;
    console.log("[OmniParser] Scale factors:", { scaleX, scaleY });

    if (detections.length === 0) return;

    // Process all detections
    detections.forEach((detection, index) => {
      // Skip all but first detection if showFirstLabelOnly is true
      if (this.showFirstLabelOnly && index > 0) return;

      const [x1, y1, x2, y2] = detection.coordinates;
      const confidence = detection.confidence;
      const label = `${detection.class} (${(confidence * 100).toFixed(1)}%)`;

      // Scale coordinates and apply margins
      const scaledX1 = x1 * scaleX + marginLeft;
      const scaledY1 = y1 * scaleY + marginTop;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      console.log(`[OmniParser] Drawing detection ${index}:`, {
        original: { x1, y1, x2, y2 },
        scaled: { x: scaledX1, y: scaledY1, width, height },
        label,
      });

      ctx.lineWidth = 2;
      ctx.font = "14px Arial";

      // Draw box using width and height
      ctx.strokeStyle = `rgba(255, 0, 0, ${confidence})`;
      ctx.strokeRect(scaledX1, scaledY1, width, height);

      // Draw label background
      ctx.fillStyle = `rgba(255, 0, 0, ${confidence * 0.7})`;
      const textWidth = ctx.measureText(label).width;
      ctx.fillRect(scaledX1, scaledY1 - 20, textWidth + 4, 20);

      // Draw label text
      ctx.fillStyle = "white";
      ctx.fillText(label, scaledX1 + 2, scaledY1 - 5);
    });
  }

  clearCanvas() {
    const ctx = this.canvas.getContext("2d");
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  showLoading(show) {
    this.isAnalyzing = show;
    this.loadingIndicator.style.display = show ? "block" : "none";
    this.analyzeButton.disabled = show;
  }

  showError(message) {
    // Could implement error display in UI if desired
  }
}

// Initialize the demo when the page loads
document.addEventListener("DOMContentLoaded", () => {
  const demoContainer = document.getElementById("omniparser-demo");
  if (!demoContainer) return;

  // Initialize OmniParser demo
  const demo = new OmniParserDemo("omniparser-demo");

  // Add error message display
  const errorDisplay = document.createElement("div");
  errorDisplay.className = "error-message";
  errorDisplay.style.display = "none";
  demoContainer.appendChild(errorDisplay);

  // Update showError method
  demo.showError = (message) => {
    errorDisplay.textContent = message;
    errorDisplay.style.display = "block";
    setTimeout(() => {
      errorDisplay.style.display = "none";
    }, 5000);
  };

  // Clean up on page unload
  window.addEventListener("beforeunload", () => {
    if (demo.ws) {
      demo.ws.close();
    }
  });
});
