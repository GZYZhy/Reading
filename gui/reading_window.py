"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 阅读窗口
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from core.article_parser import Article
from core.reading_controller import ReadingController
from core.settings import Settings
from gui.article_overview_window import ArticleOverviewWindow

class ReadingWindow:
    def __init__(self, parent, article: Article, settings: Settings):
        self.parent = parent
        self.article = article
        self.settings = settings
        self.window: tk.Toplevel
        self.controller = ReadingController()
        
        # 设置控制器
        self.controller.set_article(article)
        self.controller.set_reading_speed(settings.get_int('reading', 'reading_speed', 300))
        self.controller.set_mode(settings.get('reading', 'mode', 'line'))
        
        # 设置高性能模式
        high_performance = settings.get('reading', 'high_performance_mode', 'True').lower() == 'true'
        self.controller.set_high_performance_mode(high_performance)
        
        self.controller.set_update_callback(self.update_display)
        
        # UI元素 - 在create_window()中初始化，所以不会是None
        self.text_display: tk.Text
        self.progress_bar: ttk.Progressbar
        self.status_label: ttk.Label
        self.time_label: ttk.Label
        self.pause_button: ttk.Button
        self.stop_button: ttk.Button
        self.reset_button: ttk.Button
        
        # 动态布局相关
        self.last_window_width = 1000
        self.last_window_height = 800
        self.resize_timer = None
        
        # 新增：布局更新防抖动
        self.layout_update_timer = None
        self.layout_update_pending = False
        self.last_font_size = settings.get_int('reading', 'font_size', 60)
        
        # 重置状态标志
        self.is_reset_state = False
        
        # 答题相关
        self.current_question_index = 0
        self.selected_answers = {}  # 存储用户选择的答案
        self.question_widgets = {}  # 存储问题界面的组件
        
        self.create_window()
        
        # 初始化动态布局
        self.update_layout_params()
        
        # 自动开始阅读
        self.start_reading()
    
    def create_window(self):
        """创建阅读窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"锐读 - 速读训练 - {self.article.title}")
        self.window.configure(bg=self.settings.get('reading', 'background_color', 'white'))
        
        # 设置窗口图标
        try:
            self.window.iconbitmap("ico.png")
        except Exception:
            pass  # 如果图标文件不存在，忽略错误
        
        # 设置全屏且不允许调整大小
        self.window.attributes('-fullscreen', True)
        self.window.resizable(False, False)
        
        # 阻止窗口关闭，直到停止阅读
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 绑定窗口大小变化事件
        self.window.bind('<Configure>', self.on_window_configure)
        
        # 顶部信息栏 - 固定高度
        info_frame = ttk.Frame(self.window)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # 文章信息
        info_text = f"《{self.article.title}》 - {self.article.author} ({self.article.date})"
        ttk.Label(info_frame, text=info_text, font=('Microsoft YaHei', 12)).pack(anchor='w')
        
        # 主容器 - 使用grid布局确保控制面板总是可见
        main_container = ttk.Frame(self.window)
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 配置grid权重
        main_container.grid_rowconfigure(0, weight=1)  # 文本区域可伸缩
        main_container.grid_rowconfigure(1, weight=0)  # 控制面板固定高度
        main_container.grid_columnconfigure(0, weight=1)
        
        # 文本显示区域
        text_frame = ttk.Frame(main_container)
        text_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 10))
        
        # 创建文本显示器 - 启用自动换行
        self.text_display = tk.Text(
            text_frame,
            wrap='word',  # 启用按词换行
            font=('Microsoft YaHei', self.settings.get_int('reading', 'font_size', 60)),
            bg=self.settings.get('reading', 'background_color', 'white'),
            fg=self.settings.get('reading', 'text_color', 'black'),
            relief='flat',
            borderwidth=0,
            state='disabled',
            cursor='arrow'
        )
        
        # 设置行间距
        line_spacing = self.settings.get_float('reading', 'line_spacing', 1.5)
        self.text_display.tag_configure('content', spacing1=10, spacing3=10, 
                                       spacing2=int(line_spacing * 10))
        
        # 创建滚动条但初始时禁用
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.text_display.yview)
        self.text_display.configure(yscrollcommand=scrollbar.set)
        
        # 初始时禁用滚动功能（阅读模式）
        self.scrollbar = scrollbar
        self._disable_scrolling()
        
        # 布局文本和滚动条
        self.text_display.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 控制面板 - 固定在底部
        control_frame = ttk.Frame(main_container)
        control_frame.grid(row=1, column=0, sticky='ew')
        
        # 进度条区域
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(progress_frame, text="阅读进度:").pack(side='left')
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(side='left', padx=(10, 0), fill='x', expand=True)
        
        # 控制按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', pady=(0, 10))
        
        # 左侧按钮组
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side='left')
        
        # 删除开始按钮，合并暂停/继续为一个按钮
        self.pause_button = ttk.Button(left_buttons, text="⏸ 暂停", command=self.pause_reading)
        self.pause_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(left_buttons, text="⏹ 结束阅读", command=self.stop_reading)
        self.stop_button.pack(side='left', padx=(0, 10))
        
        # 重置按钮
        self.reset_button = ttk.Button(left_buttons, text="⏮ 重置", command=self.reset_reading, state='disabled')
        self.reset_button.pack(side='left', padx=(0, 10))
        
        # 通览全文按钮（固定显示）
        self.overview_button = ttk.Button(left_buttons, text="📖 通览全文", command=self.open_overview)
        self.overview_button.pack(side='left', padx=(0, 10))
        
        # 右侧按钮组
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side='right')
        
        # 设置按钮
        ttk.Button(right_buttons, text="⚙ 设置", command=self.open_settings).pack(side='right')
        
        # 状态栏
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill='x')
        
        # 左侧状态信息
        status_left = ttk.Frame(status_frame)
        status_left.pack(side='left', fill='x', expand=True)
        
        self.status_label = ttk.Label(status_left, text="准备开始速读训练", font=('Microsoft YaHei', 10))
        self.status_label.pack(anchor='w')
        
        # 右侧剩余时间
        status_right = ttk.Frame(status_frame)
        status_right.pack(side='right')
        
        self.time_label = ttk.Label(status_right, text="剩余时间: --", font=('Microsoft YaHei', 10))
        self.time_label.pack(anchor='e')
        
        print(f"[GUI-DEBUG] 阅读窗口创建完成，所有控件已添加")
        
        # 初始显示完整文章
        self.show_full_article()
    
    def on_window_configure(self, event):
        """窗口大小变化事件处理"""
        # 只处理窗口本身的configure事件，忽略子控件的
        if event.widget != self.window:
            return
        
        current_width = self.window.winfo_width()
        current_height = self.window.winfo_height()
        
        # 检查是否真的发生了大小变化
        if (abs(current_width - self.last_window_width) > 10 or 
            abs(current_height - self.last_window_height) > 10):
            
            print(f"[GUI-DEBUG] 窗口大小变化: {current_width}x{current_height}")
            
            # 取消之前的定时器
            if self.resize_timer:
                self.window.after_cancel(self.resize_timer)
            
            # 设置新的定时器，延迟更新避免频繁重计算
            self.resize_timer = self.window.after(300, self._delayed_layout_update)
            
            self.last_window_width = current_width
            self.last_window_height = current_height
    
    def _delayed_layout_update(self):
        """延迟的布局更新"""
        self.resize_timer = None
        try:
            self.update_layout_params()
        except Exception as e:
            print(f"[GUI-DEBUG] 布局更新出错: {e}")
    
    def update_layout_params(self):
        """根据当前窗口大小更新布局参数"""
        print(f"[GUI-DEBUG] update_layout_params 被调用")
        
        # 如果已有待处理的布局更新，取消它
        if self.layout_update_timer:
            self.window.after_cancel(self.layout_update_timer)
            self.layout_update_timer = None
            print(f"[GUI-DEBUG] 取消了之前的布局更新")
        
        # 检查字号是否发生变化
        current_font_size = self.settings.get_int('reading', 'font_size', 60)
        font_size_changed = current_font_size != self.last_font_size
        
        if font_size_changed:
            print(f"[GUI-DEBUG] 字号变化: {self.last_font_size} -> {current_font_size}")
            self.last_font_size = current_font_size
            
            # 字号变化时使用防抖动机制
            self.layout_update_pending = True
            self.layout_update_timer = self.window.after(300, self._perform_layout_update)
            print(f"[GUI-DEBUG] 字号变化，延迟300ms后更新布局")
            return
        
        # 非字号变化的立即更新
        self._perform_layout_update()
    
    def _perform_layout_update(self):
        """执行实际的布局更新"""
        self.layout_update_timer = None
        self.layout_update_pending = False
        
        print(f"[GUI-DEBUG] 开始执行布局更新")
        try:
            # 等待窗口完全初始化
            self.window.update_idletasks()
            
            # 获取文本显示区域的实际大小
            text_width = self.text_display.winfo_width()
            text_height = self.text_display.winfo_height()
            
            print(f"[GUI-DEBUG] 窗口尺寸: {text_width}x{text_height}")
            
            if text_width <= 1 or text_height <= 1:
                # 窗口还没有完全初始化，延迟执行
                print(f"[GUI-DEBUG] 窗口尺寸无效，延迟100ms后重试")
                self.layout_update_timer = self.window.after(100, self._perform_layout_update)
                return
            
            # 获取字体大小和行间距
            font_size = self.settings.get_int('reading', 'font_size', 60)
            line_spacing = self.settings.get_float('reading', 'line_spacing', 1.5)
            
            print(f"[GUI-DEBUG] 字体大小: {font_size}, 行间距: {line_spacing}")
            
            # 更准确地计算字符宽度（中文字符）
            char_width = font_size * 0.6  # 中文字符大约是字体大小的0.6倍宽
            
            # 通过实际测量来计算行高
            # 创建临时测试文本来测量实际行高
            self.text_display.config(state='normal')
            
            # 保存当前内容
            current_content = self.text_display.get(1.0, tk.END)
            print(f"[GUI-DEBUG] 保存当前内容，长度: {len(current_content)}")
            
            # 插入测试文本（多行）来测量行高
            test_text = "测试行一\n测试行二\n测试行三"
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(1.0, test_text, 'content')
            
            # 强制更新显示
            self.text_display.update_idletasks()
            print(f"[GUI-DEBUG] 已插入测试文本并更新显示")
            
            # 测量文本高度
            bbox_first = self.text_display.bbox("1.0")
            bbox_third = self.text_display.bbox("3.0")
            
            print(f"[GUI-DEBUG] bbox_first: {bbox_first}, bbox_third: {bbox_third}")
            
            actual_line_height = None
            if bbox_first and bbox_third:
                # 计算实际行高（包括行间距）
                actual_line_height = bbox_third[1] - bbox_first[1]
                print(f"[GUI-DEBUG] 实际测量行高: {actual_line_height}px")
            else:
                # 如果测量失败，使用估算值但包含行间距
                actual_line_height = font_size * line_spacing
                print(f"[GUI-DEBUG] 测量失败，使用估算行高（含行间距）: {actual_line_height}px")
            
            # 确保行高不为0或负数
            if actual_line_height <= 0:
                actual_line_height = font_size * 1.5
                print(f"[GUI-DEBUG] 行高无效，使用默认值: {actual_line_height}px")
            
            # 恢复原内容
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(1.0, current_content)
            self.text_display.config(state='disabled')
            print(f"[GUI-DEBUG] 已恢复原内容")
            
            # 计算每行可容纳的字符数（留一些边距）
            chars_per_line = max(20, int((text_width - 40) / char_width))
            
            # 计算每页可容纳的行数（确保最后一行有足够空间）
            # 预留更多边距，并使用向下取整后再减1确保空间充足
            available_height = text_height - 100  # 增加更多边距，确保底部有足够空间
            max_lines = available_height / actual_line_height
            
            # 使用floor确保不会超出边界，并额外减去1行的安全边距
            import math
            lines_per_page = max(3, int(math.floor(max_lines - 1.0)))
            
            print(f"[GUI-DEBUG] 布局参数更新: 文本区域{text_width}x{text_height}, "
                  f"实际行高: {actual_line_height:.1f}px, 可用高度: {available_height}px, "
                  f"理论最大行数: {max_lines:.2f}, 安全行数: {lines_per_page}")
            print(f"[GUI-DEBUG] 字符/行: {chars_per_line}, 行/页: {lines_per_page}")
            
            # 验证计算结果
            required_height = lines_per_page * actual_line_height + 100
            print(f"[GUI-DEBUG] 验证: {lines_per_page}行需要{required_height:.1f}px，实际有{text_height}px")
            
            # 保存当前阅读状态（如果正在阅读）
            was_reading = self.controller.is_reading
            current_progress = self.controller.get_progress() if self.controller.is_reading else 0
            was_paused = self.controller.is_paused
            
            # 如果正在阅读，先完全停止以避免状态冲突
            if was_reading:
                print(f"[GUI-DEBUG] 正在阅读中，完全停止以更新布局: 进度={current_progress:.1%}, 暂停={was_paused}")
                # 完全停止阅读线程，避免与重分页冲突
                self.controller.stop_reading()
                
                # 等待线程完全结束
                if self.controller.reading_thread and self.controller.reading_thread.is_alive():
                    self.controller.reading_thread.join(timeout=2.0)
                    print(f"[GUI-DEBUG] 阅读线程已完全停止")
            
            # 在完全停止状态下安全地更新控制器参数
            print(f"[GUI-DEBUG] 更新控制器参数...")
            
            # 设置智能分页参数
            self.controller.set_text_widget_reference(
                self.text_display, 
                available_height, 
                font_size, 
                line_spacing
            )
            
            self.controller.set_max_line_length(chars_per_line)
            self.controller.set_lines_per_page(lines_per_page)
            print(f"[GUI-DEBUG] 控制器参数更新完成，包括智能分页参数")
            
            # 如果之前正在阅读，重新启动阅读
            if was_reading:
                print(f"[GUI-DEBUG] 重新启动阅读...")
                
                # 特别针对page模式的安全重启逻辑
                if self.controller.mode == 'page':
                    # Page模式：验证current_page是否仍然有效
                    if self.controller.current_page >= len(self.controller.pages):
                        print(f"[GUI-DEBUG] Page模式：当前页{self.controller.current_page}超出新页数{len(self.controller.pages)}，调整到最后一页")
                        self.controller.current_page = max(0, len(self.controller.pages) - 1)
                    print(f"[GUI-DEBUG] Page模式安全重启：当前页{self.controller.current_page}/{len(self.controller.pages)}")
                
                # 重新启动阅读
                self.controller.is_reading = True
                self.controller.is_paused = was_paused  # 恢复原始暂停状态
                
                # 启动新的阅读线程
                import threading
                if self.controller.mode == 'line':
                    self.controller.reading_thread = threading.Thread(target=self.controller._line_reading_loop_with_fade)
                else:
                    self.controller.reading_thread = threading.Thread(target=self.controller._page_reading_loop)
                
                self.controller.reading_thread.daemon = True
                self.controller.reading_thread.start()
                print(f"[GUI-DEBUG] 新阅读线程已启动，暂停状态: {was_paused}")
                
                # 立即更新显示
                print(f"[GUI-DEBUG] 立即更新显示以应用新布局")
                self.update_display()
            else:
                # 未在阅读，只需更新显示
                print(f"[GUI-DEBUG] 未在阅读，只更新显示")
                self.update_display()
                
        except Exception as e:
            print(f"[GUI-DEBUG] 更新布局参数时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def show_full_article(self):
        """显示完整文章"""
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        # 使用原始内容，保持自然段落结构
        self.text_display.insert(1.0, self.article.original_content, 'content')
        self.text_display.config(state='disabled')
    
    def start_reading(self):
        """开始阅读"""
        print(f"[GUI-DEBUG] 开始阅读按钮被点击")
        
        # 清除重置状态标志
        self.is_reset_state = False
        
        # 确保布局参数是最新的
        print(f"[GUI-DEBUG] 强制更新布局参数...")
        self.update_layout_params()
        print(f"[GUI-DEBUG] 布局参数更新完成")
        
        # 清空显示，准备分页模式
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.config(state='disabled')
        print(f"[GUI-DEBUG] 文本框已清空")
        
        # 恢复正常的按钮状态，包括固定的通览全文按钮
        self.overview_button.pack(side='left', padx=(0, 10))
        
        self.controller.start_reading()
        self.pause_button.config(text="⏸ 暂停", state='normal')
        self.stop_button.config(text="⏹ 结束阅读", state='normal')
        self.reset_button.config(state='disabled')  # 阅读中禁用重置
        self.status_label.config(text="正在阅读...")
        print(f"[GUI-DEBUG] UI状态已更新，控制器已启动")
        
        # 立即更新显示到分页模式
        self.update_display()
        print(f"[GUI-DEBUG] 首次显示更新已调用")
    
    def pause_reading(self):
        """暂停/继续阅读"""
        print(f"[GUI-DEBUG] 暂停/继续按钮被点击")
        
        # 检查是否是重置后的开始
        if self.is_reset_state:
            print(f"[GUI-DEBUG] 重置后重新开始阅读")
            self.is_reset_state = False
            # 重新开始阅读
            self.start_reading()
            return
        
        # 正常的暂停/继续逻辑
        self.controller.pause_reading()
        if self.controller.is_paused:
            self.pause_button.config(text="▶ 继续")
            self.reset_button.config(state='normal')  # 暂停时启用重置
            self.status_label.config(text="已暂停")
            print(f"[GUI-DEBUG] 阅读已暂停")
        else:
            self.pause_button.config(text="⏸ 暂停")
            self.reset_button.config(state='disabled')  # 继续时禁用重置
            self.status_label.config(text="正在阅读...")
            print(f"[GUI-DEBUG] 阅读已继续")
    
    def stop_reading(self):
        """停止阅读"""
        print(f"[GUI-DEBUG] 停止阅读按钮被点击")
        
        # 清除重置状态
        self.is_reset_state = False
        
        self.controller.stop_reading()
        self.pause_button.config(state='disabled', text="⏸ 暂停")
        self.stop_button.config(text="⏹ 结束阅读", state='disabled')
        self.reset_button.config(state='disabled')  # 停止时禁用重置
        self.status_label.config(text="已停止")
        self.show_full_article()
        self.progress_bar['value'] = 0
        print(f"[GUI-DEBUG] 阅读已停止，UI状态已重置")
        
        # 先显示和恢复主窗口，确保它准备好接收焦点
        if self.parent:
            try:
                self.parent.deiconify()  # 显示主窗口（如果被最小化）
                self.parent.lift()        # 将主窗口置于最前
                self.parent.attributes('-topmost', True)  # 临时置顶
                self.parent.focus_force() # 强制获得焦点
                self.parent.update_idletasks()  # 确保主窗口更新完成
                print(f"[GUI-DEBUG] 停止阅读，主窗口已恢复显示")
                
                # 延迟一点时间确保主窗口完全显示
                self.parent.after(50, lambda: self.parent.attributes('-topmost', False))
                
            except Exception as e:
                print(f"[GUI-DEBUG] 恢复主窗口时出错: {e}")
        
        # 延迟销毁阅读窗口，确保主窗口已经完全显示
        def delayed_destroy():
            try:
                if self.window:
                    self.window.withdraw()  # 先隐藏窗口
                    self.window.after(100, lambda: self.window.destroy() if self.window else None)  # 延迟销毁
                    print(f"[GUI-DEBUG] 阅读窗口已安排销毁")
            except Exception as e:
                print(f"[GUI-DEBUG] 销毁窗口时出错: {e}")
        
        # 延迟执行销毁，给主窗口时间完全显示
        if self.window:
            self.window.after(100, delayed_destroy)
    
    def reset_reading(self):
        """重置阅读"""
        print(f"[GUI-DEBUG] 重置按钮被点击")
        
        # 停止当前阅读
        if self.controller.is_reading:
            self.controller.stop_reading()
        
        # 确保滚动功能被禁用（回到阅读模式）
        self._disable_scrolling()
        
        # 重置位置和状态
        self.controller.reset_position()
        self.show_full_article()
        self.progress_bar['value'] = 0
        self.time_label.config(text="剩余时间: --")
        
        # 恢复正常的按钮状态，包括固定的通览全文按钮
        self.overview_button.pack(side='left', padx=(0, 10))
        
        # 设置为重置状态（类似暂停，但可以重新开始）
        self.is_reset_state = True
        self.controller.is_reading = False
        self.controller.is_paused = True  # 设置为暂停状态，允许继续
        
        # 更新按钮状态
        self.pause_button.config(text="▶ 开始", state='normal')  # 显示为开始
        self.stop_button.config(text="⏹ 结束阅读", state='normal')
        self.reset_button.config(state='disabled')  # 重置后禁用重置按钮
        self.status_label.config(text="已重置，点击开始重新阅读")
        print(f"[GUI-DEBUG] 阅读已重置，等待重新开始")
    
    def update_display(self):
        """更新显示内容"""
        print(f"[GUI-DEBUG] update_display 被调用")
        # 在主线程中更新UI，不管是否正在阅读都要更新
        if self.window:
            # 使用 after 而不是 after_idle，确保立即执行
            self.window.after(0, self._update_display_safe)
            print(f"[GUI-DEBUG] 已调度 _update_display_safe")
        else:
            print(f"[GUI-DEBUG] 警告：窗口不存在")
    
    def _update_display_safe(self):
        """安全的UI更新方法"""
        print(f"[GUI-DEBUG] _update_display_safe 开始执行")
        try:
            # 获取当前状态
            progress = self.controller.get_progress()
            is_reading = self.controller.is_reading
            
            print(f"[GUI-DEBUG] 当前状态: 进度={progress:.1%}, 正在阅读={is_reading}")
            
            # 始终获取并显示当前页内容
            if hasattr(self.controller, 'get_current_display_text_with_states'):
                current_text, char_states = self.controller.get_current_display_text_with_states()
                print(f"[GUI-DEBUG] 获取到显示文本，长度: {len(current_text) if current_text else 0}, 状态数: {len(char_states)}")
            else:
                current_text = self.controller.get_current_display_text()
                char_states = {}
                print(f"[GUI-DEBUG] 获取到显示文本，长度: {len(current_text) if current_text else 0}")
            
            self.text_display.config(state='normal')
            self.text_display.delete(1.0, tk.END)
            
            # 检查是否处于问题模式
            if self.controller.is_in_question_mode():
                # 显示问题界面
                self._display_questions()
                print(f"[GUI-DEBUG] 显示问题界面")
            elif is_reading or progress > 0:
                # 阅读中或已开始阅读，显示分页内容
                if progress >= 1.0 and not is_reading and not self.controller.is_in_question_mode():
                    # 阅读完成，检查是否有问题（且未在答题模式）
                    # 使用reading_finished标志确保阅读真正完成
                    if hasattr(self.controller, 'reading_finished') and self.controller.reading_finished:
                        if self.controller.has_questions():
                            # 有问题，自动进入问题模式
                            print(f"[GUI-DEBUG] 阅读完成（reading_finished=True），检测到有问题，准备进入答题模式")
                            
                            # 先显示过渡信息
                            completion_text = "📚 阅读完成！\n\n文章内容已阅读完毕，正在加载答题环节..."
                            self.text_display.insert(1.0, completion_text, 'content')
                            
                            # 短暂延迟后自动进入答题模式
                            self.window.after(1500, self._auto_enter_question_mode)
                            print(f"[GUI-DEBUG] 已安排1.5秒后进入答题模式")
                        else:
                            # 没有问题，直接显示完成信息
                            completion_text = "🎉 速读训练完成！\n\n恭喜您完成了这篇文章的速读训练。"
                            self.text_display.insert(1.0, completion_text, 'content')
                            print(f"[GUI-DEBUG] 阅读完成，没有问题，显示完成信息")
                    else:
                        # 进度100%但reading_finished=False，可能是其他原因导致的进度计算
                        # 继续显示当前页面内容
                        if current_text is not None:
                            display_text = current_text
                        else:
                            display_text = ""
                        
                        self.text_display.insert(1.0, display_text, 'content')
                        
                        if char_states:
                            self._apply_fade_effects(display_text, char_states)
                            print(f"[GUI-DEBUG] 应用了渐隐效果到 {len(char_states)} 个字符")
                        
                        print(f"[GUI-DEBUG] 进度100%但reading_finished=False，继续显示分页内容")
                else:
                    # 正在阅读或暂停中，显示当前页内容
                    if current_text is not None:
                        # 直接显示内容，不再强制补齐到固定行数
                        display_text = current_text
                    else:
                        display_text = ""
                    
                    # 插入文本
                    self.text_display.insert(1.0, display_text, 'content')
                    
                    # 应用渐隐效果
                    if char_states:
                        self._apply_fade_effects(display_text, char_states)
                        print(f"[GUI-DEBUG] 应用了渐隐效果到 {len(char_states)} 个字符")
                    
                    print(f"[GUI-DEBUG] 显示分页内容")

            else:
                # 未开始阅读，显示完整文章
                # 使用原始内容，保持自然段落结构
                self.text_display.insert(1.0, self.article.original_content, 'content')
                print(f"[GUI-DEBUG] 显示完整文章")
            
            self.text_display.config(state='disabled')
            
            # 更新进度条
            self.progress_bar['value'] = progress * 100
            print(f"[GUI-DEBUG] 进度条更新到: {progress * 100:.1f}%")
            
            # 更新剩余时间
            if is_reading and not self.controller.is_paused:
                remaining_seconds = self.controller.get_remaining_time()
                if remaining_seconds > 0:
                    hours = remaining_seconds // 3600
                    minutes = (remaining_seconds % 3600) // 60
                    seconds = remaining_seconds % 60
                    
                    if hours > 0:
                        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    else:
                        time_str = f"{minutes:02d}:{seconds:02d}"
                    
                    self.time_label.config(text=f"剩余时间: {time_str}")
                else:
                    self.time_label.config(text="剩余时间: 00:00")
            else:
                self.time_label.config(text="剩余时间: --")
            
            # 检查阅读状态
            if self.is_reset_state:
                # 重置状态：显示可以重新开始
                self.pause_button.config(text="▶ 开始", state='normal')
                self.stop_button.config(text="⏹ 结束阅读", state='normal')
                self.reset_button.config(state='disabled')
                self.status_label.config(text="已重置，点击开始重新阅读")
                print(f"[GUI-DEBUG] 状态：已重置")
            elif self.controller.is_in_question_mode():
                # 答题模式：不要覆盖答题模式下的按钮设置
                print(f"[GUI-DEBUG] 状态：答题模式，保持当前按钮配置")
            elif not is_reading:
                if progress >= 1.0:
                    self.status_label.config(text="阅读完成")
                    # 阅读完成时，保持"结束阅读"按钮可用，让用户能够关闭窗口
                    self.stop_button.config(text="⏹ 结束阅读", state='normal')  # 阅读完成时保持可用
                    self.reset_button.config(state='normal')  # 阅读完成时启用重置，允许用户重新阅读
                    print(f"[GUI-DEBUG] 状态：阅读完成")
                else:
                    self.status_label.config(text="已停止")
                    self.stop_button.config(text="⏹ 结束阅读", state='disabled')  # 已停止时禁用
                    self.reset_button.config(state='disabled')  # 已停止时禁用重置
                    print(f"[GUI-DEBUG] 状态：已停止")
                self.pause_button.config(state='disabled', text="⏸ 暂停")
            elif self.controller.is_paused:
                self.status_label.config(text="已暂停")
                self.pause_button.config(text="▶ 继续", state='normal')
                self.stop_button.config(text="⏹ 结束阅读", state='normal')  # 暂停时保持可用
                self.reset_button.config(state='normal')  # 暂停时启用重置
                print(f"[GUI-DEBUG] 状态：已暂停")
            else:
                self.status_label.config(text=f"正在阅读... ({progress:.1%})")
                self.pause_button.config(text="⏸ 暂停", state='normal')
                self.stop_button.config(text="⏹ 结束阅读", state='normal')  # 阅读中保持可用
                self.reset_button.config(state='disabled')  # 阅读中禁用重置
                print(f"[GUI-DEBUG] 状态：正在阅读 {progress:.1%}")
                
        except tk.TclError:
            # 窗口已关闭
            print(f"[GUI-DEBUG] 窗口已关闭，TclError")
            pass
        except Exception as e:
            print(f"[GUI-DEBUG] 更新显示时发生错误: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[GUI-DEBUG] _update_display_safe 执行完成")
    
    def _auto_enter_question_mode(self):
        """自动进入答题模式"""
        print(f"[GUI-DEBUG] _auto_enter_question_mode 开始执行")
        try:
            # 确保控制器有问题可以显示
            if self.controller.has_questions():
                # 自动进入问题模式
                self.controller.is_question_mode = True
                print(f"[GUI-DEBUG] 设置问题模式标志为True")
                
                # 更新按钮为答题模式
                self._update_buttons_for_individual_quiz()
                
                # 启用滚动（答题时需要滚动）
                self._enable_scrolling()
                
                # 刷新显示
                self._update_display_safe()
                
                print(f"[GUI-DEBUG] 成功进入答题模式")
            else:
                print(f"[GUI-DEBUG] 没有检测到问题，无法进入答题模式")
        except Exception as e:
            print(f"[GUI-DEBUG] 自动进入答题模式时发生错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_fade_effects(self, text: str, char_states: dict):
        """应用渐隐效果到文本"""
        print(f"[GUI-DEBUG] 开始应用渐隐效果")
        
        # 配置渐隐级别的tag样式
        bg_color = self.settings.get('reading', 'background_color', 'white')
        text_color = self.settings.get('reading', 'text_color', 'black')
        
        # 定义渐隐颜色序列 (优化版：减少级别数)
        # 动态根据控制器的fading_levels生成颜色
        fading_levels = getattr(self.controller, 'fading_levels', 2)
        
        if fading_levels <= 2:
            # 简化版：只有3个状态 - normal, fading_1, faded
            fade_colors = [
                text_color,     # normal - 正常黑色
                '#808080',      # fading_1 - 中灰
                bg_color        # faded - 背景色(白色)
            ]
        else:
            # 传统版：支持更多级别（向后兼容）
            fade_colors = [
                text_color,     # normal - 正常黑色
                '#404040',      # fading_1 - 深灰
                '#808080',      # fading_2 - 中灰
                '#B0B0B0',      # fading_3 - 浅灰
                '#D0D0D0',      # fading_4 - 很浅灰
                bg_color        # faded - 背景色(白色)
            ]
        
        # 配置所有渐隐级别的tag
        for i, color in enumerate(fade_colors):
            if i == 0:
                tag_name = 'normal'
            elif i < len(fade_colors) - 1:
                tag_name = f'fading_{i}'
            else:
                tag_name = 'faded'
                
            self.text_display.tag_configure(tag_name, foreground=color)
            print(f"[GUI-DEBUG] 配置tag {tag_name}: {color}")
        
        # 清除之前的所有渐隐标签，避免冲突
        all_fade_tags = ['normal'] + [f'fading_{i}' for i in range(1, len(fade_colors)-1)] + ['faded']
        for tag in all_fade_tags:
            self.text_display.tag_delete(tag)
            self.text_display.tag_configure(tag, foreground=fade_colors[all_fade_tags.index(tag)])
        
        # 将全局字符位置转换为行列位置
        lines = text.split('\n')
        applied_count = 0
        invalid_positions = 0
        
        for pos, state in char_states.items():
            # 计算该位置对应的行和列
            row, col = self._global_pos_to_row_col(pos, lines)
            
            if row < len(lines) and col < len(lines[row]):
                try:
                    # tkinter使用1基索引
                    start_index = f"{row + 1}.{col}"
                    end_index = f"{row + 1}.{col + 1}"
                    
                    self.text_display.tag_add(state, start_index, end_index)
                    applied_count += 1
                    
                    if applied_count <= 5:  # 只显示前几个用于调试
                        print(f"[GUI-DEBUG] 字符位置{pos} -> 行{row+1}列{col}, 状态:{state}")
                        
                except tk.TclError as e:
                    print(f"[GUI-DEBUG] 索引错误: {e}")
                    invalid_positions += 1
            else:
                invalid_positions += 1
                if invalid_positions <= 5:  # 只显示前几个无效位置用于调试
                    print(f"[GUI-DEBUG] 无效位置: {pos} -> 行{row+1}列{col}, 文本行数:{len(lines)}")
        
        print(f"[GUI-DEBUG] 成功应用了 {applied_count} 个字符的渐隐效果，{invalid_positions} 个无效位置")
    
    def _global_pos_to_row_col(self, global_pos: int, lines: list) -> tuple:
        """将全局字符位置转换为行列位置"""
        current_pos = 0
        
        for row, line in enumerate(lines):
            line_length = len(line)
            
            # 检查是否在当前行内
            if current_pos <= global_pos < current_pos + line_length:
                col = global_pos - current_pos
                return row, col
            
            # 移到下一行（+1是为了换行符）
            current_pos += line_length + 1
        
        # 如果位置超出范围，返回最后位置
        if lines:
            return len(lines) - 1, len(lines[-1])
        else:
            return 0, 0
    
    def open_settings(self):
        """打开设置"""
        from gui.settings_window import SettingsWindow
        settings_window = SettingsWindow(self.window, self.settings)
        settings_window.show()
        
        # 设置关闭回调，更新阅读器设置
        def on_settings_close():
            self.controller.set_reading_speed(self.settings.get_int('reading', 'reading_speed', 300))
            self.controller.set_mode(self.settings.get('reading', 'mode', 'line'))
            
            # 设置高性能模式
            high_performance = self.settings.get('reading', 'high_performance_mode', 'True').lower() == 'true'
            self.controller.set_high_performance_mode(high_performance)
            
            # 更新显示样式
            self.text_display.config(
                font=('Microsoft YaHei', self.settings.get_int('reading', 'font_size', 60)),
                bg=self.settings.get('reading', 'background_color', 'white'),
                fg=self.settings.get('reading', 'text_color', 'black')
            )
            
            line_spacing = self.settings.get_float('reading', 'line_spacing', 1.5)
            self.text_display.tag_configure('content', spacing1=10, spacing3=10, 
                                           spacing2=int(line_spacing * 10))
            
            # 重新计算布局参数
            self.update_layout_params()
        
        settings_window.set_close_callback(on_settings_close)
    
    def open_overview(self):
        """打开通览全文窗口"""
        try:
            # 如果正在阅读且未暂停，自动暂停
            was_reading_and_not_paused = self.controller.is_reading and not self.controller.is_paused
            if was_reading_and_not_paused:
                self.pause_reading()
                print(f"[GUI-DEBUG] 自动暂停阅读以打开通览窗口")
            
            overview_window = ArticleOverviewWindow(self.window, self.article, self.settings)
            overview_window.show()
        except Exception as e:
            print(f"[GUI-DEBUG] 打开通览全文窗口时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def on_closing(self):
        """窗口关闭事件"""
        # 检查是否在答题模式
        in_question_mode = self.controller.is_in_question_mode() if hasattr(self.controller, 'is_in_question_mode') else False
        
        # 如果正在阅读或在答题模式，询问确认
        if self.controller.is_reading or in_question_mode:
            if in_question_mode:
                message = "正在答题中，确定要关闭并返回主页吗？"
            else:
                message = "正在阅读中，确定要关闭并返回主页吗？"
                
            if not messagebox.askokcancel("确认关闭", message):
                return
        
        # 清理阅读状态
        try:
            if self.controller.is_reading:
                self.controller.stop_reading()
            
            # 退出答题模式
            if in_question_mode:
                self.controller.exit_question_mode()
        except Exception as e:
            print(f"[GUI-DEBUG] 清理阅读状态时出错: {e}")
        
        # 先显示和恢复主窗口，确保它准备好接收焦点
        if self.parent:
            try:
                self.parent.deiconify()  # 显示主窗口（如果被最小化）
                self.parent.lift()        # 将主窗口置于最前
                self.parent.attributes('-topmost', True)  # 临时置顶
                self.parent.focus_force() # 强制获得焦点
                self.parent.update_idletasks()  # 确保主窗口更新完成
                print(f"[GUI-DEBUG] 主窗口已恢复显示")
                
                # 延迟一点时间确保主窗口完全显示
                self.parent.after(50, lambda: self.parent.attributes('-topmost', False))
                
            except Exception as e:
                print(f"[GUI-DEBUG] 恢复主窗口时出错: {e}")
        
        # 延迟销毁阅读窗口，确保主窗口已经完全显示
        def delayed_destroy():
            try:
                if self.window:
                    self.window.withdraw()  # 先隐藏窗口
                    self.window.after(100, lambda: self.window.destroy() if self.window else None)  # 延迟销毁
                    print(f"[GUI-DEBUG] 阅读窗口已安排销毁")
            except Exception as e:
                print(f"[GUI-DEBUG] 销毁窗口时出错: {e}")
        
        # 延迟执行销毁，给主窗口时间完全显示
        if self.window:
            self.window.after(100, delayed_destroy)
    
    def show(self):
        """显示窗口"""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
    
    def destroy(self):
        """销毁窗口"""
        if self.controller.is_reading:
            self.controller.stop_reading()
        if self.window:
            self.window.destroy()
    
    def _disable_scrolling(self):
        """禁用滚动功能（阅读模式）"""
        # 隐藏滚动条
        self.scrollbar.pack_forget()
        # 禁用滚动事件
        self.text_display.bind("<MouseWheel>", lambda e: "break")
        self.text_display.bind("<Button-4>", lambda e: "break")
        self.text_display.bind("<Button-5>", lambda e: "break")
        self.text_display.bind("<Key>", lambda e: "break")
        self.text_display.bind("<Control-Key>", lambda e: "break")
        print(f"[GUI-DEBUG] 已禁用滚动功能")
    
    def _enable_scrolling(self):
        """启用滚动功能（答题模式）"""
        # 显示滚动条
        self.scrollbar.pack(side='right', fill='y')
        # 恢复滚动事件
        self.text_display.bind("<MouseWheel>", self._on_mousewheel)
        self.text_display.bind("<Button-4>", self._on_mousewheel)
        self.text_display.bind("<Button-5>", self._on_mousewheel)
        # 允许键盘滚动
        self.text_display.unbind("<Key>")
        self.text_display.unbind("<Control-Key>")
        print(f"[GUI-DEBUG] 已启用滚动功能")
    
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        # 根据平台处理滚轮事件
        if event.delta:
            # Windows/Mac
            delta = -1 * (event.delta / 120)
        else:
            # Linux
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                return
        
        self.text_display.yview_scroll(int(delta), "units")
    
    def _display_questions(self):
        """显示问题界面"""
        questions = self.controller.get_questions()
        if not questions:
            return
        
        # 启用滚动功能（答题模式需要滚动）
        self._enable_scrolling()
        
        # 清空问题组件字典
        self.question_widgets.clear()
        self.selected_answers.clear()
        
        # 清空文本显示区域
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        
        # 显示答题标题
        self.text_display.insert(tk.END, f"📝 答题环节\n\n本文共有 {len(questions)} 道题目，请逐题作答：\n\n", 'content')
        
        # 为每道题创建独立的答题界面
        for i, question in enumerate(questions):
            self._create_question_widget(i, question)
        
        self.text_display.config(state='disabled')
        
        # 修改底部按钮为通用功能
        self._update_buttons_for_individual_quiz()
    
    
    def _create_question_widget(self, question_index, question):
        """为每道题创建独立的答题组件"""
        # 插入题目文本
        self.text_display.insert(tk.END, f"【第{question_index + 1}题】", 'content')
        self.text_display.insert(tk.END, f"\n{question.question_text}\n\n", 'content')
        
        if question.question_type == 'cho':
            # 选择题 - 显示选项
            self.text_display.insert(tk.END, f"A. {question.option_a}\n", 'content')
            self.text_display.insert(tk.END, f"B. {question.option_b}\n", 'content')
            self.text_display.insert(tk.END, f"C. {question.option_c}\n", 'content')
            self.text_display.insert(tk.END, f"D. {question.option_d}\n\n", 'content')
            
            # 创建选择按钮框架
            button_frame = ttk.Frame(self.text_display)
            
            # 选择按钮
            ttk.Button(button_frame, text="A", width=3, 
                      command=lambda: self._select_answer(question_index, 'a')).pack(side='left', padx=2)
            ttk.Button(button_frame, text="B", width=3, 
                      command=lambda: self._select_answer(question_index, 'b')).pack(side='left', padx=2)
            ttk.Button(button_frame, text="C", width=3, 
                      command=lambda: self._select_answer(question_index, 'c')).pack(side='left', padx=2)
            ttk.Button(button_frame, text="D", width=3, 
                      command=lambda: self._select_answer(question_index, 'd')).pack(side='left', padx=2)
            
            # 提交和查看答案按钮
            submit_btn = ttk.Button(button_frame, text="💡 查看答案", 
                                   command=lambda: self._show_question_answer(question_index),
                                   state='disabled')
            submit_btn.pack(side='left', padx=(10, 2))
            
            # 状态标签
            status_label = ttk.Label(button_frame, text="请选择答案", foreground='gray')
            status_label.pack(side='left', padx=(10, 0))
            
            # 将按钮框架嵌入到文本中
            self.text_display.window_create(tk.END, window=button_frame)
            
            # 保存组件引用
            self.question_widgets[question_index] = {
                'type': 'cho',
                'button_frame': button_frame,
                'submit_btn': submit_btn,
                'status_label': status_label,
                'question': question
            }
            
        else:
            # 简答题 - 只需要查看解析按钮
            self.text_display.insert(tk.END, "（本题为简答题，无需作答）\n\n", 'content')
            
            button_frame = ttk.Frame(self.text_display)
            
            # 查看解析按钮
            ttk.Button(button_frame, text="💡 查看解析", 
                      command=lambda: self._show_question_answer(question_index)).pack(side='left', padx=2)
            
            # 将按钮框架嵌入到文本中
            self.text_display.window_create(tk.END, window=button_frame)
            
            # 保存组件引用
            self.question_widgets[question_index] = {
                'type': 'ans',
                'button_frame': button_frame,
                'question': question
            }
        
        # 添加分隔线
        self.text_display.insert(tk.END, f"\n{'-'*60}\n\n", 'content')
    
    def _select_answer(self, question_index, choice):
        """选择答案"""
        self.selected_answers[question_index] = choice
        
        # 更新状态显示
        widget_info = self.question_widgets[question_index]
        choice_text = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D'}
        widget_info['status_label'].config(text=f"已选择: {choice_text[choice]}", foreground='blue')
        
        # 启用查看答案按钮
        widget_info['submit_btn'].config(state='normal')
    
    def _show_question_answer(self, question_index):
        """显示单个问题的答案和解析"""
        widget_info = self.question_widgets[question_index]
        question = widget_info['question']
        
        # 禁用当前题目的按钮
        for child in widget_info['button_frame'].winfo_children():
            if isinstance(child, ttk.Button):
                child.config(state='disabled')
        
        # 准备结果文本
        result_text = "\n🔍 答案解析：\n"
        
        if question.question_type == 'cho':
            # 选择题显示对错
            user_answer = self.selected_answers.get(question_index, '')
            correct_answer = question.correct_answer
            
            if user_answer == correct_answer:
                result_text += f"✅ 回答正确！您选择了{user_answer.upper()}，正确答案是{correct_answer.upper()}\n"
                widget_info['status_label'].config(text="✅ 回答正确！", foreground='green')
            else:
                result_text += f"❌ 回答错误！您选择了{user_answer.upper()}，正确答案是{correct_answer.upper()}\n"
                widget_info['status_label'].config(text="❌ 回答错误！", foreground='red')
        
        result_text += f"💡 解析：{question.explanation}\n"
        
        # 在当前题目后插入解析
        self.text_display.config(state='normal')
        # 找到当前题目的结束位置并插入解析
        current_pos = self.text_display.search(f"【第{question_index + 1}题】", 1.0, tk.END)
        if current_pos:
            # 找到下一个分隔线的位置
            next_separator = self.text_display.search("-"*60, current_pos, tk.END)
            if next_separator:
                # 在分隔线前插入解析
                self.text_display.insert(next_separator, result_text)
        
        self.text_display.config(state='disabled')
    
    def _update_buttons_for_individual_quiz(self):
        """更新底部按钮为独立答题模式"""
        # 答题模式只显示两个按钮
        self.pause_button.config(text="📖 通览全文", command=self.open_overview, state='normal')
        self.stop_button.config(text="❌ 关闭训练", command=self._finish_training, state='normal')
        self.reset_button.config(text="", command=lambda: None, state='disabled')  # 隐藏第三个按钮
        self.reset_button.pack_forget()  # 完全隐藏第三个按钮
        
        # 隐藏固定的通览全文按钮以避免重复
        self.overview_button.pack_forget()
        
        self.status_label.config(text="请逐题作答，完成后可关闭训练")
    
    def _show_quiz_summary(self):
        """显示答题总结"""
        questions = self.controller.get_questions()
        if not questions:
            return
        
        # 计算成绩
        total_questions = len(questions)
        choice_questions = [q for q in questions if q.question_type == 'cho']
        correct_count = 0
        
        for i, question in enumerate(questions):
            if question.question_type == 'cho':
                user_answer = self.selected_answers.get(i, '')
                if user_answer == question.correct_answer:
                    correct_count += 1
        
        # 显示成绩总结
        if choice_questions:
            score_percentage = (correct_count / len(choice_questions)) * 100
            summary_text = f"\n\n📊 答题总结\n"
            summary_text += f"选择题正确率: {correct_count}/{len(choice_questions)} ({score_percentage:.1f}%)\n"
            summary_text += f"总题目数: {total_questions} 题\n"
            
            if score_percentage >= 80:
                summary_text += "🎉 表现优秀！"
            elif score_percentage >= 60:
                summary_text += "👍 表现良好！"
            else:
                summary_text += "💪 继续努力！"
        else:
            summary_text = f"\n\n📊 答题完成\n已查看 {total_questions} 道题目的解析"
        
        # 在文本末尾添加总结
        self.text_display.config(state='normal')
        self.text_display.insert(tk.END, summary_text, 'content')
        self.text_display.config(state='disabled')
        
        # 更新底部按钮为完成状态
        self._reset_buttons_after_quiz()
    
    def _reset_buttons_after_quiz(self):
        """答题结束后重置按钮"""
        # 禁用滚动功能（回到阅读模式状态）
        self._disable_scrolling()
        
        # 答题完成后也只显示两个按钮
        self.pause_button.config(text="📖 通览全文", command=self.open_overview, state='normal')
        self.stop_button.config(text="❌ 关闭训练", command=self._finish_training, state='normal')
        self.reset_button.config(text="", command=lambda: None, state='disabled')  # 隐藏第三个按钮
        self.reset_button.pack_forget()  # 完全隐藏第三个按钮
        
        # 隐藏固定的通览全文按钮以避免重复
        self.overview_button.pack_forget()
        
        self.status_label.config(text="训练完成 - 可以通览全文或关闭训练")
    
    def _finish_training(self):
        """完成训练，关闭窗口返回主页"""
        # 清理阅读状态（不需要确认，因为用户主动选择完成）
        try:
            if self.controller.is_reading:
                self.controller.stop_reading()
            
            # 退出答题模式
            if hasattr(self.controller, 'is_in_question_mode') and self.controller.is_in_question_mode():
                self.controller.exit_question_mode()
        except Exception as e:
            print(f"[GUI-DEBUG] 清理阅读状态时出错: {e}")
        
        # 先显示和恢复主窗口，确保它准备好接收焦点
        if self.parent:
            try:
                self.parent.deiconify()  # 显示主窗口（如果被最小化）
                self.parent.lift()        # 将主窗口置于最前
                self.parent.attributes('-topmost', True)  # 临时置顶
                self.parent.focus_force() # 强制获得焦点
                self.parent.update_idletasks()  # 确保主窗口更新完成
                print(f"[GUI-DEBUG] 训练完成，主窗口已恢复显示")
                
                # 延迟一点时间确保主窗口完全显示
                self.parent.after(50, lambda: self.parent.attributes('-topmost', False))
                
            except Exception as e:
                print(f"[GUI-DEBUG] 恢复主窗口时出错: {e}")
        
        # 延迟销毁阅读窗口，确保主窗口已经完全显示
        def delayed_destroy():
            try:
                if self.window:
                    self.window.withdraw()  # 先隐藏窗口
                    self.window.after(100, lambda: self.window.destroy() if self.window else None)  # 延迟销毁
                    print(f"[GUI-DEBUG] 训练窗口已安排销毁")
            except Exception as e:
                print(f"[GUI-DEBUG] 销毁窗口时出错: {e}")
        
        # 延迟执行销毁，给主窗口时间完全显示
        if self.window:
            self.window.after(100, delayed_destroy) 