class OmniParserVisualizer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.canvas = document.createElement("canvas");
    this.ctx = this.canvas.getContext("2d");
    this.ws = null;
    this.isAnalyzing = false;

    // Set canvas properties
    this.canvas.style.position = "absolute";
    this.canvas.style.top = "0";
    this.canvas.style.left = "0";
    this.canvas.style.pointerEvents = "none";

    // Add canvas to container
    this.container.style.position = "relative";
    this.container.appendChild(this.canvas);

    // Initialize loading indicator
    this.loadingIndicator = document.createElement("div");
    this.loadingIndicator.className = "loading-indicator";
    this.loadingIndicator.innerHTML = `
            <div class="spinner"></div>
            <div class="loading-text">Analyzing...</div>
        `;
    this.loadingIndicator.style.display = "none";
    this.container.appendChild(this.loadingIndicator);

    // Bind methods
    this.handleResize = this.handleResize.bind(this);
    this.startAnalysis = this.startAnalysis.bind(this);
    this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);

    // Add resize listener
    window.addEventListener("resize", this.handleResize);
    this.handleResize();
  }

  initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    this.ws = new WebSocket(wsUrl);
    this.ws.onmessage = this.handleWebSocketMessage;
    this.ws.onclose = () => {
      console.log("WebSocket connection closed");
      setTimeout(() => this.initWebSocket(), 1000);
    };
  }

  handleWebSocketMessage(event) {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case "analysis_started":
        this.showLoading();
        break;

      case "analysis_complete":
        this.hideLoading();
        this.visualizeDetections(data.detections);
        break;

      case "analysis_error":
        this.hideLoading();
        this.showError(data.error);
        break;
    }
  }

  showLoading() {
    this.isAnalyzing = true;
    this.loadingIndicator.style.display = "flex";
  }

  hideLoading() {
    this.isAnalyzing = false;
    this.loadingIndicator.style.display = "none";
  }

  showError(message) {
    // TODO: Implement error display
    console.error("Analysis error:", message);
  }

  handleResize() {
    const rect = this.container.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
  }

  visualizeDetections(detections) {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    detections.forEach((detection) => {
      const [x1, y1, x2, y2] = detection.coordinates;
      const width = x2 - x1;
      const height = y2 - y1;

      // Draw bounding box
      this.ctx.strokeStyle = this.getClassColor(detection.class);
      this.ctx.lineWidth = 2;
      this.ctx.strokeRect(x1, y1, width, height);

      // Draw label
      this.ctx.fillStyle = this.getClassColor(detection.class);
      this.ctx.font = "12px Arial";
      const label = `${detection.class} ${Math.round(
        detection.confidence * 100
      )}%`;
      this.ctx.fillText(label, x1, y1 - 5);

      // Draw OCR text if available
      if (detection.text) {
        this.ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
        this.ctx.fillText(detection.text, x1, y2 + 15);
      }
    });
  }

  getClassColor(className) {
    // Define colors for different element types
    const colors = {
      button: "#FF6B6B",
      text: "#4ECDC4",
      image: "#45B7D1",
      icon: "#96CEB4",
      default: "#FFE66D",
    };
    return colors[className.toLowerCase()] || colors.default;
  }

  startAnalysis() {
    if (this.isAnalyzing || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.ws.send(
      JSON.stringify({
        type: "analyze_request",
      })
    );
  }

  destroy() {
    window.removeEventListener("resize", this.handleResize);
    if (this.ws) {
      this.ws.close();
    }
    this.container.removeChild(this.canvas);
    this.container.removeChild(this.loadingIndicator);
  }
}
