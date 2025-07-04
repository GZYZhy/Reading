"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 设置管理
"""
import configparser
import os
from typing import Dict, Any

class Settings:
    def __init__(self):
        self.config_file = "config.ini"
        self.config = configparser.ConfigParser()
        self.default_settings = {
            'reading': {
                'font_size': '60',
                'line_spacing': '1.5',
                'reading_speed': '300',  # 字符每分钟
                'background_color': 'white',
                'text_color': 'black',
                'mode': 'line',  # 'line' or 'page'
            },
            'app': {
                'last_folder': '',
                'window_width': '1200',
                'window_height': '800',
            }
        }
        self.load_settings()
    
    def load_settings(self):
        """加载设置，如果文件不存在则使用默认设置"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        for section, options in self.default_settings.items():
            self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, value)
        self.save_settings()
    
    def save_settings(self):
        """保存设置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """获取整数设置值"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """获取浮点数设置值"""
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
    
    def get(self, section: str, key: str, default: str = '') -> str:
        """获取设置值"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def set(self, section: str, key: str, value: str):
        """设置值"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value) 