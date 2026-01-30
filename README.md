# Gold Price Screensaver (Win11 Style) | 实时金价屏保 (Win11 风格)

[English](#english) | [中文](#中文)

---

## 中文

一个美观的、基于 PySide6 开发的 Windows 11 风格实时金价显示屏幕保护程序。

### 功能特点
- **实时更新**：每 5 秒从京东 API 获取一次最新的黄金价格。
- **美观设计**：深色模式、圆角矩形、动态阴影，完美契合 Windows 11 审美。
- **全屏显示**：自动全屏，支持多显示器（以主屏幕为准）。
- **交互逻辑**：支持标准的屏保交互，移动鼠标或按键即可退出。
- **视觉反馈**：遵循金融惯例，上涨显示为红色，下跌显示为绿色。

### 安装与运行
1. **克隆仓库**：
   ```bash
   git clone https://github.com/your-username/gold-price-screensaver.git
   cd gold-price-screensaver
   ```
2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
3. **直接运行**：
   ```bash
   python main.py
   ```

### 打包为 Windows 屏保 (.scr)
1. **安装 PyInstaller**：
   ```bash
   pip install pyinstaller
   ```
2. **执行打包**：
   ```bash
   pyinstaller --noconsole --onefile --name "GoldPriceSaver" main.py
   ```
3. **转换为 .scr**：
   将 `dist/GoldPriceSaver.exe` 重命名为 `GoldPriceSaver.scr`。
4. **安装**：
   右键点击 `GoldPriceSaver.scr` 并选择“安装”。

---

## English

A beautiful, PySide6-based Windows 11 style real-time gold price screensaver.

### Features
- **Real-time Updates**: Fetches the latest gold price from JD API every 5 seconds.
- **Aesthetic Design**: Dark mode, rounded corners, and dynamic shadows that match the Windows 11 aesthetic.
- **Full Screen**: Automatically goes full screen on launch.
- **Interactive**: Standard screensaver behavior—exit on mouse movement or key press.
- **Visual Feedback**: Follows financial conventions (Red for UP, Green for DOWN).

### Installation & Usage
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/gold-price-screensaver.git
   cd gold-price-screensaver
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run directly**:
   ```bash
   python main.py
   ```

### Building as a Windows Screensaver (.scr)
1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```
2. **Build**:
   ```bash
   pyinstaller --noconsole --onefile --name "GoldPriceSaver" main.py
   ```
3. **Convert to .scr**:
   Rename `dist/GoldPriceSaver.exe` to `GoldPriceSaver.scr`.
4. **Install**:
   Right-click `GoldPriceSaver.scr` and select "Install".

---

## License
MIT License
