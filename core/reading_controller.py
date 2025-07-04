"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 阅读控制器
"""
import time
import threading
from typing import Optional, Callable, List, Dict, Tuple
from core.article_parser import Article

class ReadingController:
    def __init__(self):
        self.current_article: Optional[Article] = None
        self.pages: List[List[str]] = []
        self.current_page = 0
        self.current_line_in_page = 0
        self.chars_in_current_line = 0
        self.lines_per_page = 10
        self.reading_speed = 300  # 字符/分钟
        self.mode = 'line'  # 'line' 或 'page'
        self.is_reading = False
        self.is_paused = False
        self.reading_thread: Optional[threading.Thread] = None
        self.update_callback: Optional[Callable] = None
        
        # 新增：字符状态管理
        self.char_states: Dict[Tuple[int, int, int], str] = {}  # (page, line, char) -> state
        self.fading_levels = 2  # 优化：减少渐隐级别数从5降到2
        
        # 新增：批量更新相关
        self.batch_update_interval = 0.05  # 批量更新间隔（秒）
        self.pending_updates = False  # 是否有待处理的更新
        self.batch_timer = None  # 批量更新定时器
        
        # 新增：动态布局相关
        self.max_line_length = 40  # 每行最大字符数
        self.pause_resume_char_states = {}  # 暂停时保存的字符状态
        
        # 新增：问题模式相关
        self.is_question_mode = False  # 是否处于问题模式
        self.reading_finished = False  # 阅读是否完成
        
        # 新增：线程安全和状态保护
        self._state_lock = threading.Lock()  # 状态访问锁
        self._absolute_char_states: Dict[int, str] = {}  # 基于绝对字符位置的状态
        self._absolute_position = 0  # 当前阅读的绝对字符位置
        
        # 新增：page模式页面内进度追踪
        self.page_reading_start_time = 0.0  # 当前页面开始阅读的时间
        self.page_reading_duration = 0.0  # 当前页面计划的阅读时间
        
        # 智能分页参数
        self.text_widget = None  # 用于测量文本高度的控件引用
        self.available_height = 800  # 可用显示高度（像素）
        self.font_size = 14  # 字体大小
        self.line_spacing = 1.5  # 行间距
    
    def set_article(self, article: Article):
        """设置要阅读的文章"""
        print(f"[DEBUG] 设置文章: {article.title}")
        self.current_article = article
        self.reset_position()
        self._create_pages()
        lines = article.original_content.split('\n')
        print(f"[DEBUG] 文章总行数: {len(lines)}")
        
    def set_lines_per_page(self, lines_per_page: int):
        """设置每页行数"""
        self.lines_per_page = lines_per_page
        print(f"[DEBUG] 设置每页行数: {lines_per_page}")
        if self.current_article:
            # 保存当前进度
            current_progress = self.get_progress()
            print(f"[DEBUG] 保存当前进度: {current_progress:.1%}")
            
            self._create_pages()
            
            # 恢复到相应的进度位置
            if current_progress > 0:
                self._restore_reading_position_by_progress(current_progress)
                print(f"[DEBUG] 恢复到进度: {current_progress:.1%}")
    
    def set_max_line_length(self, max_length: int):
        """设置每行最大字符数并重新分页"""
        if self.max_line_length != max_length:
            self.max_line_length = max_length
            print(f"[DEBUG] 设置最大行长度: {max_length}")
            if self.current_article:
                self._reformat_and_repaginate()
    
    def _reformat_and_repaginate(self):
        """重新格式化并分页（保持当前阅读进度）"""
        if not self.current_article:
            return
        
        print(f"[DEBUG] 重新格式化并分页开始")
        
        # 保存当前阅读进度
        current_progress = self.get_progress()
        print(f"[DEBUG] 当前进度: {current_progress:.1%}")
        
        # 保存绝对位置状态（这些在重新分页后仍然有效）
        with self._state_lock:
            preserved_absolute_states = self._absolute_char_states.copy()
            preserved_relative_states = self.char_states.copy()
            current_absolute_pos = self._absolute_position
            print(f"[DEBUG] 保存了 {len(preserved_absolute_states)} 个绝对位置状态")
            print(f"[DEBUG] 保存了 {len(preserved_relative_states)} 个相对位置状态")
            print(f"[DEBUG] 当前绝对位置: {current_absolute_pos}")
        
        # 记录重分页前的页面结构
        old_pages_info = [(i, len(page)) for i, page in enumerate(self.pages)]
        print(f"[DEBUG] 重分页前页面结构: {old_pages_info}")
        
        # 重新创建页面
        self._create_pages()
        
        # 记录重分页后的页面结构
        new_pages_info = [(i, len(page)) for i, page in enumerate(self.pages)]
        print(f"[DEBUG] 重分页后页面结构: {new_pages_info}")
        
        # 恢复阅读位置
        self._restore_reading_position(current_progress)
        
        # 恢复绝对位置状态（关键：这确保了渐隐状态在布局变化后保持）
        with self._state_lock:
            # 清除旧状态
            self.char_states.clear()
            self._absolute_char_states.clear()
            
            # 恢复绝对位置状态
            self._absolute_char_states = preserved_absolute_states
            
            # 验证状态一致性：检查一些关键的绝对位置是否仍然有效
            valid_states = 0
            invalid_states = 0
            for abs_pos, state in preserved_absolute_states.items():
                # 简单验证：绝对位置应该在合理范围内
                total_chars = sum(len(line) for page in self.pages for line in page)
                if 0 <= abs_pos < total_chars:
                    valid_states += 1
                else:
                    invalid_states += 1
                    # 删除无效的绝对位置状态
                    if abs_pos in self._absolute_char_states:
                        del self._absolute_char_states[abs_pos]
            
            print(f"[DEBUG] 状态验证: {valid_states} 个有效, {invalid_states} 个无效已清除")
            print(f"[DEBUG] 最终恢复了 {len(self._absolute_char_states)} 个绝对位置状态")
        
        # 额外的状态清理和验证
        self._validate_and_cleanup_states()
        
        print(f"[DEBUG] 重新分页完成: {len(self.pages)} 页")
    
    def _restore_reading_position(self, target_progress: float):
        """根据进度恢复阅读位置"""
        if target_progress <= 0 or not self.pages:
            return
        
        # 计算总字符数
        total_chars = sum(len(line) for page in self.pages for line in page)
        target_chars = int(total_chars * target_progress)
        
        # 重新定位到相应位置
        current_chars = 0
        for page_idx, page in enumerate(self.pages):
            for line_idx, line in enumerate(page):
                if current_chars + len(line) >= target_chars:
                    self.current_page = page_idx
                    self.current_line_in_page = line_idx
                    self.chars_in_current_line = max(0, target_chars - current_chars)
                    print(f"[DEBUG] 恢复位置: 页{page_idx}, 行{line_idx}, 字符{self.chars_in_current_line}")
                    return
                current_chars += len(line)
        
        # 如果没找到合适位置，设置到最后
        if self.pages:
            self.current_page = len(self.pages) - 1
            self.current_line_in_page = len(self.pages[-1]) - 1
            self.chars_in_current_line = len(self.pages[-1][-1]) if self.pages[-1] else 0
    
    def _create_pages(self):
        """创建分页 - 使用智能分页算法"""
        if not self.current_article:
            return
        
        print(f"[DEBUG] 开始智能分页")
        
        # 如果有文本控件引用，使用智能分页
        if self.text_widget and hasattr(self, 'available_height'):
            self._create_pages_smart()
        else:
            # 否则使用传统的固定行数分页
            self._create_pages_traditional()

    def _create_pages_traditional(self):
        """传统的固定行数分页方法"""
        print(f"[DEBUG] 使用传统分页，每页 {self.lines_per_page} 行")
        self.pages = []
        current_page = []
        
        # 使用原始内容而不是重新格式化的内容，保持自然段落结构
        if not self.current_article:
            return
        lines = self.current_article.original_content.split('\n')
        for line in lines:
            current_page.append(line)
            if len(current_page) >= self.lines_per_page:
                self.pages.append(current_page)
                current_page = []
        
        # 添加最后一页（如果有剩余行）
        if current_page:
            self.pages.append(current_page)
        
        print(f"[DEBUG] 传统分页完成: {len(self.pages)} 页")
        for i, page in enumerate(self.pages):
            print(f"[DEBUG]   第{i+1}页: {len(page)} 行")

    def _create_pages_smart(self):
        """智能分页：基于实际渲染高度而不是固定行数"""
        if not self.text_widget:
            print(f"[DEBUG] 智能分页失败：缺少文本控件引用，回退到传统分页")
            self._create_pages_traditional()
            return
            
        print(f"[DEBUG] 开始智能分页，可用高度: {self.available_height}px")
        
        self.pages = []
        if not self.current_article:
            return
        lines = self.current_article.original_content.split('\n')
        
        if not lines:
            print(f"[DEBUG] 没有内容行，创建空页面")
            return
        
        current_page = []
        current_height = 0
        
        # 测量单行高度（包括行间距）
        line_height = self._measure_line_height()
        print(f"[DEBUG] 测量到的行高: {line_height}px")
        
        # 使用传入的可用高度，但要更保守一些
        # 预留更多空间来应对测量误差和tag样式的影响
        safety_margin = 120  # 增加更多安全边距，确保最后一行有足够空间
        usable_height = max(100, self.available_height - safety_margin)
        print(f"[DEBUG] 实际可用高度: {usable_height}px (预留{safety_margin}px安全边距)")
        
        for i, line in enumerate(lines):
            # 测量这一行的实际高度
            line_render_height = self._measure_text_height(line, line_height)
            
            # 检查添加这一行是否会超出可用高度
            if current_height + line_render_height > usable_height and current_page:
                # 超出高度且当前页不为空，创建新页面
                self.pages.append(current_page)
                print(f"[DEBUG] 创建第{len(self.pages)}页，包含{len(current_page)}行，高度约{current_height:.1f}px")
                current_page = [line]
                current_height = line_render_height
            else:
                # 可以添加到当前页
                current_page.append(line)
                current_height += line_render_height
            
            # 检查段落边界优化
            if self._should_prefer_page_break_here(lines, i):
                # 在段落边界处，如果当前页已经使用了足够的高度，就结束当前页
                height_usage_ratio = current_height / usable_height
                if height_usage_ratio > 0.75 and current_page:  # 使用75%的阈值，更保守
                    self.pages.append(current_page)
                    print(f"[DEBUG] 在段落边界创建第{len(self.pages)}页（优化），包含{len(current_page)}行，使用率{height_usage_ratio:.1%}")
                    current_page = []
                    current_height = 0
        
        # 添加最后一页
        if current_page:
            self.pages.append(current_page)
            print(f"[DEBUG] 创建最后第{len(self.pages)}页，包含{len(current_page)}行，高度约{current_height:.1f}px")
        
        print(f"[DEBUG] 智能分页完成: {len(self.pages)} 页")
        
        # 验证分页结果
        total_lines = sum(len(page) for page in self.pages)
        original_lines = len(lines)
        if total_lines != original_lines:
            print(f"[WARNING] 分页行数不匹配: 原始{original_lines}行，分页后{total_lines}行")
        else:
            print(f"[DEBUG] 分页验证通过: {total_lines}行")
        
        # 输出每页的详细信息用于调试
        for i, page in enumerate(self.pages):
            page_height = sum(self._measure_text_height(line, line_height) for line in page)
            print(f"[DEBUG] 第{i+1}页: {len(page)}行, 预计高度{page_height:.1f}px, 利用率{page_height/usable_height:.1%}")
            
            # 额外验证：检查是否有过长的页面
            if page_height > usable_height:
                print(f"[WARNING] 第{i+1}页可能过高！预计{page_height:.1f}px > 可用{usable_height}px")

    def _measure_line_height(self) -> float:
        """测量单行文本的高度"""
        if not self.text_widget:
            return self.font_size * self.line_spacing
        
        try:
            # 临时插入测试文本来测量行高
            self.text_widget.config(state='normal')
            original_content = self.text_widget.get(1.0, 'end-1c')
            
            # 清空并插入测试文本，使用更多行来提高测量精度
            # 重要：要应用'content' tag来获得正确的间距
            test_lines = ["测试行一", "测试行二", "测试行三", "测试行四", "测试行五"]
            test_text = '\n'.join(test_lines)
            self.text_widget.delete(1.0, 'end')
            self.text_widget.insert(1.0, test_text, 'content')  # 应用content tag
            self.text_widget.update_idletasks()
            
            # 测量第一行和最后一行的位置差，计算平均行高
            bbox_first = self.text_widget.bbox("1.0")
            bbox_last = self.text_widget.bbox(f"{len(test_lines)}.0")
            
            line_height = self.font_size * self.line_spacing  # 默认值
            
            if bbox_first and bbox_last:
                total_height = bbox_last[1] - bbox_first[1]
                measured_height = total_height / (len(test_lines) - 1)  # 实际行间距离
                if measured_height > 0:
                    line_height = measured_height
                    print(f"[DEBUG] 实际测量行高: {line_height:.1f}px (基于{len(test_lines)-1}行间距，包含tag样式)")
                else:
                    print(f"[DEBUG] 测量结果无效，使用估算行高: {line_height}px")
            else:
                print(f"[DEBUG] 无法获取bbox，使用估算行高: {line_height}px")
            
            # 恢复原内容
            self.text_widget.delete(1.0, 'end')
            self.text_widget.insert(1.0, original_content)
            self.text_widget.config(state='disabled')
            
            return line_height
            
        except Exception as e:
            print(f"[DEBUG] 测量行高时出错: {e}，使用估算值")
            return self.font_size * self.line_spacing

    def _measure_text_height(self, text: str, base_line_height: float) -> float:
        """测量特定文本的渲染高度"""
        if not text.strip():
            # 空行或仅包含空白字符的行，使用较小的高度
            return base_line_height * 0.3  # 进一步减少空行高度
        
        # 检查是否是段落开始（有缩进）
        is_paragraph_start = text.startswith("    ") or text.startswith("\t")
        
        # 对于非空行，考虑文本换行的可能性
        estimated_height = base_line_height
        
        # 如果文本很长，可能会自动换行，需要更多高度
        if len(text) > self.max_line_length:
            # 估算可能的换行行数，并添加额外的安全系数
            estimated_lines = (len(text) + self.max_line_length - 1) // self.max_line_length
            # 为自动换行添加10%的安全系数，因为实际换行可能不完全按字符数切分
            estimated_height = base_line_height * estimated_lines * 1.1
        
        # 如果是段落开始，需要考虑额外的段落间距
        # 基于GUI中的tag配置：spacing1=10, spacing3=10, spacing2基于行间距
        if is_paragraph_start:
            # 段落前后各10px + 行间距的额外空间
            extra_spacing = 20 + (self.line_spacing - 1.0) * self.font_size * 0.5
            estimated_height += extra_spacing
            
        return estimated_height

    def _should_prefer_page_break_here(self, lines: list, line_index: int) -> bool:
        """判断是否应该在此处优先分页"""
        if line_index >= len(lines) - 1:
            return False
        
        current_line = lines[line_index]
        next_line = lines[line_index + 1] if line_index + 1 < len(lines) else ""
        
        # 如果当前行是空行，且下一行不是空行，优先在此处分页
        if not current_line.strip() and next_line.strip():
            return True
        
        # 如果下一行是段落开始（有缩进），优先在此处分页
        if next_line.startswith("    ") or next_line.startswith("\t"):
            return True
        
        return False

    def set_reading_speed(self, speed: int):
        """设置阅读速度（字符/分钟）"""
        self.reading_speed = max(60, min(1200, speed))  # 限制在合理范围内
        print(f"[DEBUG] 设置阅读速度为: {self.reading_speed} 字符/分钟")

    def set_mode(self, mode: str):
        """设置阅读模式"""
        if mode in ['line', 'page']:
            self.mode = mode
            print(f"[DEBUG] 设置阅读模式为: {mode}")
    
    def set_high_performance_mode(self, enabled: bool):
        """设置高性能模式"""
        if enabled:
            self.fading_levels = 2  # 高效模式：减少渐隐级别
            self.batch_update_interval = 0.08  # 稍微增加批量更新间隔
            print(f"[DEBUG] 启用高性能模式：渐隐级别={self.fading_levels}, 批量更新间隔={self.batch_update_interval}s")
        else:
            self.fading_levels = 4  # 传统模式：更多渐隐级别
            self.batch_update_interval = 0.03  # 更频繁的更新
            print(f"[DEBUG] 禁用高性能模式：渐隐级别={self.fading_levels}, 批量更新间隔={self.batch_update_interval}s")

    def set_update_callback(self, callback: Callable):
        """设置更新显示的回调函数"""
        self.update_callback = callback
        print(f"[DEBUG] 设置更新回调函数")

    def reset_position(self):
        """重置阅读位置"""
        print(f"[DEBUG] 重置阅读位置")
        with self._state_lock:
            self.current_page = 0
            self.current_line_in_page = 0
            self.chars_in_current_line = 0
            self.char_states.clear()  # 清除所有字符状态
            self.pause_resume_char_states.clear()  # 清除暂停状态
            self._absolute_char_states.clear()  # 清除绝对位置状态
            self._absolute_position = 0  # 重置绝对位置
        self.is_question_mode = False  # 重置问题模式
        self.reading_finished = False  # 重置阅读完成状态
        # 重置page模式页面内进度追踪
        self.page_reading_start_time = 0.0
        self.page_reading_duration = 0.0
        if self.current_article:
            self._create_pages()
        print(f"[DEBUG] 分页完成: {len(self.pages)} 页")
    
    def _restore_reading_position_by_progress(self, target_progress: float):
        """根据进度百分比恢复阅读位置，特别适用于page模式"""
        if target_progress <= 0 or not self.pages:
            return
        
        if self.mode == 'page':
            # Page模式：根据进度恢复到相应的页面
            target_page = int(target_progress * len(self.pages))
            target_page = min(target_page, len(self.pages) - 1)  # 确保不超出范围
            self.current_page = target_page
            self.current_line_in_page = 0
            self.chars_in_current_line = 0
            print(f"[DEBUG] Page模式恢复到第{target_page}页")
        else:
            # Line模式：使用原有的字符级精确恢复
            self._restore_reading_position(target_progress)

    def start_reading(self):
        """开始阅读"""
        if self.is_reading:
            return
        
        print(f"[DEBUG] 开始阅读，模式: {self.mode}")
        
        # 重置阅读完成和问题模式标志
        self.reading_finished = False
        self.is_question_mode = False
        print(f"[DEBUG] 重置阅读状态标志：reading_finished=False, is_question_mode=False")
        
        # Page模式的额外验证
        if self.mode == 'page':
            if not self.pages:
                print(f"[DEBUG] Page模式：没有页面数据，无法开始阅读")
                return
            
            # 确保当前页位置有效
            if self.current_page >= len(self.pages):
                print(f"[DEBUG] Page模式：当前页{self.current_page}超出范围{len(self.pages)}，重置到0")
                self.current_page = 0
            
            print(f"[DEBUG] Page模式验证通过：当前页{self.current_page}/{len(self.pages)}")
        
        self.is_reading = True
        self.is_paused = False
        
        # 启动阅读线程
        if self.mode == 'line':
            self.reading_thread = threading.Thread(target=self._line_reading_loop_with_fade)
        else:
            self.reading_thread = threading.Thread(target=self._page_reading_loop)
        
        self.reading_thread.daemon = True
        self.reading_thread.start()
        print(f"[DEBUG] 阅读线程已启动")

    def pause_reading(self):
        """暂停/继续阅读"""
        with self._state_lock:
            if self.is_paused:
                # 恢复阅读
                self.is_paused = False
                print(f"[DEBUG] 恢复阅读")
                
                # 如果有保存的暂停状态，恢复它们
                if self.pause_resume_char_states:
                    self.char_states.update(self.pause_resume_char_states)
                    self.pause_resume_char_states.clear()
                    print(f"[DEBUG] 恢复了 {len(self.char_states)} 个相对位置字符状态")
            else:
                # 暂停阅读
                self.is_paused = True
                print(f"[DEBUG] 暂停阅读")
                
                # 保存当前渐隐状态，用于恢复时继续处理
                self.pause_resume_char_states = self.char_states.copy()
                print(f"[DEBUG] 保存了 {len(self.pause_resume_char_states)} 个相对位置字符状态")
                print(f"[DEBUG] 当前有 {len(self._absolute_char_states)} 个绝对位置字符状态")

    def stop_reading(self):
        """停止阅读"""
        print(f"[DEBUG] 停止阅读")
        self.is_reading = False
        self.is_paused = False
        
        # 清理批量更新定时器
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None
        self.pending_updates = False
        
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join(timeout=1.0)
            print(f"[DEBUG] 阅读线程已停止")

    def _line_reading_loop_with_fade(self):
        """逐行阅读循环 - 带渐隐效果"""
        loop_count = 0
        
        while self.is_reading:
            loop_count += 1
            print(f"[DEBUG] 循环#{loop_count}: 页{self.current_page}, 行{self.current_line_in_page}, 字符{self.chars_in_current_line}")
            
            # 暂停检查
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            # 检查是否已完成所有页面
            if self.current_page >= len(self.pages):
                print(f"[DEBUG] 阅读完成，退出循环")
                break
            
            # 检查是否需要移到下一页
            if self.current_line_in_page >= len(self.pages[self.current_page]):
                print(f"[DEBUG] 当前页完成，移到下一页")
                # 清除当前页的字符状态
                self._clear_current_page_states()
                
                self.current_page += 1
                self.current_line_in_page = 0
                self.chars_in_current_line = 0
                
                if self.update_callback:
                    print(f"[DEBUG] 调用更新回调 (换页)")
                    self.update_callback()
                time.sleep(0.5)  # 换页暂停
                continue
            
            # 获取当前行文本
            current_line_text = self.pages[self.current_page][self.current_line_in_page]
            print(f"[DEBUG] 当前行文本: {repr(current_line_text[:30])}... (长度:{len(current_line_text)})")
            
            # 如果是空行，直接跳到下一行
            if not current_line_text.strip():
                print(f"[DEBUG] 空行，跳到下一行")
                self.current_line_in_page += 1
                self.chars_in_current_line = 0
                if self.update_callback:
                    print(f"[DEBUG] 调用更新回调 (空行)")
                    self.update_callback()
                time.sleep(0.3)
                continue
            
            # 如果当前行已经全部处理完成，移到下一行
            if self.chars_in_current_line >= len(current_line_text):
                print(f"[DEBUG] 当前行完成，移到下一行")
                self.current_line_in_page += 1
                self.chars_in_current_line = 0
                if self.update_callback:
                    print(f"[DEBUG] 调用更新回调 (行完成)")
                    self.update_callback()
                time.sleep(0.2)
                continue
            
            # 计算当前字符的绝对位置
            with self._state_lock:
                absolute_pos = self._calculate_absolute_position(
                    self.current_page, self.current_line_in_page, self.chars_in_current_line
                )
                self._absolute_position = absolute_pos
            
            # 处理当前字符的渐隐效果
            char_key = (self.current_page, self.current_line_in_page, self.chars_in_current_line)
            current_char = current_line_text[self.chars_in_current_line]
            
            # 使用绝对位置检查字符状态，线程安全
            with self._state_lock:
                current_state = self._absolute_char_states.get(absolute_pos, 'normal')
            
            start_fade_level = 0
            
            # 如果字符已经有状态，从对应级别开始
            if current_state != 'normal':
                if current_state == 'faded':
                    # 已经完全消失，跳到下一个字符
                    self.chars_in_current_line += 1
                    continue
                elif current_state.startswith('fading_'):
                    try:
                        start_fade_level = int(current_state.split('_')[1]) + 1
                        print(f"[DEBUG] 从渐隐级别 {start_fade_level} 继续字符 '{current_char}' (绝对位置{absolute_pos})")
                    except:
                        start_fade_level = 0
            
            # 优化：计算渐隐时间，考虑减少的级别数
            # 总时间保持不变，但分配给更少的级别
            total_fade_time = 60.0 / self.reading_speed
            char_delay = total_fade_time / max(1, self.fading_levels)
            
            # 执行完整的渐隐过程，确保不被中断
            success = self._fade_character_complete(absolute_pos, char_key, current_char, start_fade_level, char_delay)
            
            if success:
                # 移到下一个字符
                self.chars_in_current_line += 1
            else:
                # 如果渐隐被中断（比如停止阅读），退出循环
                print(f"[DEBUG] 字符渐隐被中断，退出循环")
                break
            
            # 每100次循环检查一次，避免无限循环
            if loop_count % 100 == 0:
                print(f"[DEBUG] 已执行{loop_count}次循环，当前状态检查...")
                if loop_count > 10000:  # 防止真的无限循环
                    print(f"[DEBUG] 循环次数过多，强制退出")
                    break
        
        # 阅读结束
        print(f"[DEBUG] 阅读循环结束，总循环次数: {loop_count}")
        self.is_reading = False
        self.reading_finished = True
        
        # 不要在这里立即进入问题模式，让GUI控制何时进入
        # 阅读完成后应该先显示完成信息，然后再考虑是否进入答题
        
        if self.update_callback:
            print(f"[DEBUG] 调用最终更新回调")
            self.update_callback()
    
    def _clear_current_page_states(self):
        """清除当前页的所有字符状态"""
        with self._state_lock:
            # 清除相对位置状态
            keys_to_remove = [key for key in self.char_states.keys() if key[0] == self.current_page]
            for key in keys_to_remove:
                del self.char_states[key]
            print(f"[DEBUG] 清除了当前页 {len(keys_to_remove)} 个相对位置字符状态")
            
            # 清除对应的绝对位置状态（为了内存管理）
            if self.current_page < len(self.pages):
                page_lines = self.pages[self.current_page]
                
                # 计算当前页第一个字符的绝对位置
                page_start_abs = self._calculate_absolute_position(self.current_page, 0, 0)
                
                # 计算当前页最后一个字符的绝对位置
                last_line_idx = len(page_lines) - 1
                last_char_idx = len(page_lines[last_line_idx]) - 1 if page_lines[last_line_idx] else 0
                page_end_abs = self._calculate_absolute_position(self.current_page, last_line_idx, last_char_idx) + 1
                
                abs_keys_to_remove = [
                    abs_pos for abs_pos in self._absolute_char_states.keys() 
                    if page_start_abs <= abs_pos < page_end_abs
                ]
                for abs_key in abs_keys_to_remove:
                    del self._absolute_char_states[abs_key]
                print(f"[DEBUG] 清除了当前页 {len(abs_keys_to_remove)} 个绝对位置字符状态 (范围: {page_start_abs}-{page_end_abs})")

    def _page_reading_loop(self):
        """按页阅读循环 - 整页消失模式，支持实时进度更新"""
        print(f"[DEBUG] Page模式阅读循环开始: 当前页{self.current_page}, 总页数{len(self.pages)}")
        
        # 额外的安全检查：确保当前页位置有效
        if self.current_page >= len(self.pages):
            print(f"[DEBUG] Page模式：当前页{self.current_page}超出范围，重置到0")
            self.current_page = 0
        
        loop_count = 0
        while self.is_reading and self.current_page < len(self.pages):
            loop_count += 1
            if loop_count % 50 == 0:  # 每50次循环记录一次状态
                print(f"[DEBUG] Page模式循环#{loop_count}: 页{self.current_page}/{len(self.pages)}")
            
            # 暂停检查
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            # 再次检查页面是否有效（防止运行时页面数量变化）
            if self.current_page >= len(self.pages):
                print(f"[DEBUG] Page模式：运行时检测到页面超出范围{self.current_page}>={len(self.pages)}，退出")
                break
            
            # 计算当前页的文本长度
            current_page_lines = self.pages[self.current_page]
            page_text = '\n'.join(current_page_lines)
            char_count = len([c for c in page_text if c.strip()])  # 只计算非空白字符
            
            # 计算页面停留时间（最少2秒，最多20秒）
            page_duration = max(2.0, min(20.0, (char_count * 60.0) / self.reading_speed))
            
            # 设置页面阅读进度追踪
            self.page_reading_start_time = time.time()
            self.page_reading_duration = page_duration
            
            if loop_count <= 3 or loop_count % 20 == 0:  # 只在开始和偶尔记录详细信息
                print(f"[DEBUG] 页面 {self.current_page + 1}/{len(self.pages)} 停留时间: {page_duration:.1f}秒, 字符数: {char_count}")
            
            # 显示当前页
            if self.update_callback:
                self.update_callback()
            
            # 等待页面时间，期间定期更新进度
            start_time = time.time()
            update_interval = 0.2  # 每0.2秒更新一次进度
            last_update_time = start_time
            
            while (time.time() - start_time < page_duration and 
                   self.is_reading and not self.is_paused):
                
                current_time = time.time()
                
                # 定期更新进度条和剩余时间
                if current_time - last_update_time >= update_interval:
                    if self.update_callback:
                        self.update_callback()
                    last_update_time = current_time
                
                time.sleep(0.1)  # 减少sleep时间以提高更新频率
                
                # 额外的安全检查：在等待期间如果页面数量发生变化，立即退出
                if self.current_page >= len(self.pages):
                    print(f"[DEBUG] Page模式：等待期间检测到页面变化，退出等待")
                    break
            
            # 页面阅读完成，清除进度追踪
            self.page_reading_start_time = 0.0
            self.page_reading_duration = 0.0
            
            # 移到下一页
            if self.is_reading and self.current_page < len(self.pages):
                self.current_page += 1
                # 立即更新显示以显示下一页或空白页
                if self.update_callback:
                    self.update_callback()
                time.sleep(0.3)  # 页间暂停
        
        # 阅读结束
        print(f"[DEBUG] Page模式阅读循环结束: 总循环{loop_count}次，最终页{self.current_page}")
        self.is_reading = False
        self.reading_finished = True
        
        # 清除进度追踪
        self.page_reading_start_time = 0.0
        self.page_reading_duration = 0.0
        
        # 不要在这里立即进入问题模式，让GUI控制何时进入
        # 阅读完成后应该先显示完成信息，然后再考虑是否进入答题
        
        if self.update_callback:
            self.update_callback()
    
    def get_current_display_text_with_states(self) -> Tuple[str, Dict[int, str]]:
        """获取当前应该显示的文本和字符状态信息
        
        Returns:
            tuple: (显示文本, {字符位置: 状态})
        """
        print(f"[DEBUG] get_current_display_text_with_states 被调用")
        
        if not self.current_article or not self.pages:
            print(f"[DEBUG] 没有文章或页面数据，返回空字符串")
            return "", {}
        
        # 如果已读完所有页面，返回空白
        if self.current_page >= len(self.pages):
            print(f"[DEBUG] 已读完所有页面 (当前页{self.current_page} >= 总页数{len(self.pages)})，返回空字符串")
            return "", {}
        
        current_page_lines = self.pages[self.current_page]
        print(f"[DEBUG] 当前页{self.current_page}有{len(current_page_lines)}行")
        
        if self.mode == 'line':
            # 逐行模式：显示当前页的所有文本，但根据状态着色
            display_lines = []
            char_states_by_pos = {}
            text_pos = 0
            
            # 线程安全地获取绝对位置状态
            with self._state_lock:
                absolute_states = self._absolute_char_states.copy()
            
            for line_idx in range(len(current_page_lines)):
                line_text = current_page_lines[line_idx]
                display_lines.append(line_text)
                
                # 为每个字符设置状态
                for char_idx in range(len(line_text)):
                    # 计算字符的绝对位置
                    absolute_pos = self._calculate_absolute_position(
                        self.current_page, line_idx, char_idx
                    )
                    
                    # 从绝对位置状态或相对位置状态获取状态
                    char_key = (self.current_page, line_idx, char_idx)
                    state = absolute_states.get(absolute_pos, 'normal')
                    if state == 'normal':
                        # 如果绝对位置没有状态，尝试相对位置
                        with self._state_lock:
                            state = self.char_states.get(char_key, 'normal')
                    
                    char_states_by_pos[text_pos] = state
                    text_pos += 1
                
                # 换行符
                if line_idx < len(current_page_lines) - 1:
                    text_pos += 1  # 为换行符留位置
                
                print(f"[DEBUG]   行{line_idx}: {repr(line_text[:20])}...")
            
            # 直接返回当前页内容，不再强制补齐到固定行数
            result = '\n'.join(display_lines)
            print(f"[DEBUG] 逐行模式返回文本，长度: {len(result)}, 状态数: {len(char_states_by_pos)}")
            print(f"[DEBUG] 绝对位置状态数: {len(absolute_states)}, 相对位置状态数: {len(self.char_states)}")
            return result, char_states_by_pos
        
        else:
            # 按页模式：显示完整的当前页
            display_lines = current_page_lines[:]
            
            # 直接返回当前页内容，不再强制补齐到固定行数
            result = '\n'.join(display_lines)
            print(f"[DEBUG] 按页模式返回文本，长度: {len(result)}")
            return result, {}  # 按页模式不需要字符状态
    
    def get_current_display_text(self) -> str:
        """兼容性方法：获取当前应该显示的文本"""
        text, _ = self.get_current_display_text_with_states()
        return text

    def get_progress(self) -> float:
        """获取阅读进度（0-1）"""
        if not self.current_article or not self.pages:
            print(f"[DEBUG] get_progress: 没有文章数据，返回0.0")
            return 0.0
        
        if len(self.pages) == 0:
            print(f"[DEBUG] get_progress: 没有页面，返回1.0")
            return 1.0
        
        if self.mode == 'line':
            # 逐行模式：基于字符级别的进度
            total_chars = sum(len(line) for page in self.pages for line in page)
            if total_chars == 0:
                print(f"[DEBUG] get_progress: 总字符数为0，返回1.0")
                return 1.0
            
            # 计算已完成的字符数
            completed_chars = 0
            
            # 已完成的页面
            for page_idx in range(self.current_page):
                page_chars = sum(len(line) for line in self.pages[page_idx])
                completed_chars += page_chars
                print(f"[DEBUG] get_progress: 页{page_idx}已完成，{page_chars}字符")
            
            # 当前页面已完成的行
            if self.current_page < len(self.pages):
                current_page = self.pages[self.current_page]
                for line_idx in range(self.current_line_in_page):
                    if line_idx < len(current_page):
                        line_chars = len(current_page[line_idx])
                        completed_chars += line_chars
                        print(f"[DEBUG] get_progress: 当前页行{line_idx}已完成，{line_chars}字符")
                
                # 当前行已处理的字符
                completed_chars += self.chars_in_current_line
                print(f"[DEBUG] get_progress: 当前行已处理{self.chars_in_current_line}字符")
            
            progress = min(1.0, completed_chars / total_chars)
            print(f"[DEBUG] get_progress: 逐行模式，{completed_chars}/{total_chars}字符，进度{progress:.1%}")
            return progress
        
        else:
            # 按页模式：基于页面的进度，考虑页面内进度
            base_progress = self.current_page / len(self.pages)
            
            # 如果正在阅读当前页且有进度追踪信息，计算页面内进度
            page_internal_progress = 0.0
            if (self.is_reading and self.page_reading_start_time > 0 and 
                self.page_reading_duration > 0 and self.current_page < len(self.pages)):
                
                elapsed_time = time.time() - self.page_reading_start_time
                page_progress = min(1.0, elapsed_time / self.page_reading_duration)
                # 页面内进度贡献到总进度
                page_internal_progress = page_progress / len(self.pages)
                
                print(f"[DEBUG] get_progress: 页面内进度 {page_progress:.1%}, 贡献 {page_internal_progress:.1%}")
            
            total_progress = min(1.0, base_progress + page_internal_progress)
            print(f"[DEBUG] get_progress: 按页模式，基础{self.current_page}/{len(self.pages)}页={base_progress:.1%}, "
                  f"页面内+{page_internal_progress:.1%}, 总进度{total_progress:.1%}")
            return total_progress
    
    def get_remaining_time(self) -> int:
        """获取剩余阅读时间（秒）"""
        if not self.current_article or not self.pages or not self.is_reading:
            return 0
        
        if self.mode == 'line':
            # 逐行模式：基于剩余字符数计算时间
            total_chars = sum(len(line) for page in self.pages for line in page)
            completed_chars = 0
            
            # 已完成的页面
            for page_idx in range(self.current_page):
                page_chars = sum(len(line) for line in self.pages[page_idx])
                completed_chars += page_chars
            
            # 当前页面已完成的行
            if self.current_page < len(self.pages):
                current_page = self.pages[self.current_page]
                for line_idx in range(self.current_line_in_page):
                    if line_idx < len(current_page):
                        line_chars = len(current_page[line_idx])
                        completed_chars += line_chars
                
                # 当前行已处理的字符
                completed_chars += self.chars_in_current_line
            
            remaining_chars = max(0, total_chars - completed_chars)
            
            # 考虑渐隐时间，每个字符需要渐隐几个级别
            chars_per_minute = self.reading_speed
            remaining_minutes = remaining_chars / chars_per_minute
            remaining_seconds = int(remaining_minutes * 60)
            
            print(f"[DEBUG] 剩余时间: {remaining_chars}字符, {remaining_seconds}秒")
            return remaining_seconds
        
        else:
            # 按页模式：基于剩余页面数计算时间，考虑当前页面内剩余时间
            remaining_full_pages = max(0, len(self.pages) - self.current_page - 1)
            
            # 估算每页的平均字符数和阅读时间
            avg_chars_per_page = sum(len(line) for page in self.pages for line in page) / len(self.pages) if self.pages else 0
            chars_per_minute = self.reading_speed
            minutes_per_page = avg_chars_per_page / chars_per_minute
            
            # 后续完整页面的时间
            full_pages_seconds = int(remaining_full_pages * minutes_per_page * 60)
            
            # 当前页面的剩余时间
            current_page_remaining_seconds = 0
            if (self.current_page < len(self.pages) and self.is_reading and 
                self.page_reading_start_time > 0 and self.page_reading_duration > 0):
                
                elapsed_time = time.time() - self.page_reading_start_time
                current_page_remaining_seconds = max(0, int(self.page_reading_duration - elapsed_time))
                
                print(f"[DEBUG] 当前页剩余时间: {current_page_remaining_seconds}秒 "
                      f"(已过{elapsed_time:.1f}秒/总{self.page_reading_duration:.1f}秒)")
            elif self.current_page < len(self.pages):
                # 如果当前页还没开始阅读，计算当前页的完整时间
                current_page_lines = self.pages[self.current_page]
                page_text = '\n'.join(current_page_lines)
                char_count = len([c for c in page_text if c.strip()])
                current_page_duration = max(2.0, min(20.0, (char_count * 60.0) / self.reading_speed))
                current_page_remaining_seconds = int(current_page_duration)
                
                print(f"[DEBUG] 当前页未开始，计算完整时间: {current_page_remaining_seconds}秒")
            
            total_remaining_seconds = full_pages_seconds + current_page_remaining_seconds
            
            print(f"[DEBUG] 剩余时间: 当前页{current_page_remaining_seconds}秒 + {remaining_full_pages}完整页{full_pages_seconds}秒 = {total_remaining_seconds}秒")
            return total_remaining_seconds
    
    def has_questions(self) -> bool:
        """检查当前文章是否有问题"""
        return (self.current_article is not None and 
                self.current_article.questions is not None and 
                len(self.current_article.questions) > 0)
    
    def get_questions(self):
        """获取当前文章的问题列表"""
        if self.current_article and self.current_article.questions:
            return self.current_article.questions
        return []
    
    def is_in_question_mode(self) -> bool:
        """检查是否处于问题模式"""
        return self.is_question_mode
    
    def exit_question_mode(self):
        """退出问题模式"""
        self.is_question_mode = False
        print(f"[DEBUG] 退出问题模式") 

    def _calculate_absolute_position(self, page_idx: int, line_idx: int, char_idx: int) -> int:
        """计算字符的绝对位置，基于原始文档的连续性"""
        absolute_pos = 0
        
        # 计算总的行索引（在整个文档中）
        total_line_idx = 0
        for p in range(page_idx):
            if p < len(self.pages):
                total_line_idx += len(self.pages[p])
        total_line_idx += line_idx
        
        # 计算到目标行之前的所有字符数
        current_line_count = 0
        for p in range(len(self.pages)):
            page_lines = self.pages[p]
            for l, line in enumerate(page_lines):
                if current_line_count >= total_line_idx:
                    break
                    
                absolute_pos += len(line)
                # 除了整个文档的最后一行，每行后都有换行符
                if not (p == len(self.pages) - 1 and l == len(page_lines) - 1):
                    absolute_pos += 1  # +1 for newline
                    
                current_line_count += 1
            
            if current_line_count >= total_line_idx:
                break
        
        # 加上当前行的字符偏移
        absolute_pos += char_idx
        
        return absolute_pos
    
    def _fade_character_complete(self, absolute_pos: int, char_key: tuple, current_char: str, start_fade_level: int, char_delay: float) -> bool:
        """优化版：高效地渐隐一个字符，减少中间状态和UI更新次数"""
        page_idx, line_idx, char_idx = char_key
        
        # 检查是否应该停止
        if not self.is_reading:
            with self._state_lock:
                self._absolute_char_states[absolute_pos] = 'faded'
                self.char_states[char_key] = 'faded'
            self._schedule_batch_update()  # 批量更新而非立即更新
            return False
        
        # 优化：根据渐隐级别数决定处理策略
        if self.fading_levels <= 2:
            # 简化模式：只有正常 -> 渐隐中 -> 消失，减少中间状态
            return self._fade_character_simplified(absolute_pos, char_key, current_char, char_delay)
        else:
            # 传统模式：保持原有的多级渐隐（已优化）
            return self._fade_character_traditional(absolute_pos, char_key, current_char, start_fade_level, char_delay)
    
    def _fade_character_simplified(self, absolute_pos: int, char_key: tuple, current_char: str, char_delay: float) -> bool:
        """简化版渐隐：只有三个状态 - normal -> fading_1 -> faded"""
        page_idx, line_idx, char_idx = char_key
        
        # 计算每个状态的持续时间
        state_duration = char_delay
        
        # 状态1: 正常 -> 渐隐中
        with self._state_lock:
            self._absolute_char_states[absolute_pos] = 'fading_1'
            self.char_states[char_key] = 'fading_1'
        
        # 安排批量更新而非立即更新
        self._schedule_batch_update()
        
        # 等待一半时间
        if not self._interruptible_sleep(state_duration):
            return False
        
        # 状态2: 渐隐中 -> 完全消失
        with self._state_lock:
            self._absolute_char_states[absolute_pos] = 'faded'
            self.char_states[char_key] = 'faded'
        
        # 最终状态更新
        self._schedule_batch_update()
        
        return True
    
    def _fade_character_traditional(self, absolute_pos: int, char_key: tuple, current_char: str, start_fade_level: int, char_delay: float) -> bool:
        """传统版渐隐：支持多级渐隐，但优化了更新频率"""
        page_idx, line_idx, char_idx = char_key
        
        for fade_level in range(start_fade_level, self.fading_levels + 1):
            if not self.is_reading:
                with self._state_lock:
                    self._absolute_char_states[absolute_pos] = 'faded'
                    self.char_states[char_key] = 'faded'
                self._schedule_batch_update()
                return False
            
            # 设置渐隐状态
            if fade_level == 0:
                state = 'normal'
            elif fade_level < self.fading_levels:
                state = f'fading_{fade_level}'
            else:
                state = 'faded'
            
            # 线程安全地更新状态
            with self._state_lock:
                self._absolute_char_states[absolute_pos] = state
                self.char_states[char_key] = state
            
            # 批量更新UI，避免每次状态变化都更新
            self._schedule_batch_update()
            
            # 等待渐隐时间（最后一级不等待）
            if fade_level < self.fading_levels:
                if not self._interruptible_sleep(char_delay):
                    return False
        
        return True
    
    def _interruptible_sleep(self, duration: float) -> bool:
        """可中断的睡眠，优化了响应性"""
        # 减少分段数，从20降到5，提高效率
        sleep_segments = 5
        segment_time = duration / sleep_segments
        
        for _ in range(sleep_segments):
            if not self.is_reading:
                return False
            
            # 处理暂停（优化：减少暂停检查频率）
            if self.is_paused:
                while self.is_paused and self.is_reading:
                    time.sleep(0.1)
                if not self.is_reading:
                    return False
            
            time.sleep(segment_time)
        
        return True 

    def _validate_and_cleanup_states(self):
        """验证并清理字符状态，确保状态一致性"""
        if not self.pages:
            return
            
        with self._state_lock:
            # 计算文档总字符数
            total_chars = 0
            for page in self.pages:
                for line in page:
                    total_chars += len(line)
            
            # 清理无效的绝对位置状态
            invalid_absolute_keys = [
                pos for pos in self._absolute_char_states.keys() 
                if pos < 0 or pos >= total_chars
            ]
            
            for key in invalid_absolute_keys:
                del self._absolute_char_states[key]
            
            # 清理无效的相对位置状态
            invalid_relative_keys = [
                key for key in self.char_states.keys()
                if (key[0] >= len(self.pages) or 
                    key[1] >= len(self.pages[key[0]]) if key[0] < len(self.pages) else True or
                    key[2] >= len(self.pages[key[0]][key[1]]) if key[0] < len(self.pages) and key[1] < len(self.pages[key[0]]) else True)
            ]
            
            for key in invalid_relative_keys:
                del self.char_states[key]
            
            if invalid_absolute_keys or invalid_relative_keys:
                print(f"[DEBUG] 状态清理: 删除了 {len(invalid_absolute_keys)} 个无效绝对位置状态, {len(invalid_relative_keys)} 个无效相对位置状态")
                print(f"[DEBUG] 当前状态: {len(self._absolute_char_states)} 个绝对位置状态, {len(self.char_states)} 个相对位置状态")

    def _schedule_batch_update(self):
        """安排批量更新，避免过于频繁的UI更新"""
        if self.pending_updates:
            return  # 已经有待处理的更新
        
        self.pending_updates = True
        # 延迟少量时间后执行批量更新
        if self.update_callback:
            # 使用threading.Timer而不是window.after，因为这里是在后台线程中
            if self.batch_timer:
                self.batch_timer.cancel()
            
            self.batch_timer = threading.Timer(self.batch_update_interval, self._execute_batch_update)
            self.batch_timer.start()
    
    def _execute_batch_update(self):
        """执行批量更新"""
        self.pending_updates = False
        self.batch_timer = None
        
        if self.update_callback:
            self.update_callback() 

    def set_text_widget_reference(self, text_widget, available_height: int, font_size: int, line_spacing: float = 1.5):
        """设置文本控件引用和显示参数，用于智能分页"""
        self.text_widget = text_widget
        self.available_height = available_height
        self.font_size = font_size
        self.line_spacing = line_spacing
        print(f"[DEBUG] 设置智能分页参数: 高度{available_height}px, 字体{font_size}pt, 行距{line_spacing}") 