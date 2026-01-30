import sys
import requests
import time
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QWidget, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QPropertyAnimation, Property,
    QEasingCurve, QPoint, QRect, QSize, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtGui import QFont, QColor, QMouseEvent, QKeyEvent, QScreen, QPainter, QPen, QPainterPath, QLinearGradient

# API URL for Gold Price
API_URL = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"

# Enable High DPI scaling
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class RollingDigit(QWidget):
    """A single digit that rolls like an odometer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(85, 180)
        self._current_digit = "0"
        self._target_digit = "0"
        self._offset = 0
        self.font = QFont("'Segoe UI Variable Display', 'Inter', sans-serif", 130, QFont.Weight.Bold)
        
        self.anim = QPropertyAnimation(self, b"offset")
        self.anim.setDuration(800)
        self.anim.setEasingCurve(QEasingCurve.Type.OutExpo)

    def get_offset(self): return self._offset
    def set_offset(self, val):
        self._offset = val
        self.update()
    offset = Property(float, get_offset, set_offset)

    def setDigit(self, digit: str):
        if self._target_digit == digit: return
        self._current_digit = self._target_digit
        self._target_digit = digit
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font)
        painter.setPen(QColor("#FFFFFF"))
        
        h = self.height()
        # Draw current digit moving out
        painter.drawText(self.rect().translated(0, int(-self._offset * h)), Qt.AlignmentFlag.AlignCenter, self._current_digit)
        # Draw target digit moving in
        painter.drawText(self.rect().translated(0, int((1 - self._offset) * h)), Qt.AlignmentFlag.AlignCenter, self._target_digit)

class RollingNumber(QWidget):
    """A collection of RollingDigits for a full number."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.digits = []
        self._last_text = ""

    def setText(self, text: str):
        if text == self._last_text: return
        
        # Clean up or add widgets if length changed
        if len(text) != len(self.digits):
            for d in self.digits: d.deleteLater()
            self.digits = []
            for char in text:
                if char.isdigit():
                    d = RollingDigit(self)
                    self.digits.append(d)
                    self.layout.addWidget(d)
                else:
                    lbl = QLabel(char)
                    lbl.setStyleSheet("color: white; font-size: 130px; font-weight: bold;")
                    self.layout.addWidget(lbl)
                    self.digits.append(lbl) # Placeholder
        
        for i, char in enumerate(text):
            if isinstance(self.digits[i], RollingDigit) and char.isdigit():
                self.digits[i].setDigit(char)
            elif not char.isdigit():
                pass # Symbol stays same
        
        self._last_text = text

class TrendChart(QWidget):
    """A simple sparkline chart for price trends."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.history = []
        self.color = QColor("#444444")

    def addData(self, price: float, is_up: bool):
        self.history.append(price)
        if len(self.history) > 40: self.history.pop(0)
        self.color = QColor("#FF3B30") if is_up else QColor("#34C759")
        self.update()

    def paintEvent(self, event):
        if len(self.history) < 2: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        max_p, min_p = max(self.history), min(self.history)
        rng = (max_p - min_p) if max_p != min_p else 1
        
        path = QPainterPath()
        for i, p in enumerate(self.history):
            x = i * (w / (len(self.history) - 1))
            y = h - ((p - min_p) / rng * (h * 0.8) + h * 0.1)
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)
            
        pen = QPen(self.color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Gradient area
        grad_path = QPainterPath(path)
        grad_path.lineTo(w, h)
        grad_path.lineTo(0, h)
        grad_path.closeSubpath()
        
        gradient = QLinearGradient(0, 0, 0, h)
        c = QColor(self.color)
        c.setAlpha(40)
        gradient.setColorAt(0, c)
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillPath(grad_path, gradient)

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
        """Initialize a sleek iOS-like UI with pure black background."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #000000;") # Pure black
        
        # Main Container
        self.content_container = QWidget(self.central_widget)
        self.content_container.setFixedSize(1000, 750)
        self.content_container.move(
            (self.width() - 1000) // 2 if self.width() > 1000 else 0,
            (self.height() - 750) // 2 if self.height() > 750 else 0
        )
        
        self.container_layout = QVBoxLayout(self.content_container)
        self.container_layout.setContentsMargins(50, 50, 50, 50)
        self.container_layout.setSpacing(10)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        self.title_label = QLabel("京东金融 · 实时金价")
        self.title_label.setStyleSheet("color: #666666; font-size: 24px; font-weight: 400; font-family: 'Segoe UI Variable Display', sans-serif;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Price Rolling Number
        self.price_rolling = RollingNumber()
        self.price_rolling.setFixedHeight(200)
        
        # Trend Chart
        self.trend_chart = TrendChart()
        self.trend_chart.setFixedWidth(800)
        
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
        self.container_layout.addWidget(self.price_rolling, 0, Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addSpacing(20)
        self.container_layout.addWidget(self.trend_chart, 0, Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addSpacing(10)
        self.container_layout.addWidget(self.change_label)
        self.container_layout.addStretch()
        self.container_layout.addWidget(self.bottom_info)

    def start_drift_animation(self) -> None:
        """Slow drifting animation to prevent screen burn-in."""
        screen_w = self.screen().size().width()
        screen_h = self.screen().size().height()
        
        center_x = (screen_w - self.content_container.width()) // 2
        center_y = (screen_h - self.content_container.height()) // 2
        offset = 60
        
        self.drift_group = QSequentialAnimationGroup()
        points = [
            QPoint(center_x - offset, center_y - offset),
            QPoint(center_x + offset, center_y - offset),
            QPoint(center_x + offset, center_y + offset),
            QPoint(center_x - offset, center_y + offset)
        ]
        
        for i in range(len(points)):
            anim = QPropertyAnimation(self.content_container, b"pos")
            anim.setDuration(30000) # Very slow
            anim.setStartValue(points[i])
            anim.setEndValue(points[(i + 1) % len(points)])
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.drift_group.addAnimation(anim)
            
        self.drift_group.setLoopCount(-1)
        self.drift_group.start()

    def update_price(self, data: Dict[str, Any]) -> None:
        """Update UI with rolling numbers and chart."""
        price_str = data.get("price", "0.00")
        price_val = float(price_str)
        rate = data.get("upAndDownRate", "+0.00%")
        amt = data.get("upAndDownAmt", "+0.00")
        is_up = "+" in rate
        
        # Update Rolling Number
        self.price_rolling.setText(price_str)
        
        # Update Chart
        self.trend_chart.addData(price_val, is_up)
        
        # Update Change Label
        color = "#FF3B30" if is_up else "#34C759"
        indicator = "↑" if is_up else "↓"
        self.change_label.setText(f"{indicator} {rate}  {amt}")
        self.change_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 600;")
        self.time_label.setText(f"Last Sync: {time.strftime('%H:%M:%S')}")

    def handle_error(self, error_msg: str) -> None:
        self.change_label.setText("Connecting...")

    def close_and_exit(self) -> None:
        """Safely stop the worker thread and exit the application."""
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
            # Avoid exiting immediately on launch due to system-generated mouse events
            if time.time() - self.start_time < 1.0:
                return
                
            current_pos = event.globalPosition().toPoint()
            if self.last_mouse_pos is None:
                self.last_mouse_pos = current_pos
                return

            # Use a small threshold (10 pixels) to avoid micro-movements/vibrations
            if (current_pos - self.last_mouse_pos).manhattanLength() > 10:
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
