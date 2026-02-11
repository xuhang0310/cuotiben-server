"""
输入净化服务
用于净化和过滤用户输入，防止提示词注入和其他安全问题
"""

import re
from typing import Optional
from enum import Enum


class SanitizationLevel(Enum):
    """净化级别"""
    BASIC = "basic"          # 基础净化：去除HTML标签、基本转义
    MODERATE = "moderate"    # 中等净化：基础净化 + 特殊字符过滤
    STRICT = "strict"        # 严格净化：中等净化 + 语义过滤


class InputSanitizerService:
    """输入净化服务类"""

    def __init__(self):
        # 定义需要过滤的危险模式
        self.dangerous_patterns = [
            # 提示词注入相关
            r'(?i)\b(system|instruction|prompt|role|ignore|disregard|forget|previous|above|below|this|message|response|answer|tell|me|to|the|user|following|instructions?)\b',
            r'<.*?>',  # HTML/XML标签
            r'\{.*?\}',  # 模板占位符
            r'\$\{.*?\}',  # JavaScript模板表达式
            r'%\{.*?\}',  # 其他模板表达式
            # 潜在的命令注入
            r'(?i)(exec|execute|eval|system|shell|command|run|import|from)',
            # 潜在的SQL注入片段
            r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)",
        ]

        # 定义危险字符
        self.dangerous_chars = {
            'control': ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0B', '\x0C', '\x0E', '\x0F'],
            'escape': ['\\', '`', '$', '|', '&', ';', '<', '>', '{', '}']
        }

    def sanitize_input(
        self,
        input_text: str,
        level: SanitizationLevel = SanitizationLevel.MODERATE,
        custom_filters: Optional[list] = None
    ) -> str:
        """
        净化输入文本

        Args:
            input_text: 待净化的输入文本
            level: 净化级别
            custom_filters: 自定义过滤规则

        Returns:
            净化后的文本
        """
        if not input_text:
            return input_text

        sanitized = input_text

        # 根据级别应用不同的净化策略
        if level == SanitizationLevel.BASIC:
            sanitized = self._basic_sanitization(sanitized)
        elif level == SanitizationLevel.MODERATE:
            sanitized = self._basic_sanitization(sanitized)
            sanitized = self._moderate_sanitization(sanitized)
        elif level == SanitizationLevel.STRICT:
            sanitized = self._basic_sanitization(sanitized)
            sanitized = self._moderate_sanitization(sanitized)
            sanitized = self._strict_sanitization(sanitized)

        # 应用自定义过滤器
        if custom_filters:
            for pattern in custom_filters:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        return sanitized

    def _basic_sanitization(self, text: str) -> str:
        """基础净化：去除HTML标签和基本转义"""
        # 去除HTML/XML标签
        text = re.sub(r'<[^>]*>', '', text)
        
        # 去除潜在的模板占位符
        text = re.sub(r'\{[^{}]*\}', '', text)
        text = re.sub(r'\$\{[^{}]*\}', '', text)
        
        return text

    def _moderate_sanitization(self, text: str) -> str:
        """中等净化：基础净化 + 特殊字符过滤"""
        # 过滤危险字符
        for char_list in self.dangerous_chars.values():
            for char in char_list:
                text = text.replace(char, '')
        
        # 过滤危险模式
        for pattern in self.dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text

    def _strict_sanitization(self, text: str) -> str:
        """严格净化：中等净化 + 语义过滤"""
        # 进一步过滤可能的注入内容
        # 移除连续的标点符号（可能用于提示词混淆）
        text = re.sub(r'[!?]{3,}', ' ', text)
        text = re.sub(r'[.]{4,}', '.', text)
        
        # 移除可能用于提示词注入的关键词组合
        injection_keywords = [
            r'(?i)(system\s+prompt|instruction\s+to|ignore\s+the|disregard\s+the|start\s+new|begin\s+new|forget\s+previous)',
            r'(?i)(pretend|assume|imagine|act\s+as|roleplay|you\s+are\s+a)',
            r'(?i)(never\s+mind|just|k|ok|sure|yes|no|but|however)'
        ]
        
        for keyword_pattern in injection_keywords:
            text = re.sub(keyword_pattern, ' ', text)
        
        return text

    def validate_input_length(self, text: str, max_length: int = 1000) -> bool:
        """验证输入长度"""
        return len(text) <= max_length

    def detect_potential_injection(self, text: str) -> dict:
        """
        检测潜在的注入内容

        Returns:
            包含检测结果的字典
        """
        detected_issues = {
            'has_dangerous_patterns': False,
            'has_dangerous_chars': False,
            'has_html_tags': False,
            'has_template_placeholders': False,
            'score': 0  # 风险评分 (0-100)
        }

        # 检测危险模式
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                detected_issues['has_dangerous_patterns'] = True
                detected_issues['score'] += 25

        # 检测危险字符
        for char_list in self.dangerous_chars.values():
            for char in char_list:
                if char in text:
                    detected_issues['has_dangerous_chars'] = True
                    detected_issues['score'] += 10

        # 检测HTML标签
        if re.search(r'<[^>]*>', text):
            detected_issues['has_html_tags'] = True
            detected_issues['score'] += 20

        # 检测模板占位符
        if re.search(r'\{[^{}]*\}', text) or re.search(r'\$\{[^{}]*\}', text):
            detected_issues['has_template_placeholders'] = True
            detected_issues['score'] += 15

        return detected_issues

    def escape_special_characters(self, text: str) -> str:
        """
        转义特殊字符，防止注入
        """
        # 转义可能导致问题的字符
        escape_map = {
            '{': '{{',
            '}': '}}',
            '[': '[',
            ']': ']',
            '\\': '\\\\',
            '`': '\\`',
            '$': '\\$'
        }

        for char, escaped_char in escape_map.items():
            text = text.replace(char, escaped_char)

        return text