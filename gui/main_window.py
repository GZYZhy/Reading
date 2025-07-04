"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 主窗口
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import List, Optional
from core.settings import Settings
from core.article_parser import ArticleParser, Article
from gui.reading_window import ReadingWindow
from gui.settings_window import SettingsWindow
from gui.about_window import AboutWindow

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.settings = Settings()
        self.article_parser = ArticleParser()
        self.articles: List[Article] = []
        self.reading_window: Optional[ReadingWindow] = None
        self.settings_window: Optional[SettingsWindow] = None
        self.about_window: Optional[AboutWindow] = None
        
        self.setup_ui()
        self.load_last_folder()
    
    def setup_ui(self):
        """设置UI界面"""
        # 窗口配置
        self.root.title("锐读 - 速读训练")
        width = self.settings.get_int('app', 'window_width', 1200)
        height = self.settings.get_int('app', 'window_height', 800)
        self.root.geometry(f"{width}x{height}")
        self.root.configure(bg='#f8f9fa')  # 更现代的浅色背景
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("ico.png")
        except Exception:
            pass  # 如果图标文件不存在，忽略错误
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式 - 更现代的设计
        style.configure('Card.TFrame', background='white', relief='flat', borderwidth=0)
        style.configure('Main.TFrame', background='#f8f9fa')
        style.configure('Title.TLabel', font=('Microsoft YaHei', 28, 'bold'), background='#f8f9fa', foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Microsoft YaHei', 14), background='#f8f9fa', foreground='#7f8c8d')
        style.configure('Header.TLabel', font=('Microsoft YaHei', 16, 'bold'), background='#f8f9fa', foreground='#34495e')
        style.configure('Modern.TButton', font=('Microsoft YaHei', 10, 'bold'), padding=(20, 10))
        style.configure('Accent.TButton', font=('Microsoft YaHei', 12, 'bold'), padding=(25, 15))
        
        # 主容器 - 增加边距，使用更现代的背景
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # 标题区域 - 重新设计更美观的标题区域
        title_frame = ttk.Frame(main_frame, style='Main.TFrame')
        title_frame.pack(fill='x', pady=(0, 30))
        
        # 标题和副标题
        title_container = ttk.Frame(title_frame, style='Main.TFrame')
        title_container.pack(side='left')
        
        title_label = ttk.Label(title_container, text="锐读", style='Title.TLabel')
        title_label.pack(anchor='w')
        
        subtitle_label = ttk.Label(title_container, text="专业的速读训练平台", style='Subtitle.TLabel')
        subtitle_label.pack(anchor='w')
        
        # 工具栏 - 更现代的按钮设计
        toolbar_frame = ttk.Frame(title_frame, style='Main.TFrame')
        toolbar_frame.pack(side='right')
        
        select_folder_btn = ttk.Button(toolbar_frame, text="📁 选择文件夹", command=self.select_folder, style='Modern.TButton')
        select_folder_btn.pack(side='left', padx=(0, 15))
        
        settings_btn = ttk.Button(toolbar_frame, text="⚙️ 设置", command=self.open_settings, style='Modern.TButton')
        settings_btn.pack(side='left', padx=(0, 15))
        
        about_btn = ttk.Button(toolbar_frame, text="ℹ️ 关于", command=self.open_about, style='Modern.TButton')
        about_btn.pack(side='left')
        
        # 内容区域 - 优化布局和间距
        content_frame = ttk.Frame(main_frame, style='Main.TFrame')
        content_frame.pack(fill='both', expand=True)
        
        # 左侧 - 文章列表区域，使用卡片式设计
        left_frame = ttk.Frame(content_frame, style='Card.TFrame')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 20))
        
        # 文章列表容器
        list_container = ttk.Frame(left_frame)
        list_container.pack(fill='both', expand=True, padx=25, pady=25)
        
        # 文章列表标题
        list_header = ttk.Frame(list_container, style='Main.TFrame')
        list_header.pack(fill='x', pady=(0, 20))
        
        ttk.Label(list_header, text="📚 文章库", style='Header.TLabel').pack(side='left')
        
        # 文章数量标签
        self.article_count_label = ttk.Label(list_header, text="", font=('Microsoft YaHei', 10), 
                                           background='#e3f2fd', foreground='#1976d2', 
                                           padding=(10, 5))
        self.article_count_label.pack(side='right')
        
        # 文章列表
        list_frame = ttk.Frame(list_container)
        list_frame.pack(fill='both', expand=True)
        
        # 创建Treeview来显示文章 - 更现代的样式
        columns = ('title', 'author', 'date', 'type')
        self.article_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)
        
        # 设置列标题
        self.article_tree.heading('title', text='📖 标题')
        self.article_tree.heading('author', text='✍️ 作者')
        self.article_tree.heading('date', text='📅 日期')
        self.article_tree.heading('type', text='🏷️ 类型')
        
        # 设置列宽
        self.article_tree.column('title', width=350)
        self.article_tree.column('author', width=120)
        self.article_tree.column('date', width=100)
        self.article_tree.column('type', width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.article_tree.yview)
        self.article_tree.configure(yscrollcommand=scrollbar.set)
        
        self.article_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 双击事件
        self.article_tree.bind('<Double-1>', self.on_article_double_click)
        
        # 右侧 - 控制面板，重新设计为更优雅的卡片
        right_frame = ttk.Frame(content_frame, style='Card.TFrame')
        right_frame.pack(side='right', fill='y')
        right_frame.configure(width=320)
        
        # 控制面板内容
        control_inner = ttk.Frame(right_frame)
        control_inner.pack(fill='both', expand=True, padx=25, pady=25)
        
        # 控制面板标题
        control_header = ttk.Frame(control_inner, style='Main.TFrame')
        control_header.pack(fill='x', pady=(0, 25))
        
        ttk.Label(control_header, text="🎯 阅读控制", font=('Microsoft YaHei', 16, 'bold'), 
                 background='white', foreground='#2c3e50').pack(anchor='w')
        
        # 开始阅读按钮 - 更突出的设计
        start_btn_frame = ttk.Frame(control_inner)
        start_btn_frame.pack(fill='x', pady=(0, 30))
        
        self.start_button = ttk.Button(
            start_btn_frame, 
            text="🚀 开始速读训练", 
            command=self.start_reading,
            style='Accent.TButton'
        )
        self.start_button.pack(fill='x')
        
        # 快速设置标题
        settings_header = ttk.Frame(control_inner, style='Main.TFrame')
        settings_header.pack(fill='x', pady=(0, 20))
        
        ttk.Label(settings_header, text="⚡ 快速设置", font=('Microsoft YaHei', 14, 'bold'), 
                 background='white', foreground='#34495e').pack(anchor='w')
        
        # 阅读模式
        mode_frame = ttk.Frame(control_inner)
        mode_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(mode_frame, text="📖 阅读模式:", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w')
        self.mode_var = tk.StringVar(value=self.settings.get('reading', 'mode', 'line'))
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, 
                                values=['line', 'page'], state='readonly', height=8)
        mode_combo.pack(fill='x', pady=(8, 0))
        mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
        # 阅读速度
        speed_frame = ttk.Frame(control_inner)
        speed_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(speed_frame, text="⚡ 阅读速度 (字/分钟):", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w')
        self.speed_var = tk.StringVar(value=self.settings.get('reading', 'reading_speed', '300'))
        speed_spinbox = ttk.Spinbox(speed_frame, from_=60, to=1200, textvariable=self.speed_var, width=10)
        speed_spinbox.pack(fill='x', pady=(8, 0))
        speed_spinbox.bind('<KeyRelease>', self.on_speed_change)
        
        # 字体大小
        font_frame = ttk.Frame(control_inner)
        font_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(font_frame, text="🔤 字体大小:", font=('Microsoft YaHei', 10, 'bold')).pack(anchor='w')
        self.font_size_var = tk.StringVar(value=self.settings.get('reading', 'font_size', '60'))
        font_spinbox = ttk.Spinbox(font_frame, from_=20, to=100, textvariable=self.font_size_var, width=10)
        font_spinbox.pack(fill='x', pady=(8, 0))
        font_spinbox.bind('<KeyRelease>', self.on_font_size_change)
    

    
    def select_folder(self):
        """选择文章文件夹"""
        folder_path = filedialog.askdirectory(title="选择文章文件夹")
        if folder_path:
            self.load_articles_from_folder(folder_path)
            # 保存路径到设置
            self.settings.set('app', 'last_folder', folder_path)
            self.settings.save_settings()
    
    def load_last_folder(self):
        """加载上次打开的文件夹"""
        last_folder = self.settings.get('app', 'last_folder')
        print(f"[GUI-DEBUG] 上次文件夹路径: {last_folder}")
        
        if last_folder and os.path.exists(last_folder):
            print("[GUI-DEBUG] 开始加载上次的文件夹")
            self.load_articles_from_folder(last_folder)
        else:
            print("[GUI-DEBUG] 没有上次的文件夹或路径不存在")
    
    def load_articles_from_folder(self, folder_path: str):
        """从文件夹加载文章"""
        try:
            print(f"[GUI-DEBUG] 开始加载文章夹: {folder_path}")
            self.articles = self.article_parser.load_articles_from_folder(folder_path)
            print(f"[GUI-DEBUG] 加载到 {len(self.articles)} 篇文章")
            
            self.update_article_list()
            
            if self.articles:
                print("[GUI-DEBUG] 显示成功消息")
                messagebox.showinfo("成功", f"成功加载 {len(self.articles)} 篇文章")
            else:
                print("[GUI-DEBUG] 显示警告消息")
                messagebox.showwarning("提示", "所选文件夹中没有找到有效的txt文章文件")
        except Exception as e:
            print(f"[GUI-DEBUG] 加载文章出错: {e}")
            messagebox.showerror("错误", f"加载文章时出错: {e}")
    
    def update_article_list(self):
        """更新文章列表显示"""
        # 清空现有内容
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        # 添加文章
        for i, article in enumerate(self.articles):
            self.article_tree.insert('', 'end', iid=i, values=(
                article.title,
                article.author,
                article.date,
                article.type
            ))
        
        # 更新文章数量标签
        article_count = len(self.articles)
        if article_count > 0:
            self.article_count_label.config(text=f"共 {article_count} 篇文章")
        else:
            self.article_count_label.config(text="暂无文章")
    
    def on_article_double_click(self, event):
        """文章双击事件"""
        print("[GUI-DEBUG] 文章被双击")
        selection = self.article_tree.selection()
        print(f"[GUI-DEBUG] 双击选择的文章: {selection}")
        
        if selection:
            article_index = int(selection[0])
            print(f"[GUI-DEBUG] 双击开始阅读文章索引: {article_index}")
            self.start_reading_with_article(self.articles[article_index])
    
    def start_reading(self):
        """开始速读训练"""
        print("[GUI-DEBUG] 开始阅读按钮被点击")
        print(f"[GUI-DEBUG] 文章数量: {len(self.articles)}")
        
        if not self.articles:
            print("[GUI-DEBUG] 没有文章，显示警告")
            messagebox.showwarning("提示", "请先选择包含文章的文件夹")
            return
        
        selection = self.article_tree.selection()
        print(f"[GUI-DEBUG] 选择的文章: {selection}")
        
        if not selection:
            print("[GUI-DEBUG] 没有选择文章，显示警告")
            messagebox.showwarning("提示", "请选择要阅读的文章")
            return
        
        article_index = int(selection[0])
        print(f"[GUI-DEBUG] 开始阅读文章索引: {article_index}")
        print(f"[GUI-DEBUG] 文章标题: {self.articles[article_index].title}")
        
        self.start_reading_with_article(self.articles[article_index])
    
    def start_reading_with_article(self, article: Article):
        """使用指定文章开始阅读"""
        print(f"[GUI-DEBUG] 准备开始阅读文章: {article.title}")
        
        if self.reading_window:
            print("[GUI-DEBUG] 销毁旧的阅读窗口")
            self.reading_window.destroy()
        
        print("[GUI-DEBUG] 创建新的阅读窗口")
        self.reading_window = ReadingWindow(self.root, article, self.settings)
        print("[GUI-DEBUG] 显示阅读窗口")
        self.reading_window.show()
    
    def open_settings(self):
        """打开设置窗口"""
        if self.settings_window:
            self.settings_window.destroy()
        
        self.settings_window = SettingsWindow(self.root, self.settings)
        self.settings_window.show()
    
    def open_about(self):
        """打开关于窗口"""
        if self.about_window:
            self.about_window.destroy()
        
        self.about_window = AboutWindow(self.root, self.settings)
        self.about_window.show()
    
    def on_mode_change(self, event=None):
        """阅读模式改变"""
        self.settings.set('reading', 'mode', self.mode_var.get())
        self.settings.save_settings()
    
    def on_speed_change(self, event=None):
        """阅读速度改变"""
        try:
            speed = int(self.speed_var.get())
            self.settings.set('reading', 'reading_speed', str(speed))
            self.settings.save_settings()
        except ValueError:
            pass
    
    def on_font_size_change(self, event=None):
        """字体大小改变"""
        try:
            size = int(self.font_size_var.get())
            self.settings.set('reading', 'font_size', str(size))
            self.settings.save_settings()
        except ValueError:
            pass
    
    def run(self):
        """运行主窗口"""
        self.root.mainloop()
    
    def destroy(self):
        """销毁窗口"""
        if self.reading_window:
            self.reading_window.destroy()
        if self.settings_window:
            self.settings_window.destroy()
        if self.about_window:
            self.about_window.destroy()
        self.root.destroy() 