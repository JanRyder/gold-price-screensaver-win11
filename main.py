import sys
import requests
import time
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, 
    QWidget, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QPropertyAnimation, 
    QEasingCurve, QPoint, QSize, QParallelAnimationGroup, QSequentialAnimationGroup,
    QRect, Property
)
from PySide6.QtGui import QFont, QColor, QMouseEvent, QKeyEvent, QScreen, QPainter, QPen, QPainterPath

# API URL for Gold Price
API_URL = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"

# Enable High DPI scaling
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class RollingDigit(QWidget):
    """A single digit that rolls up/down."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 160)
        self._current_digit = "0"
        self._target_digit = "0"
        self._offset = 0
        self.font = QFont("Segoe UI Variable Display", 100, QFont.Weight.Bold)

    def set_digit(self, digit: str):
        if self._current_digit == digit:
            return
        self._target_digit = digit
        self.animate_roll()

    def animate_roll(self):
        self.anim = QPropertyAnimation(self, b"offset")
        self.anim.setDuration(800)
        self.anim.setStartValue(0)
        self.anim.setEndValue(160)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuart)
        self.anim.finished.connect(self._on_anim_finished)
        self.anim.start()

    def _on_anim_finished(self):
        self._current_digit = self._target_digit
        self._offset = 0
        self.update()

    @Property(int)
    def offset(self): return self._offset
    @offset.setter
    def offset(self, value):
        self._offset = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font)
        painter.setPen(QColor("#FFFFFF"))

        # Draw current digit (moving out)
        painter.drawText(self.rect().translated(0, self._offset), Qt.AlignmentFlag.AlignCenter, self._current_digit)
        # Draw target digit (moving in)
        painter.drawText(self.rect().translated(0, self._offset - 160), Qt.AlignmentFlag.AlignCenter, self._target_digit)

class RollingNumberLabel(QWidget):
    """A row of RollingDigits to display a full price."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.digits = []
        self._last_text = ""

    def set_text(self, text: str):
        if text == self._last_text:
            return
        
        # Clean existing widgets if structure changes (e.g., price length change)
        if len(text) != len(self._last_text):
            for i in reversed(range(self.layout.count())): 
                self.layout.itemAt(i).widget().setParent(None)
            self.digits = []
            for char in text:
                if char.isdigit():
                    d = RollingDigit()
                    self.layout.addWidget(d)
                    self.digits.append(d)
                else:
                    lbl = QLabel(char)
                    lbl.setStyleSheet("color: white; font-size: 100px; font-weight: bold; font-family: 'Segoe UI Variable Display';")
                    self.layout.addWidget(lbl)
                    self.digits.append(lbl)
        
        # Update digits
        digit_idx = 0
        for i, char in enumerate(text):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, RollingDigit):
                widget.set_digit(char)
        
        self._last_text = text

class TrendChart(QWidget):
    """A simple line chart to show price trends."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.prices = []
        self.max_points = 50

    def add_price(self, price: float):
        self.prices.append(price)
        if len(self.prices) > self.max_points:
            self.prices.pop(0)
        self.update()

    def paintEvent(self, event):
        if len(self.prices) < 2:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        min_p, max_p = min(self.prices), max(self.prices)
        if min_p == max_p:
            min_p -= 1
            max_p += 1
            
        def get_y(p): return h - 20 - (p - min_p) / (max_p - min_p) * (h - 40)
        def get_x(i): return 20 + i * (w - 40) / (len(self.prices) - 1)

        path = QPainterPath()
        path.moveTo(get_x(0), get_y(self.prices[0]))
        for i in range(1, len(self.prices)):
            path.lineTo(get_x(i), get_y(self.prices[i]))

        # Draw line
        pen = QPen(QColor("#3b82f6"), 3)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Draw gradient fill
        fill_path = QPainterPath(path)
        fill_path.lineTo(get_x(len(self.prices)-1), h)
        fill_path.lineTo(get_x(0), h)
        fill_path.closeSubpath()
        
        from PySide6.QtGui import QLinearGradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(59, 130, 246, 100))
        grad.setColorAt(1, QColor(59, 130, 246, 0))
        painter.fillPath(fill_path, grad)

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
        self.central_widget.setStyleSheet("background-color: #000000;") # Pure black for OLED
        
        # Main Layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(100, 100, 100, 100)
        self.main_layout.setSpacing(0)
        
        # Top: Title
        self.title_label = QLabel("京东金融 · 实时金价")
        self.title_label.setStyleSheet("color: #666666; font-size: 28px; font-weight: 400; font-family: 'Segoe UI Variable Display', sans-serif;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addWidget(self.title_label)
        
        # Middle: Rolling Number
        self.rolling_label = RollingNumberLabel()
        self.main_layout.addWidget(self.rolling_label)
        
        # Middle: Change info
        self.info_layout = QHBoxLayout()
        self.change_label = QLabel("正在同步数据...")
        self.change_label.setStyleSheet("color: #444444; font-size: 40px; font-weight: 500;")
        self.info_layout.addWidget(self.change_label)
        self.info_layout.addStretch()
        self.main_layout.addLayout(self.info_layout)
        
        self.main_layout.addSpacing(40)
        
        # Bottom: Trend Chart
        self.trend_chart = TrendChart()
        self.main_layout.addWidget(self.trend_chart)
        
        self.main_layout.addStretch()
        
        # Bottom Footer
        self.footer_layout = QHBoxLayout()
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #333333; font-size: 18px;")
        
        self.disclaimer_label = QLabel("数据来源：京东金融。仅供参考，不构成投资建议。")
        self.disclaimer_label.setStyleSheet("color: #222222; font-size: 14px;")
        
        self.footer_layout.addWidget(self.time_label)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.disclaimer_label)
        self.main_layout.addLayout(self.footer_layout)

    def start_drift_animation(self) -> None:
        """Extremely subtle drift to prevent burn-in without being noticeable."""
        self.drift_group = QSequentialAnimationGroup()
        # Only move a few pixels very slowly
        for pos in [QPoint(2, 2), QPoint(-2, 2), QPoint(-2, -2), QPoint(2, -2)]:
            anim = QPropertyAnimation(self, b"window_offset")
            anim.setDuration(60000) # 1 minute per move
            anim.setEndValue(pos)
            self.drift_group.addAnimation(anim)
        self.drift_group.setLoopCount(-1)
        self.drift_group.start()

    @Property(QPoint)
    def window_offset(self): return self.central_widget.pos()
    @window_offset.setter
    def window_offset(self, pos): self.central_widget.move(pos)

    def update_price(self, data: Dict[str, Any]) -> None:
        """Update the UI with rolling number and trend chart."""
        price_str = data.get("price", "0.00")
        price_val = float(price_str)
        
        # Update Rolling Label
        self.rolling_label.set_text(price_str)
        
        # Update Trend Chart
        self.trend_chart.add_price(price_val)
        
        # Update Change Info
        rate = data.get("upAndDownRate", "+0.00%")
        amt = data.get("upAndDownAmt", "+0.00")
        is_up = "+" in rate
        color = "#FF3B30" if is_up else "#34C759"
        indicator = "↑" if is_up else "↓"
        
        self.change_label.setText(f"{indicator} {rate}  {amt}")
        self.change_label.setStyleSheet(f"color: {color}; font-size: 40px; font-weight: 600;")
        self.time_label.setText(f"最后同步: {time.strftime('%H:%M:%S')}")

    def handle_error(self, error_msg: str) -> None:
        self.change_label.setText("网络连接中...")
        self.change_label.setStyleSheet("color: #333333; font-size: 24px;")

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
