"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 设置窗口
"""
import tkinter as tk
from tkinter import ttk, colorchooser
from typing import Optional, Callable
from core.settings import Settings

class SettingsWindow:
    def __init__(self, parent, settings: Settings):
        self.parent = parent
        self.settings = settings
        self.window: Optional[tk.Toplevel] = None
        self.close_callback: Optional[Callable] = None
        
        # 设置变量
        self.font_size_var = tk.StringVar()
        self.line_spacing_var = tk.StringVar() 
        self.reading_speed_var = tk.StringVar()
        self.background_color_var = tk.StringVar()
        self.text_color_var = tk.StringVar()
        self.mode_var = tk.StringVar()
        self.high_performance_var = tk.BooleanVar()  # 高性能模式
        
        self.create_window()
        self.load_current_settings()
    
    def create_window(self):
        """创建设置窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("锐读 - 速读训练 - 设置")
        
        # 设置窗口图标
        try:
            self.window.iconbitmap("ico.png")
        except Exception:
            pass  # 如果图标文件不存在，忽略错误
        
        # 设置合适的窗口大小
        initial_width = 580
        initial_height = 500
        min_width = 550
        min_height = 450
        
        # 获取屏幕尺寸，让窗口居中显示
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - initial_width) // 2
        y = (screen_height - initial_height) // 2
        
        self.window.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
        self.window.minsize(min_width, min_height)
        self.window.configure(bg='#f0f0f0')
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 主容器
        main_container = ttk.Frame(self.window)
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 标题
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(title_frame, text="阅读设置", font=('Microsoft YaHei', 16, 'bold')).pack(anchor='w')
        
        # 创建可滚动的内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(content_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # 创建笔记本控件（选项卡）在可滚动区域内
        self.notebook = ttk.Notebook(self.scrollable_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 基本设置选项卡
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="基本设置")
        self.create_basic_settings(basic_frame)
        
        # 外观设置选项卡
        appearance_frame = ttk.Frame(self.notebook)
        self.notebook.add(appearance_frame, text="外观设置")
        self.create_appearance_settings(appearance_frame)
        
        # 固定在底部的按钮区域
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill='x', side='bottom')
        
        # 添加分隔线
        separator = ttk.Separator(button_frame, orient='horizontal')
        separator.pack(fill='x', pady=(0, 10))
        
        # 按钮容器
        button_container = ttk.Frame(button_frame)
        button_container.pack(fill='x')
        
        # 添加按钮样式配置
        style = ttk.Style()
        style.configure('Settings.TButton', font=('Microsoft YaHei', 10), padding=(12, 6))
        
        ttk.Button(button_container, text="确定", command=self.save_and_close, style='Settings.TButton').pack(side='right', padx=(8, 0))
        ttk.Button(button_container, text="取消", command=self.cancel_and_close, style='Settings.TButton').pack(side='right', padx=(8, 8))
        ttk.Button(button_container, text="应用", command=self.apply_settings, style='Settings.TButton').pack(side='right', padx=(8, 8))
        ttk.Button(button_container, text="重置", command=self.reset_to_defaults, style='Settings.TButton').pack(side='left')
    
    def create_basic_settings(self, parent):
        """创建基本设置"""
        # 字号设置
        font_frame = ttk.LabelFrame(parent, text="字号设置", padding=15)
        font_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(font_frame, text="字体大小:").pack(anchor='w')
        
        font_control_frame = ttk.Frame(font_frame)
        font_control_frame.pack(fill='x', pady=(5, 0))
        
        font_scale = ttk.Scale(
            font_control_frame, 
            from_=20, to=100, 
            orient='horizontal',
            variable=self.font_size_var,
            command=self.on_font_size_change
        )
        font_scale.pack(side='left', fill='x', expand=True)
        
        self.font_size_label = ttk.Label(font_control_frame, text="60")
        self.font_size_label.pack(side='right', padx=(10, 0))
        
        # 行间距设置
        spacing_frame = ttk.LabelFrame(parent, text="行间距设置", padding=15)
        spacing_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(spacing_frame, text="行间距:").pack(anchor='w')
        
        spacing_control_frame = ttk.Frame(spacing_frame)
        spacing_control_frame.pack(fill='x', pady=(5, 0))
        
        spacing_scale = ttk.Scale(
            spacing_control_frame,
            from_=1.0, to=3.0,
            orient='horizontal',
            variable=self.line_spacing_var,
            command=self.on_line_spacing_change
        )
        spacing_scale.pack(side='left', fill='x', expand=True)
        
        self.spacing_label = ttk.Label(spacing_control_frame, text="1.5")
        self.spacing_label.pack(side='right', padx=(10, 0))
        
        # 阅读速度设置
        speed_frame = ttk.LabelFrame(parent, text="阅读速度设置", padding=15)
        speed_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(speed_frame, text="阅读速度 (字符/分钟):").pack(anchor='w')
        
        speed_control_frame = ttk.Frame(speed_frame)
        speed_control_frame.pack(fill='x', pady=(5, 0))
        
        speed_scale = ttk.Scale(
            speed_control_frame,
            from_=60, to=1200,
            orient='horizontal',
            variable=self.reading_speed_var,
            command=self.on_reading_speed_change
        )
        speed_scale.pack(side='left', fill='x', expand=True)
        
        self.speed_label = ttk.Label(speed_control_frame, text="300")
        self.speed_label.pack(side='right', padx=(10, 0))
        
        # 阅读模式
        mode_frame = ttk.LabelFrame(parent, text="阅读模式", padding=15)
        mode_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Radiobutton(mode_frame, text="逐行阅读", variable=self.mode_var, value='line').pack(anchor='w', pady=2)
        ttk.Radiobutton(mode_frame, text="按页阅读", variable=self.mode_var, value='page').pack(anchor='w', pady=2)
        
        # 高性能模式
        performance_frame = ttk.LabelFrame(parent, text="性能设置", padding=15)
        performance_frame.pack(fill='x')
        
        high_perf_checkbox = ttk.Checkbutton(
            performance_frame, 
            text="启用高性能模式 (减少渐隐效果，提高流畅度)", 
            variable=self.high_performance_var
        )
        high_perf_checkbox.pack(anchor='w', pady=2)
        
        # 高性能模式说明
        ttk.Label(
            performance_frame, 
            text="启用后将减少文字渐隐的中间状态，提高阅读流畅度，\n特别适合配置较低的设备或阅读较长的文章。",
            font=('Microsoft YaHei', 9),
            foreground='#666'
        ).pack(anchor='w', pady=(2, 0))
    
    def create_appearance_settings(self, parent):
        """创建外观设置"""
        # 背景颜色设置
        bg_frame = ttk.LabelFrame(parent, text="背景颜色设置", padding=15)
        bg_frame.pack(fill='x', pady=(0, 15))
        
        bg_preset_frame = ttk.Frame(bg_frame)
        bg_preset_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(bg_preset_frame, text="预设颜色:").pack(anchor='w')
        
        preset_frame = ttk.Frame(bg_preset_frame)
        preset_frame.pack(fill='x', pady=(5, 0))
        
        # 预设颜色按钮
        colors = [('纯白色', 'white'), ('浅蓝色', '#E3F2FD'), ('护眼绿', '#E8F5E8'), ('暖黄色', '#FFF8E1')]
        for name, color in colors:
            btn = ttk.Button(preset_frame, text=name, 
                           command=lambda c=color: self.set_background_color(c))
            btn.pack(side='left', padx=(0, 10))
        
        # 自定义颜色
        custom_bg_frame = ttk.Frame(bg_frame)
        custom_bg_frame.pack(fill='x')
        
        ttk.Label(custom_bg_frame, text="自定义颜色:").pack(side='left')
        
        self.bg_color_preview = tk.Label(custom_bg_frame, width=3, height=1, relief='solid', borderwidth=1)
        self.bg_color_preview.pack(side='left', padx=(10, 5))
        
        ttk.Button(custom_bg_frame, text="选择颜色", command=self.choose_background_color).pack(side='left')
        
        # 文字颜色设置
        text_frame = ttk.LabelFrame(parent, text="文字颜色设置", padding=15)
        text_frame.pack(fill='x')
        
        text_preset_frame = ttk.Frame(text_frame)
        text_preset_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(text_preset_frame, text="预设颜色:").pack(anchor='w')
        
        text_colors_frame = ttk.Frame(text_preset_frame)
        text_colors_frame.pack(fill='x', pady=(5, 0))
        
        # 预设文字颜色
        text_colors = [('黑色', 'black'), ('深灰', '#333333'), ('棕色', '#8B4513'), ('深蓝', '#000080')]
        for name, color in text_colors:
            btn = ttk.Button(text_colors_frame, text=name,
                           command=lambda c=color: self.set_text_color(c))
            btn.pack(side='left', padx=(0, 10))
        
        # 自定义文字颜色
        custom_text_frame = ttk.Frame(text_frame)
        custom_text_frame.pack(fill='x')
        
        ttk.Label(custom_text_frame, text="自定义颜色:").pack(side='left')
        
        self.text_color_preview = tk.Label(custom_text_frame, width=3, height=1, relief='solid', borderwidth=1)
        self.text_color_preview.pack(side='left', padx=(10, 5))
        
        ttk.Button(custom_text_frame, text="选择颜色", command=self.choose_text_color).pack(side='left')
    
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def load_current_settings(self):
        """加载当前设置"""
        self.font_size_var.set(self.settings.get('reading', 'font_size', '60'))
        self.line_spacing_var.set(self.settings.get('reading', 'line_spacing', '1.5'))
        self.reading_speed_var.set(self.settings.get('reading', 'reading_speed', '300'))
        self.background_color_var.set(self.settings.get('reading', 'background_color', 'white'))
        self.text_color_var.set(self.settings.get('reading', 'text_color', 'black'))
        self.mode_var.set(self.settings.get('reading', 'mode', 'line'))
        self.high_performance_var.set(self.settings.get('reading', 'high_performance_mode', 'True').lower() == 'true')
        
        # 更新显示
        self.update_labels()
        self.update_color_previews()
    
    def update_labels(self):
        """更新标签显示"""
        self.font_size_label.config(text=str(int(float(self.font_size_var.get()))))
        self.spacing_label.config(text=f"{float(self.line_spacing_var.get()):.1f}")
        self.speed_label.config(text=str(int(float(self.reading_speed_var.get()))))
    
    def update_color_previews(self):
        """更新颜色预览"""
        bg_color = self.background_color_var.get()
        text_color = self.text_color_var.get()
        
        self.bg_color_preview.config(bg=bg_color)
        self.text_color_preview.config(bg=text_color)
    
    def on_font_size_change(self, value):
        """字体大小改变"""
        self.font_size_label.config(text=str(int(float(value))))
    
    def on_line_spacing_change(self, value):
        """行间距改变"""
        self.spacing_label.config(text=f"{float(value):.1f}")
    
    def on_reading_speed_change(self, value):
        """阅读速度改变"""
        self.speed_label.config(text=str(int(float(value))))
    
    def set_background_color(self, color):
        """设置背景颜色"""
        self.background_color_var.set(color)
        self.update_color_previews()
    
    def set_text_color(self, color):
        """设置文字颜色"""
        self.text_color_var.set(color)
        self.update_color_previews()
    
    def choose_background_color(self):
        """选择背景颜色"""
        color = colorchooser.askcolor(color=self.background_color_var.get())[1]
        if color:
            self.set_background_color(color)
    
    def choose_text_color(self):
        """选择文字颜色"""
        color = colorchooser.askcolor(color=self.text_color_var.get())[1]
        if color:
            self.set_text_color(color)
    
    def apply_settings(self):
        """应用设置"""
        try:
            self.settings.set('reading', 'font_size', str(int(float(self.font_size_var.get()))))
            self.settings.set('reading', 'line_spacing', str(float(self.line_spacing_var.get())))
            self.settings.set('reading', 'reading_speed', str(int(float(self.reading_speed_var.get()))))
            self.settings.set('reading', 'background_color', self.background_color_var.get())
            self.settings.set('reading', 'text_color', self.text_color_var.get())
            self.settings.set('reading', 'mode', self.mode_var.get())
            self.settings.set('reading', 'high_performance_mode', str(self.high_performance_var.get()))
            
            self.settings.save_settings()
            
            if self.close_callback:
                self.close_callback()
                
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"设置值无效: {e}")
    
    def save_and_close(self):
        """保存并关闭"""
        self.apply_settings()
        self.window.destroy()
    
    def cancel_and_close(self):
        """取消并关闭"""
        self.window.destroy()
    
    def reset_to_defaults(self):
        """重置到默认值"""
        self.font_size_var.set('60')
        self.line_spacing_var.set('1.5')
        self.reading_speed_var.set('300')
        self.background_color_var.set('white')
        self.text_color_var.set('black')
        self.mode_var.set('line')
        self.high_performance_var.set(True)  # 默认启用高性能模式
        
        self.update_labels()
        self.update_color_previews()
    
    def set_close_callback(self, callback: Callable):
        """设置关闭回调"""
        self.close_callback = callback
    
    def on_closing(self):
        """窗口关闭事件"""
        self.window.destroy()
    
    def show(self):
        """显示窗口"""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
    
    def destroy(self):
        """销毁窗口"""
        if self.window:
            self.window.destroy() 