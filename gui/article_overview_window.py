"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 文章通览窗口
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional
from core.article_parser import Article
from core.settings import Settings

class ArticleOverviewWindow:
    def __init__(self, parent, article: Article, settings: Settings):
        self.parent = parent
        self.article = article
        self.settings = settings
        self.window: Optional[tk.Toplevel] = None
        
        self.create_window()
    
    def create_window(self):
        """创建通览全文窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"锐读 - 速读训练 - 通览全文 - {self.article.title}")
        
        # 设置窗口图标
        try:
            self.window.iconbitmap("ico.png")
        except Exception:
            pass  # 如果图标文件不存在，忽略错误
        
        # 获取屏幕尺寸，设置为屏幕的80%大小
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # 居中显示
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(bg=self.settings.get('reading', 'background_color', 'white'))
        
        # 明确禁用全屏并允许调整窗口大小
        self.window.attributes('-fullscreen', False)
        self.window.resizable(True, True)
        self.window.minsize(600, 400)
        
        # 顶部信息栏
        info_frame = ttk.Frame(self.window)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # 顶部标题栏
        title_frame = ttk.Frame(info_frame)
        title_frame.pack(fill='x')
        
        # 左侧文章信息
        info_left = ttk.Frame(title_frame)
        info_left.pack(side='left', fill='x', expand=True)
        
        info_text = f"《{self.article.title}》 - {self.article.author} ({self.article.date})"
        ttk.Label(info_left, text=info_text, font=('Microsoft YaHei', 14, 'bold')).pack(anchor='w')
        
        # 右侧关闭按钮
        info_right = ttk.Frame(title_frame)
        info_right.pack(side='right')
        
        close_button = ttk.Button(info_right, text="✕", command=self.close_window, width=3)
        close_button.pack(side='right')
        
        # 说明文字
        ttk.Label(info_frame, text="您可以自由滚动浏览全文内容", 
                 font=('Microsoft YaHei', 10), foreground='#666').pack(anchor='w', pady=(5, 0))
        
        # 主容器
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)
        
        # 文本显示区域
        self.text_display = tk.Text(
            text_frame,
            wrap='word',
            font=('Microsoft YaHei', self.settings.get_int('reading', 'font_size', 20)),
            bg=self.settings.get('reading', 'background_color', 'white'),
            fg=self.settings.get('reading', 'text_color', 'black'),
            relief='flat',
            borderwidth=0,
            state='disabled',
            cursor='arrow'
        )
        
        # 设置行间距
        line_spacing = self.settings.get_float('reading', 'line_spacing', 1.5)
        self.text_display.tag_configure('content', 
                                       spacing1=10, 
                                       spacing3=10, 
                                       spacing2=int(line_spacing * 10))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.text_display.yview)
        self.text_display.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.text_display.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="关闭", command=self.close_window).pack(side='right')
        
        # 显示文章内容
        self.load_article_content()
        
        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def load_article_content(self):
        """加载文章内容"""
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        # 使用原始内容，保持自然段落结构
        self.text_display.insert(1.0, self.article.original_content, 'content')
        self.text_display.config(state='disabled')
        
        # 滚动到顶部
        self.text_display.see(1.0)
    
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