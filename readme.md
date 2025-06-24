# AquesTalkPy

[![Python Version](https://img.shields.io/badge/python-3.x%20(32--bit)-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AquesTalkPy 是一个针对日语语音合成引擎 **AquesTalk1** 和 **AquesTalk2** 的高级 Python 封装库和应用工具包。它不仅为开发者提供了简洁的编程接口，还内置了功能完善的图形界面(GUI)和Web API，方便各类用户直接使用。

## 版权与法律声明

> **重要**: 本项目**不包含**任何 AquesTalk 的核心库文件 (如 `.dll`, `.phont` 文件或字典)。
>
> * 用户必须拥有并提供**自己合法获取的 AquesTalk 相关文件**。
> * 本项目仅为官方 DLL 文件提供一个 Python ctypes 封装层，方便调用。
> * 所有与 AquesTalk 相关的商标和版权均归 [株式会社 A-quest](http://www.a-quest.com/products/aquestalk.html) 所有。
> * 请在遵守 AquesTalk 最终用户许可协议 (EULA) 的前提下使用本项目。

## 关键要求：必须使用32位Python

> **这是运行本项目的最重要前提！**
>
> AquesTalk 官方提供的 `.dll` 动态链接库是 **32位 (x86) 程序**。因此，您**必须**在 **32位 的 Python 环境**中运行本项目的所有脚本 (`ui.py`, `api.py` 等)。
>
> **在64位Python环境下，程序将因无法加载DLL而立即失败。**

## 项目特点

* **高级封装接口**: 提供简洁的 `AquesSynthesizer` 类，屏蔽了 AquesTalk1 和 AquesTalk2 底层调用的差异，方便开发者集成。
* **内置图形界面 (GUI)**: 提供一个基于 PyQt5 的完整桌面应用 (`ui.py`)，支持文本输入、参数实时调节、音色选择、预览和批量生成功能。
* **内置 Web API**: 提供一个基于 Flask 的网络服务 (`api.py`)，允许通过 HTTP 请求进行远程语音合成，便于系统集成。
* **中文直转日语语音**: 内置独特的转换模块 (`text_to_ja.py`)，可将中文文本自动转写为符合发音习惯的日语假名，再进行语音合成。

## 快速开始

### 1. 前提条件

* **32位 Python 环境** (已安装)。
* **AquesTalk 相关文件** (已按下方结构准备好)。

### 2. 目录结构

请务必按照以下结构组织你的文件，否则本工具包将无法找到所需组件：

```
AquesTalkPy/
├── aq_dic/              # AquesTalk 字典目录
│   └── ...
├── aqtk1/               # AquesTalk1 引擎和音色目录
│   ├── f1/              # 示例音色 f1 (目录名即为音色名)
│   │   └── AquesTalk.dll
│   └── (其他音色目录...)
├── aqtk2/               # AquesTalk2 引擎和音色目录
│   ├── phont/           # AquesTalk2 音色文件目录
│   │   ├── aq_yukkuri.phont
│   │   └── (其他音色目录...)
│   └── AquesTalk2.dll
├── AqKanji2Koe.dll      # 共享的汉字->假名转换库
├── main.py              # 核心封装库
├── ui.py                # 内置的 PyQt5 图形界面
├── api.py               # 内置的 Flask Web API
├── core_aq1.py          # AquesTalk1 底层 ctypes 封装
├── core_aq2.py          # AquesTalk2 底层 ctypes 封装
└── text_to_ja.py        # 中文->日语假名转换器
```

### 3. 安装依赖

确保您正在使用 **32位** 的 `pip`。

```bash
# requirements.txt

pip install -r requirements.txt
```

您也可以使用本项目内置的嵌入式python作为解释器

## 使用方法

### 方式一：运行图形界面 (GUI)

对于大多数用户，这是最推荐的使用方式。

```bash
# 再次提醒：请使用 32位 Python 运行
python ui.py
```

### 方式二：运行 Web API 服务

如果您需要在其他程序中调用语音合成功能，可以启动此服务。

```bash
# 再次提醒：请使用 32位 Python 运行
python api.py
```
API 将在 `http://0.0.0.0:5000` 上提供服务。

### 方式三：作为Python库进行开发

开发者可以将本项目的核心模块集成到自己的应用中。

```python
from main import AquesSynthesizer
from text_to_ja import ChineseToHiragana

# 确保文件结构正确
text = "你好, こんにちは"
ja_text = ChineseToHiragana().convert(text)

# 使用 with 语句确保资源被正确释放
try:
    with AquesSynthesizer(
        engine='aq2',
        voice='aq_yukkuri.phont',
        dll_base='.\\aqtk2',
        dic_dir='.\\aq_dic'
    ) as synth:
        wav_data = synth.synthesize(ja_text, speed=110, pitch=120, volume=100)
        with open('output.wav', 'wb') as f:
            f.write(wav_data)
        print("语音合成成功: output.wav")
except Exception as e:
    print(f"发生错误: {e}")

```

## 文件概览

* `core_aq1.py` / `core_aq2.py`: 底层的 ctypes 封装，直接与 DLL 进行交互。
* `main.py`: 核心模块，提供了统一的 `AquesSynthesizer` 类，这是开发者主要交互的接口。
* `text_to_ja.py`: 语言处理模块，负责将中文、英文、日文混合文本统一转换为日语假名。
* `ui.py`: 一个功能完整的桌面应用，为用户提供图形化的操作方式。
* `api.py`: 一个功能完整的Web API服务，为其他程序提供HTTP调用接口。

## 许可证

本项目采用 MIT 许可证。

## 致谢

* **[Aquestalk](http://www.a-quest.com/products/aquestalk.html)**: 感谢 A-quest 公司开发出如此优秀的语音合成引擎。