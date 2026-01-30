import sys
import os
import requests
import time
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
    QWidget, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QMessageBox
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QPropertyAnimation, 
    QEasingCurve, QPoint, QPointF, QSize, QParallelAnimationGroup, QSequentialAnimationGroup,
    Property, QRect
)
from PySide6.QtGui import (
    QFont, QColor, QMouseEvent, QKeyEvent, QScreen, 
    QPainter, QPen, QPainterPath, QLinearGradient, QGradient, QCursor
)

# API URL for Gold Price
API_URL = "https://api.jdjygold.com/gw2/generic/jrm/h5/m/stdLatestPrice?productSku=1961543816"

# Enable High DPI scaling
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

class RollingDigit(QWidget):
    """A single digit that rolls up/down like an odometer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0 # Odometer-like position
        self._target_value = 0.0
        self.setFixedWidth(80) 
        self.setFixedHeight(160)
        self.anim = QPropertyAnimation(self, b"value_prop")
        self.anim.setDuration(1200) # Slower for more smoothness
        self.anim.setEasingCurve(QEasingCurve.Type.OutExpo)

    @Property(float)
    def value_prop(self): return self._value
    @value_prop.setter
    def value_prop(self, val):
        self._value = val
        self.update()

    def setDigit(self, digit: str):
        if not digit.isdigit(): return
        target = float(digit)
        
        # Calculate the shortest path for the rolling effect
        # We allow the internal _value to grow/shrink indefinitely to keep it smooth
        current_base = int(self._value) // 10 * 10
        target_abs = current_base + target
        
        # Adjust target to minimize distance from current _value
        while target_abs - self._value > 5: target_abs -= 10
        while target_abs - self._value < -5: target_abs += 10
        
        if abs(target_abs - self._value) < 0.01: return

        self.anim.stop()
        self.anim.setStartValue(self._value)
        self.anim.setEndValue(target_abs)
        self.anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont("'Segoe UI Variable Display', 'Inter'", 90, QFont.Weight.Bold))
        painter.setPen(QColor("#FFFFFF"))
        
        h = self.height()
        # Draw digits around the current floating _value
        for i in range(-2, 3):
            val_to_draw = int(self._value + i + 0.5)
            digit = val_to_draw % 10
            y_pos = h/2 + (val_to_draw - self._value) * h
            rect = QRect(0, int(y_pos - h/2), self.width(), h)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(digit))

class RollingNumber(QWidget):
    """A widget composed of multiple rolling digits."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(2) # Add small spacing between digits
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.digits = []
        self._value = ""

    def setValue(self, value: str):
        if value == self._value: return
        
        # Sync digits
        if len(self.digits) != len(value):
            # Clear and rebuild to avoid layout issues
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            self.digits = []
            
            for char in value:
                if char in ".¥":
                    lbl = QLabel(char)
                    lbl.setStyleSheet("color: white; font-size: 80px; font-weight: bold;")
                    lbl.setFixedWidth(45)
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.layout.addWidget(lbl)
                    self.digits.append(lbl)
                else:
                    d = RollingDigit()
                    self.layout.addWidget(d)
                    self.digits.append(d)
        
        for i, char in enumerate(value):
            if isinstance(self.digits[i], RollingDigit) and char.isdigit():
                self.digits[i].setDigit(char)
            elif isinstance(self.digits[i], QLabel):
                self.digits[i].setText(char)
        self._value = value

class TrendChart(QWidget):
    """A smooth line chart for price history."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self._prev_series = []
        self._target_series = []
        self._t = 1.0
        self._series_anim = QPropertyAnimation(self, b"anim_t")
        self._series_anim.setDuration(900)
        self._series_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setMinimumHeight(200)

    @Property(float)
    def anim_t(self):
        return self._t

    @anim_t.setter
    def anim_t(self, value: float):
        self._t = value
        self.update()

    def addData(self, price: float):
        if not self.history:
            self.history = [price]
            self._prev_series = [price]
            self._target_series = [price]
            self._t = 1.0
            self.update()
            return

        current_series = self._target_series if self._target_series else self.history
        self._prev_series = list(current_series)

        self.history.append(price)
        if len(self.history) > 100: self.history.pop(0)
        self._target_series = list(self.history)

        if len(self._prev_series) < len(self._target_series):
            pad = [self._prev_series[0]] * (len(self._target_series) - len(self._prev_series))
            self._prev_series = pad + self._prev_series
        elif len(self._prev_series) > len(self._target_series):
            self._prev_series = self._prev_series[-len(self._target_series):]

        self._series_anim.stop()
        self._t = 0.0
        self._series_anim.setStartValue(0.0)
        self._series_anim.setEndValue(1.0)
        self._series_anim.start()
        self.update()

    def paintEvent(self, event):
        if len(self.history) < 2:
            return

        if self._target_series and self._prev_series and self._t < 1.0:
            series = [a + (b - a) * self._t for a, b in zip(self._prev_series, self._target_series)]
        else:
            series = self.history

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        min_p, max_p = min(series), max(series)
        p_range = max_p - min_p if max_p != min_p else 1.0
        
        # Add padding
        min_p -= p_range * 0.1
        max_p += p_range * 0.1
        p_range = max_p - min_p

        path = QPainterPath()
        gradient = QLinearGradient(0, 0, 0, h)
        
        # Set color based on overall trend
        is_up = self.history[-1] >= self.history[0]
        color = QColor("#FF3B30") if is_up else QColor("#34C759")
        
        pen = QPen(color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        for i, p in enumerate(series):
            x = i * (w / (len(series) - 1))
            y = h - ((p - min_p) / p_range) * h
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)

        painter.drawPath(path)
        
        # Fill area under path
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()
        
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 60))
        gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
        painter.fillPath(fill_path, gradient)

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
    
    def __init__(self, is_preview: bool = False, run_worker: bool = True) -> None:
        super().__init__()
        self.is_preview = is_preview
        self.run_worker = run_worker
        self.last_mouse_pos: Optional[QPoint] = None
        self._cursor_last_pos: Optional[QPoint] = None
        self._exiting = False
        
        # Configure window properties
        self.setWindowTitle("实时金价windows屏保")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        
        if not self.is_preview:
            self.showFullScreen()
            self.setCursor(Qt.CursorShape.BlankCursor)
        
        self.init_ui()

        self.setMouseTracking(True)
        self.central_widget.setMouseTracking(True)
        for w in (self.price_widget, self.chart):
            w.setMouseTracking(True)

        if not self.is_preview:
            self._cursor_timer = QTimer(self)
            self._cursor_timer.setInterval(50)
            self._cursor_timer.timeout.connect(self._poll_cursor)
            self._cursor_timer.start()
        
        # Only start worker thread on the main window to save resources and avoid exit issues
        if self.run_worker:
            self.worker = GoldPriceWorker()
            self.worker.data_received.connect(self.update_price)
            self.worker.error_occurred.connect(self.handle_error)
            self.worker.start()
        else:
            self.change_label.setText("同步中...")

    def init_ui(self) -> None:
        """Initialize a sleek iOS-like UI with pure black background."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #000000;")
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(100, 100, 100, 100)
        self.main_layout.setSpacing(40)
        
        # Header: Title and Time
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("京东金融 · 实时金价")
        self.title_label.setStyleSheet("color: #666666; font-size: 28px; font-weight: 500;")
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #444444; font-size: 24px;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.time_label)
        
        # Price Area
        self.price_widget = RollingNumber()
        
        # Trend Chart
        self.chart = TrendChart()
        
        # Change & Info
        self.info_layout = QHBoxLayout()
        self.change_label = QLabel("正在同步数据...")
        self.change_label.setStyleSheet("color: #444444; font-size: 36px; font-weight: 600;")
        self.disclaimer_label = QLabel("数据仅供参考，不构成投资建议。")
        self.disclaimer_label.setStyleSheet("color: #222222; font-size: 14px;")
        self.info_layout.addWidget(self.change_label)
        self.info_layout.addStretch()
        self.info_layout.addWidget(self.disclaimer_label, alignment=Qt.AlignmentFlag.AlignBottom)
        
        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.price_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.chart)
        self.main_layout.addLayout(self.info_layout)

    def update_price(self, data: Dict[str, Any]) -> None:
        """Update the UI with rolling numbers and chart."""
        price_str = data.get("price", "0.00")
        price_val = float(price_str)
        
        # Update rolling number
        self.price_widget.setValue(f"¥{price_str}")
        
        # Update chart
        self.chart.addData(price_val)
        
        # Update change info
        rate = data.get("upAndDownRate", "+0.00%")
        amt = data.get("upAndDownAmt", "+0.00")
        is_up = "+" in rate
        color = "#FF3B30" if is_up else "#34C759"
        indicator = "↑" if is_up else "↓"
        
        self.change_label.setText(f"{indicator} {rate}  {amt}")
        self.change_label.setStyleSheet(f"color: {color}; font-size: 36px; font-weight: 600;")
        self.time_label.setText(time.strftime('%H:%M:%S'))

    def handle_error(self, error_msg: str) -> None:
        self.change_label.setText("数据同步中...")
        self.change_label.setStyleSheet("color: #333333; font-size: 24px;")

    def _poll_cursor(self) -> None:
        if self.is_preview or self._exiting:
            return
        pos = QCursor.pos()
        if self._cursor_last_pos is None:
            self._cursor_last_pos = pos
            return
        if pos != self._cursor_last_pos:
            self.close_and_exit()

    def close_and_exit(self) -> None:
        """Safely stop all worker threads and force terminate the process."""
        if self._exiting:
            return
        self._exiting = True

        # 1. Stop all timers and hide ALL windows immediately
        if hasattr(self, "_cursor_timer"):
            self._cursor_timer.stop()
            
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QWidget):
                widget.hide()
                widget.close()
        
        # 2. Process events to ensure windows are removed from screen
        QApplication.processEvents()

        # 3. Stop worker thread
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(300)

        # 4. Final aggressive exit
        # Using os._exit(0) to bypass any PySide cleanup hangs
        os._exit(0)

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
            # Capture initial position to avoid exit on first fake move event
            current_pos = event.globalPosition().toPoint()
            if self.last_mouse_pos is None:
                self.last_mouse_pos = current_pos
                return
            
            # Exit on any intentional movement (>2 pixels)
            if (current_pos - self.last_mouse_pos).manhattanLength() > 2:
                self.close_and_exit()
        super().mouseMoveEvent(event)

def main():
    # Recommended for frozen executables
    import multiprocessing
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    
    # Handle Windows Screen Saver arguments
    # /s: Start the screensaver (Full screen)
    # /p: Preview in the screen saver selection dialog
    # /c: Configure
    
    args = sys.argv[1:]
    mode = "run" # default
    
    if args:
        arg = args[0].lower()
        if arg.startswith("/p"): mode = "preview"
        elif arg.startswith("/c"): mode = "config"
        elif arg.startswith("/s"): mode = "saver"

    if mode == "config":
        QMessageBox.information(None, "设置", "实时金价屏保目前无需额外配置。\n数据每 5 秒自动同步自京东金融。")
        sys.exit(0)

    if mode == "preview":
        # In a real preview, we should embed into the passed HWND.
        # For now, just show a small window to avoid crashing.
        window = ScreenSaverWindow(is_preview=True)
        window.setFixedSize(400, 300)
        window.show()
        sys.exit(app.exec())

    # Multi-monitor support for 'saver' or 'run' mode
    screens = app.screens()
    windows = []
    
    for i, screen in enumerate(screens):
        is_main = (i == 0)
        # Only the first window runs the background worker
        win = ScreenSaverWindow(is_preview=False, run_worker=is_main)
        
        # Position the window on the specific screen
        geom = screen.geometry()
        win.setGeometry(geom)
        
        if not is_main:
            # Secondary screens can show a simple black screen or a mirrored view
            # For now, we'll just show the same UI but without its own API worker
            pass
            
        win.showFullScreen()
        windows.append(win)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
