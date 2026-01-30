import sys
import requests
import time
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, 
    QWidget, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QPropertyAnimation, 
    QEasingCurve, QPoint, QSize
)
from PySide6.QtGui import QFont, QColor, QMouseEvent, QKeyEvent, QScreen

# API URL for Gold Price
API_URL = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"

# Enable High DPI scaling
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class GoldPriceWorker(QThread):
    """Worker thread to fetch gold price data every 5 seconds."""
    data_received = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        while self._running:
            try:
                response = requests.get(API_URL, timeout=10)
                if not self._running: break
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and "resultData" in data:
                        self.data_received.emit(data["resultData"]["datas"])
                    else:
                        self.error_occurred.emit("API 返回数据格式错误")
                else:
                    self.error_occurred.emit(f"HTTP 错误: {response.status_code}")
            except Exception as e:
                if self._running:
                    self.error_occurred.emit(f"请求失败: {str(e)}")
            
            # Wait for 5 seconds in small increments to remain responsive to stop
            for _ in range(50):
                if not self._running: break
                time.sleep(0.1)

class ScreenSaverWindow(QMainWindow):
    """The main fullscreen window for the screensaver."""
    
    def __init__(self, is_preview: bool = False) -> None:
        super().__init__()
        self.is_preview = is_preview
        self.last_mouse_pos: Optional[QPoint] = None
        
        # Configure window properties
        self.setWindowTitle("实时金价屏保")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        if not self.is_preview:
            self.showFullScreen()
            self.setCursor(Qt.CursorShape.BlankCursor) # Hide cursor in full screen
        
        self.init_ui()
        
        # Start worker thread
        self.worker = GoldPriceWorker()
        self.worker.data_received.connect(self.update_price)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def init_ui(self) -> None:
        """Initialize a modern UI with dark theme."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #0f172a;") # Dark blue-black background
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Main Container for Content
        self.container = QFrame()
        self.container.setFixedSize(800, 500)
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.7);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Shadow effect for container
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(50, 50, 50, 50)
        self.container_layout.setSpacing(20)
        
        # Title
        self.title_label = QLabel("京东黄金 - 实时金价")
        self.title_label.setStyleSheet("color: #94a3b8; font-size: 24px; font-weight: 300;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Price Label
        self.price_label = QLabel("--.--")
        self.price_label.setStyleSheet("color: #f8fafc; font-size: 120px; font-weight: bold;")
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Change Info (Rate and Amount)
        self.change_label = QLabel("正在加载数据...")
        self.change_label.setStyleSheet("color: #64748b; font-size: 32px; font-weight: 500;")
        self.change_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Update Time
        self.time_label = QLabel(f"最后更新: {time.strftime('%H:%M:%S')}")
        self.time_label.setStyleSheet("color: #475569; font-size: 18px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.container_layout.addWidget(self.title_label)
        self.container_layout.addWidget(self.price_label)
        self.container_layout.addWidget(self.change_label)
        self.container_layout.addStretch()
        self.container_layout.addWidget(self.time_label)
        
        self.layout.addWidget(self.container)

    def update_price(self, data: Dict[str, Any]) -> None:
        """Update the UI with new gold price data."""
        price = data.get("price", "0.00")
        rate = data.get("upAndDownRate", "+0.00%")
        amt = data.get("upAndDownAmt", "+0.00")
        
        # Update price with animation? (Optional)
        self.price_label.setText(f"¥{price}")
        
        # Handle color based on change (In China, Red is UP, Green is DOWN)
        is_up = "+" in rate
        color = "#ef4444" if is_up else "#22c55e" # Red-500 or Green-500
        indicator = "▲" if is_up else "▼"
        
        self.change_label.setText(f"{indicator} {rate} ({amt})")
        self.change_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 500;")
        
        self.time_label.setText(f"最后更新: {time.strftime('%H:%M:%S')}")

    def handle_error(self, error_msg: str) -> None:
        """Log error or show in UI."""
        print(f"Error: {error_msg}")
        self.change_label.setText("数据连接异常")
        self.change_label.setStyleSheet("color: #94a3b8; font-size: 24px;")

    def close_and_exit(self) -> None:
        """Safely stop the worker thread and exit the application."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000) # Wait up to 1s
        QApplication.quit()
        # Force exit if quit() is not enough
        sys.exit(0)

    # --- Screen Saver Exit Triggers ---
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self.is_preview:
            self.close_and_exit()
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.is_preview:
            self.close_and_exit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.is_preview:
            # First mouse move might happen on window show
            current_pos = event.globalPosition().toPoint()
            if self.last_mouse_pos is None:
                self.last_mouse_pos = current_pos
            elif (current_pos - self.last_mouse_pos).manhattanLength() > 15:
                self.close_and_exit()
        super().mouseMoveEvent(event)

def main():
    app = QApplication(sys.argv)
    
    # Handle Windows Screen Saver arguments
    # /s: Start the screensaver
    # /p: Preview in the screen saver selection dialog (needs to handle window embedding, skipped for simplicity)
    # /c: Configure (not implemented)
    
    args = sys.argv[1:]
    is_preview = False
    
    if args:
        first_arg = args[0].lower()
        if first_arg.startswith("/p"):
            # Preview mode (usually followed by a window handle)
            is_preview = True
        elif first_arg.startswith("/c"):
            # Configure mode - we can just exit or show a message
            sys.exit(0)
        elif first_arg.startswith("/s"):
            # Normal start
            pass

    window = ScreenSaverWindow(is_preview=is_preview)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
