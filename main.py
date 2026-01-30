import sys
import requests
import time
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QWidget, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QPropertyAnimation, 
    QEasingCurve, QPoint, QSize, QParallelAnimationGroup, QSequentialAnimationGroup,
    Property, QRect
)
from PySide6.QtGui import QFont, QColor, QMouseEvent, QKeyEvent, QScreen, QPainter, QPen, QLinearGradient, QPathResolver, QPainterPath

# API URL for Gold Price
API_URL = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"

# Enable High DPI scaling
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class RollingDigit(QWidget):
    """A single digit that rolls vertically."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._digit = "0"
        self._offset = 0.0
        self.setFixedSize(70, 160) # Matched to font size
        self.font = QFont("'Segoe UI Variable Display', 'Inter'", 110, QFont.Weight.Bold)

    def get_offset(self): return self._offset
    def set_offset(self, value):
        self._offset = value
        self.update()
    offset = Property(float, get_offset, set_offset)

    def setDigit(self, digit: str):
        if self._digit == digit: return
        
        target_offset = 1.0 if int(digit) > int(self._digit) or (self._digit=="9" and digit=="0") else -1.0
        
        self.anim = QPropertyAnimation(self, b"offset")
        self.anim.setDuration(800)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(target_offset)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuart)
        
        old_digit = self._digit
        self._digit = digit
        self._prev_digit = old_digit
        
        self.anim.finished.connect(lambda: self.set_offset(0.0))
        self.anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font)
        painter.setPen(QColor("#FFFFFF"))
        
        h = self.height()
        y_center = h / 2 + 40 # Adjustment for font baseline
        
        if self._offset == 0:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._digit)
        else:
            # Draw old digit moving out
            old_rect = QRect(0, -self._offset * h, self.width(), h)
            painter.setOpacity(1.0 - abs(self._offset))
            painter.drawText(old_rect, Qt.AlignmentFlag.AlignCenter, self._prev_digit)
            
            # Draw new digit moving in
            new_rect = QRect(0, h - self._offset * h if self._offset > 0 else -h - self._offset * h, self.width(), h)
            painter.setOpacity(abs(self._offset))
            painter.drawText(new_rect, Qt.AlignmentFlag.AlignCenter, self._digit)

class RollingNumber(QWidget):
    """A group of RollingDigits for the full price."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.digits = []
        self._current_val = ""

    def setValue(self, value: str):
        # Format: "¥123.45"
        if value == self._current_val: return
        self._current_val = value
        
        # Clear and rebuild if length changes or first time
        if len(value) != len(self.digits):
            for i in reversed(range(self.layout.count())):
                self.layout.itemAt(i).widget().setParent(None)
            self.digits = []
            for char in value:
                if char.isdigit():
                    d = RollingDigit()
                    self.digits.append(d)
                    self.layout.addWidget(d)
                else:
                    lbl = QLabel(char)
                    lbl.setStyleSheet("color: white; font-size: 110px; font-weight: bold;")
                    self.layout.addWidget(lbl)
                    self.digits.append(lbl)
        
        # Update digits
        for char, widget in zip(value, self.digits):
            if isinstance(widget, RollingDigit):
                widget.setDigit(char)

class TrendChart(QWidget):
    """A smooth sparkline chart."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.history = []
        self.color = QColor("#444444")

    def addValue(self, val: float, is_up: bool):
        self.history.append(val)
        if len(self.history) > 40: self.history.pop(0)
        self.color = QColor("#FF3B30") if is_up else QColor("#34C759")
        self.update()

    def paintEvent(self, event):
        if len(self.history) < 2: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        max_v = max(self.history)
        min_v = min(self.history)
        rng = max(max_v - min_v, 1.0)
        
        path = QPainterPath()
        for i, v in enumerate(self.history):
            x = (i / (len(self.history) - 1)) * w
            y = h - ((v - min_v) / rng) * (h - 20) - 10
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)
            
        # Draw gradient area
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()
        
        grad = QLinearGradient(0, 0, 0, h)
        c = QColor(self.color)
        c.setAlpha(40)
        grad.setColorAt(0, c)
        c.setAlpha(0)
        grad.setColorAt(1, c)
        painter.fillPath(fill_path, grad)
        
        # Draw line
        pen = QPen(self.color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)

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
        self.setWindowTitle("实时金价windows屏保")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.X11BypassWindowManagerHint)
        
        if not self.is_preview:
            self.showFullScreen()
            self.setCursor(Qt.CursorShape.BlankCursor)
        
        self.init_ui()
        
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
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Main Container
        self.content_container = QWidget()
        self.content_container.setFixedSize(1000, 700)
        self.container_layout = QVBoxLayout(self.content_container)
        self.container_layout.setContentsMargins(50, 50, 50, 50)
        self.container_layout.setSpacing(0)
        
        # Title
        self.title_label = QLabel("京东金融 · 实时金价")
        self.title_label.setStyleSheet("color: #666666; font-size: 24px; font-weight: 400; font-family: 'Segoe UI Variable Display', 'Inter';")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Rolling Price
        self.price_widget = RollingNumber()
        
        # Change Info
        self.change_label = QLabel("正在同步...")
        self.change_label.setStyleSheet("color: #444444; font-size: 36px; font-weight: 500;")
        self.change_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Trend Chart
        self.trend_chart = TrendChart()
        self.trend_chart.setFixedWidth(800)
        
        # Bottom Info
        self.bottom_info = QWidget()
        self.bottom_layout = QVBoxLayout(self.bottom_info)
        self.bottom_layout.setSpacing(5)
        
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #333333; font-size: 16px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.disclaimer_label = QLabel("数据仅供参考，不构成投资建议。")
        self.disclaimer_label.setStyleSheet("color: #222222; font-size: 12px;")
        self.disclaimer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.bottom_layout.addWidget(self.time_label)
        self.bottom_layout.addWidget(self.disclaimer_label)
        
        self.container_layout.addWidget(self.title_label)
        self.container_layout.addStretch(1)
        self.container_layout.addWidget(self.price_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addWidget(self.change_label)
        self.container_layout.addSpacing(40)
        self.container_layout.addWidget(self.trend_chart, alignment=Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addStretch(1)
        self.container_layout.addWidget(self.bottom_info)
        
        self.main_layout.addWidget(self.content_container)

    def update_price(self, data: Dict[str, Any]) -> None:
        """Update UI with rolling animation and trend chart."""
        price_str = data.get("price", "0.00")
        self.price_widget.setValue(f"¥{price_str}")
        
        rate = data.get("upAndDownRate", "+0.00%")
        amt = data.get("upAndDownAmt", "+0.00")
        
        is_up = "+" in rate
        color = "#FF3B30" if is_up else "#34C759"
        indicator = "↑" if is_up else "↓"
        
        self.change_label.setText(f"{indicator} {rate}  {amt}")
        self.change_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 600;")
        self.time_label.setText(f"Last Sync: {time.strftime('%H:%M:%S')}")
        
        # Update Trend Chart
        try:
            val = float(price_str.replace(",", ""))
            self.trend_chart.addValue(val, is_up)
        except: pass

    def handle_error(self, error_msg: str) -> None:
        self.change_label.setText("Connecting...")
        self.change_label.setStyleSheet("color: #333333; font-size: 24px;")

    def close_and_exit(self) -> None:
        """Safely stop worker and force immediate exit."""
        try:
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(500)
            self.hide() # Hide window immediately to avoid visual lag
            QApplication.processEvents()
            QApplication.quit()
        finally:
            import os
            os._exit(0) # Force kill process to prevent any residual windows

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
