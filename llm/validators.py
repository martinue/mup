import json
from typing import Dict, Any, Optional
from loguru import logger


class OutputValidator:
    @staticmethod
    def validate_json_structure(data: Dict, required_fields: list) -> bool:
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"[校验] 缺少字段: {field}")
                return False
        
        return True
    
    @staticmethod
    def validate_enum_value(value: str, allowed_values: list) -> bool:
        return value in allowed_values
    
    @staticmethod
    def validate_confidence(value: float) -> bool:
        return 0 <= value <= 1
    
    @staticmethod
    def validate_suggestion(value: float) -> bool:
        return 0 <= value <= 2
    
    @staticmethod
    def sanitize_json_response(response: str) -> Optional[Dict]:
        if not response:
            return None
        
        try:
            json_str = response.strip()
            
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            if not json_str.startswith("{"):
                start = json_str.find("{")
                end = json_str.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = json_str[start:end]
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"[校验] JSON解析失败: {e}")
            return None


class MarketEnvValidator(OutputValidator):
    REQUIRED_FIELDS = ["env_type", "confidence", "reason"]
    ALLOWED_ENV_TYPES = ["震荡市", "单边牛市", "单边熊市"]
    
    @classmethod
    def validate(cls, data: Dict) -> bool:
        if not cls.validate_json_structure(data, cls.REQUIRED_FIELDS):
            return False
        
        if not cls.validate_enum_value(data.get("env_type"), cls.ALLOWED_ENV_TYPES):
            return False
        
        if not cls.validate_confidence(data.get("confidence", 0)):
            return False
        
        return True


class SignalFilterValidator(OutputValidator):
    REQUIRED_FIELDS = ["decision", "reason"]
    ALLOWED_DECISIONS = ["pass", "reject"]
    
    @classmethod
    def validate(cls, data: Dict) -> bool:
        if not cls.validate_json_structure(data, cls.REQUIRED_FIELDS):
            return False
        
        if not cls.validate_enum_value(data.get("decision"), cls.ALLOWED_DECISIONS):
            return False
        
        return True


class RiskAlertValidator(OutputValidator):
    REQUIRED_FIELDS = ["risk_level", "affected_symbols", "reason"]
    ALLOWED_RISK_LEVELS = ["high", "medium", "low"]
    
    @classmethod
    def validate(cls, data: Dict) -> bool:
        if not cls.validate_json_structure(data, cls.REQUIRED_FIELDS):
            return False
        
        if not cls.validate_enum_value(data.get("risk_level"), cls.ALLOWED_RISK_LEVELS):
            return False
        
        return True


class ValuationValidator(OutputValidator):
    REQUIRED_FIELDS = ["valuation", "suggestion", "reason"]
    ALLOWED_VALUATIONS = ["低估", "合理", "高估"]
    
    @classmethod
    def validate(cls, data: Dict) -> bool:
        if not cls.validate_json_structure(data, cls.REQUIRED_FIELDS):
            return False
        
        if not cls.validate_enum_value(data.get("valuation"), cls.ALLOWED_VALUATIONS):
            return False
        
        if not cls.validate_suggestion(data.get("suggestion", 1)):
            return False
        
        return True


output_validator = OutputValidator()
