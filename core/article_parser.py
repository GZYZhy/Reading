"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 文章解析器
"""
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Question:
    question_text: str
    question_type: str  # 'cho' for choice, 'ans' for answer
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None  # For choice questions: 'a', 'b', 'c', 'd'
    explanation: str = ""

@dataclass
class Article:
    title: str
    author: str
    date: str
    type: str
    content: str
    original_content: str  # 添加原始内容字段
    filepath: str
    questions: Optional[List[Question]] = None  # 添加问题列表

class ArticleParser:
    def __init__(self):
        self.articles: List[Article] = []
    
    def load_articles_from_folder(self, folder_path: str) -> List[Article]:
        """从文件夹加载所有txt文章"""
        self.articles = []
        if not os.path.exists(folder_path):
            return self.articles
        
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                filepath = os.path.join(folder_path, filename)
                article = self.parse_article(filepath)
                if article:
                    self.articles.append(article)
        
        return self.articles
    
    def parse_article(self, filepath: str) -> Optional[Article]:
        """解析单个文章文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取元数据
            title = self._extract_metadata(content, 'title')
            author = self._extract_metadata(content, 'author')
            date = self._extract_metadata(content, 'date')
            article_type = self._extract_metadata(content, 'type')
            
            # 提取正文内容和问题部分
            original_content, questions = self._extract_content_and_questions(content)
            
            # 直接使用原始内容，保持自然段落结构，让UI处理换行
            # 不再强制重新格式化，保持文章的原汁原味
            
            return Article(
                title=title or os.path.splitext(os.path.basename(filepath))[0],
                author=author or "未知作者",
                date=date or "未知日期",
                type=article_type or "未分类",
                content=original_content,  # 直接使用原始内容
                original_content=original_content,  # 保存原始内容
                filepath=filepath,
                questions=questions
            )
        except Exception as e:
            print(f"解析文章文件 {filepath} 时出错: {e}")
            return None
    
    def _extract_metadata(self, content: str, key: str) -> str:
        """提取元数据"""
        pattern = rf'\[{key}:"([^"]*?)"\]'
        match = re.search(pattern, content)
        return match.group(1) if match else ""
    
    def _extract_content_and_questions(self, content: str) -> tuple:
        """提取正文内容和问题部分"""
        # 移除所有元数据标签
        content = re.sub(r'\[title:"[^"]*?"\]\s*', '', content)
        content = re.sub(r'\[author:"[^"]*?"\]\s*', '', content)
        content = re.sub(r'\[date:"[^"]*?"\]\s*', '', content)
        content = re.sub(r'\[type:"[^"]*?"\]\s*', '', content)
        
        # 分离正文内容和问题部分
        question_match = re.search(r'\[question\](.*)', content, re.DOTALL)
        if question_match:
            # 有问题部分
            main_content = content[:question_match.start()].strip()
            question_content = question_match.group(1).strip()
            questions = self._parse_questions(question_content)
        else:
            # 没有问题部分
            main_content = content.strip()
            questions = None
        
        # 移除开头的空行
        main_content = main_content.lstrip('\n\r')
        
        # 智能重组段落
        processed_content = self._smart_paragraph_reconstruction(main_content)
        
        return processed_content, questions
    
    def _extract_content(self, content: str) -> str:
        """提取正文内容，保留原始格式并智能重组段落（保持向后兼容）"""
        processed_content, _ = self._extract_content_and_questions(content)
        return processed_content
    
    def _smart_paragraph_reconstruction(self, content: str) -> str:
        """智能重组段落，保持原始txt文件的自然段落结构，只合并被强制换行的文本"""
        lines = content.split('\n')
        paragraphs = []
        current_paragraph_lines = []
        
        for line in lines:
            # 跳过完全空白的行
            if not line.strip():
                continue
                
            # 检测段落开始的标志：
            # 1. 行首有空格缩进
            # 2. 或者是第一行（对于没有缩进的单段落文章）
            stripped_line = line.lstrip()
            line_indent = line[:len(line) - len(stripped_line)]
            
            # 如果这行有缩进，说明是新段落的开始
            if line_indent:
                # 如果之前有段落在构建，先保存它
                if current_paragraph_lines:
                    merged_paragraph = self._merge_paragraph_lines(current_paragraph_lines)
                    if merged_paragraph.strip():
                        paragraphs.append(merged_paragraph)
                    current_paragraph_lines = []
                
                # 开始新段落
                current_paragraph_lines = [line]
            else:
                # 没有缩进的行
                if current_paragraph_lines:
                    # 如果已经有段落在构建，这是段落的继续行
                    current_paragraph_lines.append(line)
                else:
                    # 如果没有段落在构建，这是第一行（无缩进的单段落文章）
                    current_paragraph_lines = [line]
        
        # 处理最后一个段落
        if current_paragraph_lines:
            merged_paragraph = self._merge_paragraph_lines(current_paragraph_lines)
            if merged_paragraph.strip():
                paragraphs.append(merged_paragraph)
        
        return '\n'.join(paragraphs)
    
    def _merge_paragraph_lines(self, lines):
        """将一个段落内被强制换行的多行重新合并成一行"""
        if not lines:
            return ""
        
        # 获取第一行的缩进
        first_line = lines[0]
        stripped_first = first_line.lstrip()
        indent = first_line[:len(first_line) - len(stripped_first)]
        
        # 合并所有行的内容，去掉每行的缩进
        merged_content = ""
        for line in lines:
            stripped = line.lstrip()
            merged_content += stripped
        
        # 返回带原始缩进的合并段落
        return indent + merged_content
    
    def reformat_content(self, content: str, max_line_length: int = 40) -> str:
        """根据指定的最大行长度重新格式化内容，保持段落结构"""
        # 按自然段落分割（以换行符为分隔符）
        paragraphs = content.split('\n')
        processed_lines = []
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) == 0:
                # 保留空行（段落间隔）
                processed_lines.append(paragraph)
            else:
                # 处理非空段落
                # 提取段落的缩进
                original_indent = ""
                stripped_paragraph = paragraph.lstrip()
                if len(paragraph) > len(stripped_paragraph):
                    original_indent = paragraph[:len(paragraph) - len(stripped_paragraph)]
                
                # 如果段落长度在限制内，直接保留
                if len(paragraph) <= max_line_length:
                    processed_lines.append(paragraph)
                else:
                    # 段落过长，需要在段落内部换行，但保持段落结构
                    split_lines = self._split_paragraph_into_lines(stripped_paragraph, max_line_length, original_indent)
                    processed_lines.extend(split_lines)
        
        return '\n'.join(processed_lines)

    def _split_paragraph_into_lines(self, paragraph: str, max_length: int, original_indent: str = "") -> list:
        """将单个段落分割成多行，保持语义完整性和缩进"""
        if len(original_indent + paragraph) <= max_length:
            return [original_indent + paragraph]
        
        result = []
        
        # 计算后续行的缩进（通常比首行缩进少一些或相同）
        continuation_indent = "    "  # 后续行使用4个空格缩进
        
        # 可用长度：第一行扣除原始缩进，后续行扣除继续缩进
        first_line_max = max_length - len(original_indent)
        continuation_max = max_length - len(continuation_indent)
        
        current_text = paragraph
        is_first_line = True
        
        while current_text:
            if is_first_line:
                max_chars = first_line_max
                line_indent = original_indent
                is_first_line = False
            else:
                max_chars = continuation_max
                line_indent = continuation_indent
            
            if len(current_text) <= max_chars:
                # 剩余文本可以放在一行内
                result.append(line_indent + current_text)
                break
            
            # 寻找合适的断点
            break_point = self._find_break_point(current_text, max_chars)
            
            if break_point == -1:
                # 找不到合适断点，强制在最大长度处断开
                break_point = max_chars
            
            # 添加当前行
            line_text = current_text[:break_point].rstrip()
            if line_text:  # 避免空行
                result.append(line_indent + line_text)
            
            # 准备下一行的文本
            current_text = current_text[break_point:].lstrip()
        
        return result
    
    def _find_break_point(self, text: str, max_length: int) -> int:
        """在指定长度内找到最佳的断点位置"""
        if len(text) <= max_length:
            return len(text)
        
        # 按优先级寻找断点：句号 > 逗号等标点 > 空格
        punctuation_marks = ['。', '！', '？', '；']
        comma_marks = ['，', '、', '：']
        
        # 首先在句号等强断点处查找
        for i in range(max_length - 1, max_length // 2, -1):
            if i < len(text) and text[i] in punctuation_marks:
                return i + 1
        
        # 然后在逗号等弱断点处查找  
        for i in range(max_length - 1, max_length // 2, -1):
            if i < len(text) and text[i] in comma_marks:
                return i + 1
        
        # 最后在空格处查找
        for i in range(max_length - 1, max_length // 2, -1):
            if i < len(text) and text[i] == ' ':
                return i + 1
        
        # 找不到合适断点
        return -1

    def _split_long_line(self, line: str, max_length: int = 40) -> list:
        """将长行分割成多行，保持语义完整性（保留兼容性）"""
        # 这个方法保留用于向后兼容，但现在使用新的段落处理逻辑
        return self._split_paragraph_into_lines(line.strip(), max_length, "    ")
    
    def get_articles_by_type(self, article_type: str) -> List[Article]:
        """根据类型筛选文章"""
        return [article for article in self.articles if article.type == article_type]
    
    def get_article_types(self) -> List[str]:
        """获取所有文章类型"""
        types = set(article.type for article in self.articles)
        return list(types)
    
    def _parse_questions(self, question_content: str) -> List[Question]:
        """解析问题内容"""
        questions = []
        
        # 使用正则表达式匹配所有问题块
        question_pattern = r'<question\d+>(.*?)</question\d+>'
        question_matches = re.findall(question_pattern, question_content, re.DOTALL)
        
        for match in question_matches:
            question_data = match.strip()
            
            # 解析问题文本
            que_match = re.search(r'<que>(.*?)</que>', question_data, re.DOTALL)
            question_text = que_match.group(1).strip() if que_match else ""
            
            # 解析问题类型
            type_match = re.search(r'<type>(.*?)</type>', question_data, re.DOTALL)
            question_type = type_match.group(1).strip() if type_match else ""
            
            # 解析解释
            explain_match = re.search(r'<explain>(.*?)</explain>', question_data, re.DOTALL)
            explanation = explain_match.group(1).strip() if explain_match else ""
            
            if question_type == 'cho':
                # 选择题，解析选项和答案
                option_a_match = re.search(r'<a>(.*?)</a>', question_data, re.DOTALL)
                option_b_match = re.search(r'<b>(.*?)</b>', question_data, re.DOTALL)
                option_c_match = re.search(r'<c>(.*?)</c>', question_data, re.DOTALL)
                option_d_match = re.search(r'<d>(.*?)</d>', question_data, re.DOTALL)
                ans_match = re.search(r'<ans>(.*?)</ans>', question_data, re.DOTALL)
                
                option_a = option_a_match.group(1).strip() if option_a_match else ""
                option_b = option_b_match.group(1).strip() if option_b_match else ""
                option_c = option_c_match.group(1).strip() if option_c_match else ""
                option_d = option_d_match.group(1).strip() if option_d_match else ""
                correct_answer = ans_match.group(1).strip() if ans_match else ""
                
                question = Question(
                    question_text=question_text,
                    question_type=question_type,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_answer=correct_answer,
                    explanation=explanation
                )
            else:
                # 简答题
                question = Question(
                    question_text=question_text,
                    question_type=question_type,
                    explanation=explanation
                )
            
            if question_text:  # 只添加有问题文本的问题
                questions.append(question)
        
        return questions 