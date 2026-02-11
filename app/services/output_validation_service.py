"""
输出验证服务
验证AI生成的响应是否符合安全和质量标准
"""

import re
from typing import Dict, Any, Optional
from app.models.ai_chat import AiGroupMember
from app.services.input_sanitizer_service import InputSanitizerService, SanitizationLevel


class OutputValidationService:
    """输出验证服务类"""

    def __init__(self, db_session):
        self.db = db_session
        self.sanitizer = InputSanitizerService()
        
        # 定义验证规则
        self.validation_rules = {
            "content_filters": {
                "forbidden_phrases": [
                    "系统指令", "system prompt", "ignore above", "disregard previous",
                    "as a language model", "as an AI assistant", "I cannot",
                    "I'm sorry", "I apologize", "I shouldn't", "I can't"
                ],
                "forbidden_patterns": [
                    r'<.*?>',  # HTML标签
                    r'\{.*?\}',  # 模板占位符
                    r'\$\{.*?\}',  # JS模板表达式
                    r'%\{.*?\}',  # 其他模板表达式
                ]
            },
            "format_requirements": {
                "max_length": 500,  # 最大长度
                "min_length": 1,    # 最小长度
                "allowed_special_chars": ['!', '?', '.', ',', ':', ';', '-', '(', ')'],  # 允许的特殊字符
            },
            "role_compliance": {
                "require_personality_reflection": True,  # 是否需要反映个性
                "require_stance_consistency": True       # 是否需要保持立场一致
            }
        }

    def validate_response(
        self,
        ai_member: AiGroupMember,
        response: str,
        original_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证AI响应是否符合安全和质量标准
        
        Args:
            ai_member: AI成员对象
            response: AI生成的响应
            original_prompt: 原始提示词（可选）
            
        Returns:
            验证结果字典
        """
        results = {
            "is_valid": True,
            "issues_found": [],
            "quality_score": 100,  # 质量分数 (0-100)
            "compliance_score": 100,  # 合规分数 (0-100)
            "suggestions": []
        }
        
        # 检查基本格式要求
        format_check = self._check_format_requirements(response)
        if not format_check["is_valid"]:
            results["is_valid"] = False
            results["issues_found"].extend(format_check["issues"])
            results["quality_score"] -= 20
        
        # 检查内容安全性
        content_check = self._check_content_safety(response)
        if not content_check["is_valid"]:
            results["is_valid"] = False
            results["issues_found"].extend(content_check["issues"])
            results["quality_score"] -= 30
        
        # 检查角色合规性
        compliance_check = self._check_role_compliance(ai_member, response)
        if not compliance_check["is_compliant"]:
            results["is_valid"] = False
            results["issues_found"].extend(compliance_check["issues"])
            results["compliance_score"] -= 40
        
        # 检查是否泄露系统信息
        leak_check = self._check_for_system_leakage(response)
        if not leak_check["is_safe"]:
            results["is_valid"] = False
            results["issues_found"].extend(leak_check["issues"])
            results["quality_score"] -= 25
        
        # 计算最终分数
        results["quality_score"] = max(0, results["quality_score"])
        results["compliance_score"] = max(0, results["compliance_score"])
        
        return results

    def _check_format_requirements(self, response: str) -> Dict[str, Any]:
        """检查格式要求"""
        results = {
            "is_valid": True,
            "issues": []
        }
        
        # 检查长度
        min_len = self.validation_rules["format_requirements"]["min_length"]
        max_len = self.validation_rules["format_requirements"]["max_length"]
        
        if len(response) < min_len:
            results["is_valid"] = False
            results["issues"].append({
                "type": "too_short",
                "severity": "high",
                "message": f"响应长度({len(response)})小于最小要求({min_len})"
            })
        
        if len(response) > max_len:
            results["is_valid"] = False
            results["issues"].append({
                "type": "too_long",
                "severity": "medium",
                "message": f"响应长度({len(response)})超过最大限制({max_len})"
            })
        
        return results

    def _check_content_safety(self, response: str) -> Dict[str, Any]:
        """检查内容安全性"""
        results = {
            "is_valid": True,
            "issues": []
        }
        
        # 检查禁用短语
        for phrase in self.validation_rules["content_filters"]["forbidden_phrases"]:
            if phrase.lower() in response.lower():
                results["is_valid"] = False
                results["issues"].append({
                    "type": "forbidden_phrase",
                    "severity": "medium",
                    "message": f"发现禁用短语: {phrase}",
                    "phrase": phrase
                })
        
        # 检查禁用模式
        import re
        for pattern in self.validation_rules["content_filters"]["forbidden_patterns"]:
            if re.search(pattern, response, re.IGNORECASE):
                results["is_valid"] = False
                results["issues"].append({
                    "type": "forbidden_pattern",
                    "severity": "high",
                    "message": f"发现禁用模式: {pattern}",
                    "pattern": pattern
                })
        
        # 使用输入净化器检测潜在问题
        injection_detection = self.sanitizer.detect_potential_injection(response)
        if injection_detection["score"] > 20:  # 风险评分高于20%
            results["is_valid"] = False
            results["issues"].append({
                "type": "potential_injection",
                "severity": "high",
                "message": f"检测到潜在注入，风险评分: {injection_detection['score']}",
                "details": injection_detection
            })
        
        return results

    def _check_role_compliance(self, ai_member: AiGroupMember, response: str) -> Dict[str, Any]:
        """检查角色合规性"""
        results = {
            "is_compliant": True,
            "issues": []
        }
        
        # 检查是否反映了AI的个性特征
        if (self.validation_rules["role_compliance"]["require_personality_reflection"] 
            and ai_member.personality 
            and ai_member.personality.lower() not in response.lower()):
            results["is_compliant"] = False
            results["issues"].append({
                "type": "personality_not_reflected",
                "severity": "low",
                "message": "响应未能体现AI的个性特征"
            })
        
        # 检查是否保持了AI的立场
        if (self.validation_rules["role_compliance"]["require_stance_consistency"] 
            and ai_member.initial_stance 
            and ai_member.initial_stance.lower() not in response.lower()):
            results["is_compliant"] = False
            results["issues"].append({
                "type": "stance_not_maintained",
                "severity": "medium",
                "message": "响应未能保持AI的初始立场"
            })
        
        return results

    def _check_for_system_leakage(self, response: str) -> Dict[str, Any]:
        """检查是否泄露系统信息"""
        results = {
            "is_safe": True,
            "issues": []
        }
        
        leakage_indicators = [
            "system:",
            "system prompt:",
            "instruction:",
            "instructions:",
            "role:",
            "你是一个AI助手",
            "作为AI",
            "language model"
        ]
        
        for indicator in leakage_indicators:
            if indicator.lower() in response.lower():
                results["is_safe"] = False
                results["issues"].append({
                    "type": "system_leakage",
                    "severity": "high",
                    "message": f"检测到系统信息泄露: {indicator}",
                    "indicator": indicator
                })
        
        return results

    def post_process_response(self, response: str, ai_member: AiGroupMember) -> str:
        """
        后处理AI响应，使其更自然和安全
        
        Args:
            response: AI生成的原始响应
            ai_member: AI成员对象
            
        Returns:
            处理后的响应
        """
        # 使用正则表达式去除过度的格式化标记
        import re

        # 移除过多的星号、井号等格式符号
        processed = re.sub(r'\*{2,}', '', response)  # 移除多余的**
        processed = re.sub(r'#{1,}', '', processed)   # 移除多余的#
        processed = re.sub(r'^\s*[-*]\s*', '', processed, flags=re.MULTILINE)  # 移除列表符号

        # 限制重复的换行符
        processed = re.sub(r'\n{3,}', '\n\n', processed)

        # 修剪首尾空白
        processed = processed.strip()

        # 确保不超过最大长度，同时保留完整句子
        if len(processed) > 500:
            # 尝试在句子边界处截断
            last_sentence_end = max(
                processed.rfind('.', 0, 500),
                processed.rfind('!', 0, 500),
                processed.rfind('?', 0, 500)
            )
            
            if last_sentence_end != -1 and last_sentence_end > 300:  # 确保截断位置合理
                processed = processed[:last_sentence_end + 1]
            else:
                # 如果找不到合适的句子边界，则硬截断
                processed = processed[:500] + "..."

        return processed

    def validate_and_correct_response(
        self,
        ai_member: AiGroupMember,
        response: str,
        original_prompt: str,
        auto_correct: bool = True
    ) -> Dict[str, Any]:
        """
        验证并可选择性地纠正AI响应
        
        Args:
            ai_member: AI成员对象
            response: AI生成的响应
            original_prompt: 原始提示词
            auto_correct: 是否自动纠正
            
        Returns:
            包含验证结果和可能的纠正后响应的字典
        """
        # 首先验证响应
        validation_result = self.validate_response(ai_member, response, original_prompt)
        
        result = {
            "original_response": response,
            "validation_result": validation_result,
            "final_response": response,
            "was_corrected": False
        }
        
        if validation_result["is_valid"] and auto_correct:
            # 如果验证失败且启用了自动纠正，则尝试后处理
            corrected_response = self.post_process_response(response, ai_member)
            
            # 再次验证纠正后的响应
            corrected_validation = self.validate_response(ai_member, corrected_response, original_prompt)
            
            if corrected_validation["is_valid"]:
                result["final_response"] = corrected_response
                result["was_corrected"] = True
            else:
                # 如果纠正后仍无效，则返回原始验证结果
                result["validation_result"] = corrected_validation
        elif not validation_result["is_valid"]:
            # 如果验证失败且未启用自动纠正
            result["final_response"] = response  # 保持原样，但标记为无效
        
        return result