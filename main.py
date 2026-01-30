import sys
import requests
import time
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, 
    QWidget, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QPropertyAnimation, Property,
    QEasingCurve, QPoint, QRect, QSize, QParallelAnimationGroup, QSequentialAnimationGroup
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
            
            # Wait for 5 seconds in small increments
            for _ in range(50):
                if not self._running: break
                time.sleep(0.1)

class ScreenSaverWindow(QMainWindow):
    """The main fullscreen window for the screensaver."""
    
    def __init__(self, is_preview: bool = False) -> None:
        super().__init__()
        self.is_preview = is_preview
        self.last_mouse_pos: Optional[QPoint] = None
        self.start_time = time.time()
        
        # Configure window properties
        self.setWindowTitle("实时金价windows屏保")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        if not self.is_preview:
            self.showFullScreen()
            self.setCursor(Qt.CursorShape.BlankCursor)
        
        self.init_ui()
        
        # Start drift animation (Screen Burn-in Protection)
        if not self.is_preview:
            self.start_drift_animation()
        
        # Start worker thread
        self.worker = GoldPriceWorker()
        self.worker.data_received.connect(self.update_price)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()

    def init_ui(self) -> None:
        """Initialize a sleek UI with pure black background."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #000000;")
        
        # Main Container
        self.content_container = QWidget(self.central_widget)
        self.content_container.setFixedSize(1000, 600)
        self.content_container.move(
            (self.width() - 1000) // 2 if self.width() > 1000 else 0,
            (self.height() - 600) // 2 if self.height() > 600 else 0
        )
        
        self.container_layout = QVBoxLayout(self.content_container)
        self.container_layout.setContentsMargins(50, 50, 50, 50)
        self.container_layout.setSpacing(20)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        self.title_label = QLabel("京东金融 · 实时金价")
        self.title_label.setStyleSheet("color: #666666; font-size: 24px; font-weight: 400; font-family: 'Segoe UI Variable Display', sans-serif;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Price Label
        self.price_label = QLabel("--.--")
        self.price_label.setStyleSheet("color: #FFFFFF; font-size: 160px; font-weight: 700; font-family: 'Segoe UI Variable Display', sans-serif;")
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Opacity effect for fade animation
        self.price_opacity = QGraphicsOpacityEffect(self.price_label)
        self.price_label.setGraphicsEffect(self.price_opacity)
        self.price_opacity.setOpacity(1.0)
        
        # Change Info
        self.change_label = QLabel("正在同步...")
        self.change_label.setStyleSheet("color: #444444; font-size: 36px; font-weight: 500;")
        self.change_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Bottom Disclaimer
        self.bottom_info = QWidget()
        self.bottom_layout = QVBoxLayout(self.bottom_info)
        
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #333333; font-size: 16px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.disclaimer_label = QLabel("数据来源：京东金融。仅供参考，不构成投资建议。")
        self.disclaimer_label.setStyleSheet("color: #222222; font-size: 12px;")
        self.disclaimer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.bottom_layout.addWidget(self.time_label)
        self.bottom_layout.addWidget(self.disclaimer_label)
        
        self.container_layout.addWidget(self.title_label)
        self.container_layout.addStretch()
        self.container_layout.addWidget(self.price_label)
        self.container_layout.addWidget(self.change_label)
        self.container_layout.addStretch()
        self.container_layout.addWidget(self.bottom_info)

    def start_drift_animation(self) -> None:
        """Slow drifting animation to prevent screen burn-in."""
        screen_w = self.screen().size().width()
        screen_h = self.screen().size().height()
        
        center_x = (screen_w - self.content_container.width()) // 2
        center_y = (screen_h - self.content_container.height()) // 2
        offset = 50
        
        self.drift_group = QSequentialAnimationGroup()
        points = [
            QPoint(center_x - offset, center_y - offset),
            QPoint(center_x + offset, center_y - offset),
            QPoint(center_x + offset, center_y + offset),
            QPoint(center_x - offset, center_y + offset)
        ]
        
        for i in range(len(points)):
            anim = QPropertyAnimation(self.content_container, b"pos")
            anim.setDuration(40000) # Very slow
            anim.setStartValue(points[i])
            anim.setEndValue(points[(i + 1) % len(points)])
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.drift_group.addAnimation(anim)
            
        self.drift_group.setLoopCount(-1)
        self.drift_group.start()

    def update_price(self, data: Dict[str, Any]) -> None:
        """Update UI with fade animation."""
        price_str = f"¥{data.get('price', '0.00')}"
        if self.price_label.text() == price_str:
            return

        self.fade_anim = QSequentialAnimationGroup()
        
        fade_out = QPropertyAnimation(self.price_opacity, b"opacity")
        fade_out.setDuration(400)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        fade_in = QPropertyAnimation(self.price_opacity, b"opacity")
        fade_in.setDuration(600)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InBack)
        
        fade_out.finished.connect(lambda: self._apply_update(data))
        
        self.fade_anim.addAnimation(fade_out)
        self.fade_anim.addAnimation(fade_in)
        self.fade_anim.start()

    def _apply_update(self, data: Dict[str, Any]) -> None:
        price = data.get("price", "0.00")
        rate = data.get("upAndDownRate", "+0.00%")
        amt = data.get("upAndDownAmt", "+0.00")
        is_up = "+" in rate
        
        self.price_label.setText(f"¥{price}")
        color = "#FF3B30" if is_up else "#34C759"
        indicator = "↑" if is_up else "↓"
        self.change_label.setText(f"{indicator} {rate}  {amt}")
        self.change_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 600;")
        self.time_label.setText(f"Last Sync: {time.strftime('%H:%M:%S')}")

    def handle_error(self, error_msg: str) -> None:
        self.change_label.setText("Connecting...")

    def close_and_exit(self) -> None:
        """Safely exit."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(500)
        QApplication.instance().quit()
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
            if time.time() - self.start_time < 2.0: # Increased delay
                return
            current_pos = event.globalPosition().toPoint()
            if self.last_mouse_pos is None:
                self.last_mouse_pos = current_pos
                return
            if (current_pos - self.last_mouse_pos).manhattanLength() > 30: # Increased threshold
                self.close_and_exit()
        super().mouseMoveEvent(event)

def main():
    app = QApplication(sys.argv)
    args = sys.argv[1:]
    is_preview = any(arg.lower().startswith("/p") for arg in args)
    
    if any(arg.lower().startswith("/c") for arg in args):
        sys.exit(0)

    window = ScreenSaverWindow(is_preview=is_preview)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
