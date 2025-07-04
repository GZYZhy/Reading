"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 关于窗口
"""
import tkinter as tk
from tkinter import ttk
import webbrowser
from typing import Optional
from core.settings import Settings

class AboutWindow:
    def __init__(self, parent, settings: Settings):
        self.parent = parent
        self.settings = settings
        self.window: Optional[tk.Toplevel] = None
        
        self.create_window()
    
    def create_window(self):
        """创建关于窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("关于 锐读")
        
        # 设置窗口图标
        try:
            self.window.iconbitmap("ico.png")
        except Exception:
            pass
        
        # 获取屏幕尺寸，设置为合适大小
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = 520  # 进一步减小窗口宽度
        window_height = 650  # 同时略微减小高度
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(bg='#f8f9fa')
        
        # 禁用全屏并允许调整窗口大小
        self.window.attributes('-fullscreen', False)
        self.window.resizable(True, True)
        self.window.minsize(500, 550)  # 调整最小尺寸
        
        # 创建主容器
        main_container = ttk.Frame(self.window)
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 创建可滚动的内容区域
        self.create_scrollable_content(main_container)
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def create_scrollable_content(self, parent):
        """创建可滚动的内容区域"""
        # Canvas和滚动条
        canvas = tk.Canvas(parent, highlightthickness=0, bg='#f8f9fa')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # 布局Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 在可滚动区域内创建内容
        self.create_content(scrollable_frame)
    
    def create_content(self, parent):
        """创建关于页面的具体内容"""
        
        # 标题区域
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x', pady=(0, 20))
        
        # 程序标题
        title_label = ttk.Label(title_frame, text="锐读 - 速读训练程序", 
                              font=('Microsoft YaHei', 24, 'bold'),
                              foreground='#2c3e50')
        title_label.pack(pady=(10, 5))
        
        # 版本信息
        version_label = ttk.Label(title_frame, text="Version 1.0.0", 
                                font=('Microsoft YaHei', 12),
                                foreground='#7f8c8d')
        version_label.pack(pady=(0, 5))
        
        # 副标题
        subtitle_label = ttk.Label(title_frame, 
                                 text="专为阅读速度训练设计的Python桌面应用程序",
                                 font=('Microsoft YaHei', 14),
                                 foreground='#34495e')
        subtitle_label.pack(pady=(0, 20))
        
        # 分隔线
        separator1 = ttk.Separator(parent, orient='horizontal')
        separator1.pack(fill='x', pady=(0, 20))
        
        # 主要特性
        features_frame = ttk.LabelFrame(parent, text="✨ 主要特性", padding=10)
        features_frame.pack(fill='x', pady=(0, 12))
        
        features_text = """🚀 智能阅读训练：逐行消隐和自动翻页两种训练模式
⚡ 速度控制：可调节阅读速度（60-1200字符/分钟）
📊 实时反馈：进度显示、剩余时间估算
🎯 答题功能：支持选择题和简答题的阅读理解测试
🎨 个性化设置：字体、颜色、背景可自定义
📱 现代化界面：仪表板风格，直观易用
🧠 智能分页：基于屏幕大小自动调整页面内容
📖 通览全文：随时查看完整文章内容"""
        
        features_label = ttk.Label(features_frame, text=features_text,
                                 font=('Microsoft YaHei', 11),
                                 justify='left')
        features_label.pack(anchor='w')
        
        # 快速开始
        quick_start_frame = ttk.LabelFrame(parent, text="🚀 快速开始", padding=10)
        quick_start_frame.pack(fill='x', pady=(0, 12))
        
        quick_start_text = """1. 选择文章文件夹：点击"选择文件夹"，选择包含txt文章的目录
2. 选择文章：在文章列表中双击或选中文章
3. 开始训练：点击"开始速读训练"按钮
4. 控制阅读：使用暂停、停止、重置等功能按钮
5. 答题测试：阅读完成后可进行理解测试（如有题目）"""
        
        quick_start_label = ttk.Label(quick_start_frame, text=quick_start_text,
                                    font=('Microsoft YaHei', 11),
                                    justify='left')
        quick_start_label.pack(anchor='w')
        
        # 文章格式说明
        format_frame = ttk.LabelFrame(parent, text="📄 支持的文章格式", padding=10)
        format_frame.pack(fill='x', pady=(0, 12))
        
        format_text = """程序支持特定格式的txt文章文件，包含元数据和可选的答题功能：

[title:"文章标题"]     [author:"作者姓名"]
[date:"2024/01/15"]   [type:"文章类型"]

    文章正文内容...
    支持段落、缩进和空行...

[question]  <!-- 可选：答题部分 -->
<question1>
    <que>问题内容</que>
    <type>cho</type>  <!-- cho=选择题, ans=简答题 -->
    <a>选项A</a>  <b>选项B</b>  <c>选项C</c>  <d>选项D</d>
    <ans>a</ans>
    <explain>答案解析</explain>
</question1>"""
        
        format_label = ttk.Label(format_frame, text=format_text,
                               font=('Consolas', 10),
                               justify='left')
        format_label.pack(anchor='w')
        
        # 系统要求
        requirements_frame = ttk.LabelFrame(parent, text="🔧 系统要求", padding=10)
        requirements_frame.pack(fill='x', pady=(0, 12))
        
        requirements_text = """• Python: 3.7+
• 操作系统: Windows / macOS / Linux  
• 依赖包: tkinter (通常随Python自带)、Pillow
• 内存: 建议512MB+
• 屏幕分辨率: 建议1024x768+"""
        
        requirements_label = ttk.Label(requirements_frame, text=requirements_text,
                                     font=('Microsoft YaHei', 11),
                                     justify='left')
        requirements_label.pack(anchor='w')
        
        # 项目信息
        project_frame = ttk.LabelFrame(parent, text="📁 项目信息", padding=10)
        project_frame.pack(fill='x', pady=(0, 12))
        
        # GitHub链接
        github_frame = ttk.Frame(project_frame)
        github_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(github_frame, text="GitHub项目地址:", 
                font=('Microsoft YaHei', 11, 'bold')).pack(side='left')
        
        github_link = ttk.Label(github_frame, text="https://github.com/GZYZhy/Reading",
                              font=('Microsoft YaHei', 11),
                              foreground='#3498db',
                              cursor='hand2')
        github_link.pack(side='left', padx=(10, 0))
        github_link.bind("<Button-1>", 
                        lambda e: webbrowser.open("https://github.com/GZYZhy/Reading"))
        
        # 开发者信息
        developer_frame = ttk.Frame(project_frame)
        developer_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(developer_frame, text="开发者:", 
                font=('Microsoft YaHei', 11, 'bold')).pack(side='left')
        ttk.Label(developer_frame, text="ZhangWeb GZYZhy",
                font=('Microsoft YaHei', 11)).pack(side='left', padx=(10, 0))
        
        # 许可证信息
        license_frame = ttk.Frame(project_frame)
        license_frame.pack(fill='x')
        
        ttk.Label(license_frame, text="开源许可证:", 
                font=('Microsoft YaHei', 11, 'bold')).pack(side='left')
        ttk.Label(license_frame, text="Apache License 2.0",
                font=('Microsoft YaHei', 11)).pack(side='left', padx=(10, 0))
        
        # 分隔线
        separator2 = ttk.Separator(parent, orient='horizontal')
        separator2.pack(fill='x', pady=15)
        
        # 免责声明
        disclaimer_frame = ttk.LabelFrame(parent, text="⚠️ 免责声明", padding=10)
        disclaimer_frame.pack(fill='x', pady=(0, 12))
        
        disclaimer_text = """本软件为独立开发的免费开源项目，与任何商业平台无关联。

功能设计灵感可能来源于公共领域概念，但代码实现均为原创。

软件仅供学习和个人使用，使用者需自行承担使用风险。

如有疑问或建议，请访问GitHub项目页面提交Issue。"""
        
        disclaimer_label = ttk.Label(disclaimer_frame, text=disclaimer_text,
                                   font=('Microsoft YaHei', 10),
                                   justify='left',
                                   foreground='#7f8c8d')
        disclaimer_label.pack(anchor='w')
        
        # 底部按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=15)
        
        # 关闭按钮
        close_button = ttk.Button(button_frame, text="关闭", 
                                command=self.close_window)
        close_button.pack(side='right')
        
        # 访问GitHub按钮
        github_button = ttk.Button(button_frame, text="访问GitHub", 
                                 command=lambda: webbrowser.open("https://github.com/GZYZhy/Reading"))
        github_button.pack(side='right', padx=(0, 10))
        
        # 版权信息
        copyright_label = ttk.Label(parent, 
                                  text="(c)2025 ZhangWeb GZYZhy - Reading Training - Apache License 2.0",
                                  font=('Microsoft YaHei', 9),
                                  foreground='#95a5a6')
        copyright_label.pack(pady=8)
    
    def close_window(self):
        """关闭窗口"""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def show(self):
        """显示窗口"""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
    
    def destroy(self):
        """销毁窗口"""
        self.close_window() 