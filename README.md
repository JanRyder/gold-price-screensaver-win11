# 实时金价windows屏保 (Win11 Style)

[English](#english) | [中文](#中文)

---

## 中文

一个美观的、基于 PySide6 开发的 Windows 11 风格实时金价显示屏幕保护程序。**数据来源于京东金融**。

### 🚀 快速下载
- **[点击下载 GoldPriceSaver.scr](https://github.com/JanRyder/gold-price-screensaver-win11/raw/main/GoldPriceSaver.scr)**
  > 下载后右键点击文件，选择“安装”即可使用。

### ✅ 彻底解决“(2) 进程”和“残存界面”的方案
如果你希望任务管理器中**只显示 1 个进程**，且完全避免退出时的残存黑框，请根据你的需求选择：

#### 方案 A：使用 Nuitka 编译（推荐：单文件 + 单进程）
Nuitka 是比 PyInstaller 更先进的工具，它将 Python 代码编译为真正的 C++ 可执行文件，不会像 PyInstaller 那样通过解压临时文件运行（这正是产生 2 个进程的原因）。
1. **安装 Nuitka**: `pip install -U nuitka`
2. **安装 C++ 编译器**: (如果提示需要，请按提示下载安装，或安装 [Visual Studio Community](https://visualstudio.microsoft.com/zh-hans/vs/community/))
3. **执行编译**:
   ```bash
   python -m nuitka --standalone --onefile --windows-disable-console --enable-plugin=pyside6 --output-filename=GoldPriceSaver.exe main.py
   ```
4. **效果**: 编译出的 `GoldPriceSaver.exe`（改名为 `.scr`）在任务管理器中**只显示 1 个进程**。

#### 方案 B：便携版（单进程）
如果你不想编译，请直接使用我们准备好的便携版：
- **[点击下载 GoldPriceSaver-portable.zip](https://github.com/JanRyder/gold-price-screensaver-win11/raw/main/GoldPriceSaver-portable.zip)**
  - 解压后运行 `Install-Screensaver.ps1`。这种方式也是单进程运行，且启动速度最快。

### ⚠️ 无法安装/打开的解决方法
如果你遇到“Windows 已保护你的电脑”或无法双击打开的情况，请尝试：
1. **解除锁定**：右键点击下载的 `GoldPriceSaver.scr` -> 属性 -> 勾选底部的“**解除锁定**” (Unblock) -> 确定。
2. **手动存放**：将文件复制到 `C:\Windows\System32` 目录下（需要管理员权限），然后在系统设置中选择它。
3. **SmartScreen**：如果弹出警告，点击“更多信息” -> “**仍要运行**”。
4. **测试运行**：你可以先将后缀名改回 `.exe` 双击测试是否能正常打开。如果可以打开，说明程序没问题，是系统权限阻止了屏保安装。

### ⚖️ 法律声明与免责条款
- **数据来源**：本程序数据来源于京东金融公开接口，仅供个人学习及参考之用。
- **准确性**：本程序不保证数据的实时性、准确性或完整性。数据可能存在延迟或偏差。
- **投资建议**：本程序展示的数据**不构成任何投资建议**。因使用本程序数据导致的任何投资损失，作者概不负责。
- **侵权声明**：本程序为开源项目，无意侵犯任何公司或个人的知识产权。如认为本项目内容存在侵权，请联系删除。
- **风险提示**：屏幕保护程序长时间运行请注意屏幕老化风险，本项目已内置防烧屏漂移逻辑，但不承担任何硬件损坏责任。

### 功能特点
- **实时更新**：每 5 秒从京东金融 API 获取一次最新的黄金价格。
- **丝滑滚动数字**：采用 iOS 风格的数字滚动动画，变化过程更自然。
- **动态趋势图**：实时绘制价格波动曲线，直观展现跌涨趋势。
- **极简设计**：纯黑背景配合高对比度文字，保护屏幕同时提升质感。
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

### ✅ Solve "(2) Processes" & "Residual UI" Issues
If you want **only 1 process** in Task Manager and want to avoid any residual black frames upon exit:

#### Option A: Use Nuitka (Recommended: Single-file + Single-process)
Nuitka compiles Python to a native C++ executable, avoiding the "bootloader + extraction" architecture of PyInstaller (which causes the 2-process issue).
1. **Install Nuitka**: `pip install -U nuitka`
2. **Build**:
   ```bash
   python -m nuitka --standalone --onefile --windows-disable-console --enable-plugin=pyside6 --output-filename=GoldPriceSaver.exe main.py
   ```

#### Option B: Portable Version (Single-process)
If you prefer not to compile, use the portable build:
- **[Download GoldPriceSaver-portable.zip](https://github.com/JanRyder/gold-price-screensaver-win11/raw/main/GoldPriceSaver-portable.zip)**
  - Unzip and run `Install-Screensaver.ps1`.

### ⚖️ Legal Disclaimer
- **Data Source**: Data is fetched from JD Finance public API. For educational and personal use only.
- **Accuracy**: No guarantee of real-time accuracy or completeness. Data may be delayed.
- **Investment Advice**: This software does **NOT** provide financial or investment advice. The author is not responsible for any financial loss.
- **Copyright**: This is an open-source project. If you believe any content infringes on your rights, please contact for removal.
- **Risk Warning**: Use at your own risk. Built-in drift logic is provided for screen protection, but the author is not liable for any hardware issues.

### Features
- **Real-time Updates**: Fetches the latest gold price from JD Finance API every 5 seconds.
- **Smooth Rolling Numbers**: iOS-style rolling digit animations for a more natural feel.
- **Dynamic Trend Chart**: Real-time price fluctuation curve to visualize trends.
- **Minimalist Design**: Pure black background with high contrast text for quality and protection.
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
