# 锐读 - 速读训练程序


> 一个专为阅读速度训练设计的Python桌面应用程序，支持智能分页、双模式阅读和答题功能。



## ✨ 主要特性

- **🚀 智能阅读训练**：逐行消隐和自动翻页两种训练模式
- **⚡ 速度控制**：可调节阅读速度（60-1200字符/分钟）
- **📊 实时反馈**：进度显示、剩余时间估算
- **🎯 答题功能**：支持选择题和简答题的阅读理解测试
- **🎨 个性化设置**：字体、颜色、背景可自定义
- **📱 现代化界面**：仪表板风格，直观易用

## 🔧 系统要求

- **Python**: 3.7+
- **操作系统**: Windows / macOS / Linux
- **依赖包**: tkinter (通常随Python自带)、Pillow

## 📥 快速安装

1. **克隆项目**
   ```bash
   git clone https://github.com/GZYZhy/Reading
   cd Reading
   ```

2. **自动安装依赖**
   ```bash
   python install.py
   ```

3. **启动程序**
   ```bash
   python start.py
   ```

## 🚀 快速开始

1. **选择文章文件夹**：点击"选择文件夹"，选择包含txt文章的目录
2. **选择文章**：在文章列表中双击或选中文章
3. **开始训练**：点击"开始速读训练"按钮
4. **控制阅读**：使用暂停、停止、重置等功能按钮

## 📄 文章格式支持

程序支持特定格式的txt文章文件，包含元数据和可选的答题功能：

```txt
[title:"文章标题"]
[author:"作者姓名"]
[date:"2024/01/15"]
[type:"文章类型"]
    文章正文内容...
    支持段落、缩进和空行...

[question]
<question1>
    <que>问题内容</que>
    <type>cho</type>
    <a>选项A</a>
    <b>选项B</b>
    <c>选项C</c>
    <d>选项D</d>
    <ans>a</ans>
    <explain>答案解析</explain>
</question1>
```

## 📁 项目结构

```
Reading/
├── main.py                 # 主程序入口
├── start.py               # 启动脚本（推荐）
├── install.py             # 依赖安装脚本
├── core/                  # 核心功能模块
│   ├── settings.py        # 设置管理
│   ├── article_parser.py  # 文章解析
│   └── reading_controller.py # 阅读控制
├── gui/                   # 图形界面模块
│   ├── main_window.py     # 主窗口
│   ├── reading_window.py  # 阅读窗口
│   ├── settings_window.py # 设置窗口
│   └── article_overview_window.py # 文章通览
├── sample_articles/       # 示例文章
└── ico.png               # 程序图标
```

## 📖 详细使用说明

详细的使用方法、文章格式规范和功能介绍请参考 [USAGE.md](USAGE.md)

## 📄 许可证

本项目基于 Apache License 2.0 开源许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

---

## 免责声明

本软件为独立开发的免费开源项目，与任何商业平台无关联。

功能设计灵感可能来源于公共领域概念，但代码实现均为原创。

如有疑问或更多建议，请提交Issue，我们会尽快处理。

**(c)2025 ZhangWeb GZYZhy - Reading Training - Apache License 2.0** 