# 实时金价windows屏保 (Win11 Style)

[English](#english) | [中文](#中文)

---

## 中文

一个美观的、基于 PySide6 开发的 Windows 11 风格实时金价显示屏幕保护程序。**数据来源于京东金融**。

### 🚀 快速下载
- **[点击下载 GoldPriceSaver.scr](https://github.com/JanRyder/gold-price-screensaver-win11/raw/main/GoldPriceSaver.scr)**
  > 下载后右键点击文件，选择“安装”即可使用。

### ⚖️ 法律声明与免责条款
- **数据来源**：本程序数据来源于京东金融公开接口，仅供个人学习及参考之用。
- **准确性**：本程序不保证数据的实时性、准确性或完整性。数据可能存在延迟或偏差。
- **投资建议**：本程序展示的数据**不构成任何投资建议**。因使用本程序数据导致的任何投资损失，作者概不负责。
- **侵权声明**：本程序为开源项目，无意侵犯任何公司或个人的知识产权。如认为本项目内容存在侵权，请联系删除。
- **风险提示**：屏幕保护程序长时间运行请注意屏幕老化风险，本项目已内置防烧屏漂移逻辑，但不承担任何硬件损坏责任。

### 功能特点
- **实时更新**：每 5 秒从京东金融 API 获取一次最新的黄金价格。
- **iOS 级动画**：采用平滑的淡入淡出效果处理价格波动。
- **防烧屏逻辑**：内置内容漂移算法，保护 OLED 屏幕免受烧屏困扰。
- **极简审美**：纯黑背景，极致对比度，适配 Windows 11 设计语言。
- **交互逻辑**：支持标准的屏保交互，移动鼠标或按键即可退出。

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

A beautiful, PySide6-based Windows 11 style real-time gold price screensaver. **Data provided by JD Finance**.

### 🚀 Direct Download
- **[Download GoldPriceSaver.scr](https://github.com/JanRyder/gold-price-screensaver-win11/raw/main/GoldPriceSaver.scr)**
  > After downloading, right-click the file and select "Install" to use.

### ⚖️ Legal Disclaimer
- **Data Source**: Data is fetched from JD Finance public API. For educational and personal use only.
- **Accuracy**: No guarantee of real-time accuracy or completeness. Data may be delayed.
- **Investment Advice**: This software does **NOT** provide financial or investment advice. The author is not responsible for any financial loss.
- **Copyright**: This is an open-source project. If you believe any content infringes on your rights, please contact for removal.
- **Risk Warning**: Use at your own risk. Built-in drift logic is provided for screen protection, but the author is not liable for any hardware issues.

### Features
- **Real-time Updates**: Fetches the latest gold price from JD Finance API every 5 seconds.
- **iOS-style Animation**: Smooth fade-in/out transitions for price fluctuations.
- **Anti-Burn-in Logic**: Built-in content drifting algorithm to protect OLED screens.
- **Minimalist Aesthetic**: Pure black background with high contrast, following Windows 11 design principles.
- **Interactive**: Standard screensaver behavior—exit on mouse movement or key press.

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
