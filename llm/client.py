import json
import requests
from typing import Optional, Dict, Any
from loguru import logger
from config.settings import settings


class LLMClient:
    def __init__(self, provider: str = None, api_key: str = None, model: str = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._get_model()
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        
        self._setup_client()
        logger.info(f"[LLM] 初始化 {self.provider} 客户端, 模型: {self.model}")
    
    def _get_api_key(self) -> str:
        if self.provider == "doubao":
            return settings.DOUBAO_API_KEY
        elif self.provider == "deepseek":
            return settings.DEEPSEEK_API_KEY
        return ""
    
    def _get_model(self) -> str:
        if self.provider == "doubao":
            return settings.DOUBAO_MODEL
        elif self.provider == "deepseek":
            return settings.DEEPSEEK_MODEL
        return ""
    
    def _setup_client(self):
        if self.provider == "doubao":
            # 火山引擎豆包API
            self.url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        elif self.provider == "deepseek":
            self.url = "https://api.deepseek.com/v1/chat/completions"
        else:
            self.url = ""
    
    def is_available(self) -> bool:
        return bool(self.api_key) and bool(self.model)
    
    def chat(self, prompt: str, system_prompt: str = None) -> str:
        if not self.is_available():
            logger.warning(f"[LLM] {self.provider} 未配置，无法调用")
            return ""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(
                self.url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"[LLM] API调用失败: {response.status_code} - {response.text}")
                return ""
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            usage = result.get("usage", {})
            logger.info(f"[LLM] 调用成功, tokens: {usage.get('total_tokens', 0)}")
            
            return content
        except Exception as e:
            logger.error(f"[LLM] 调用异常: {e}")
            return ""
    
    def analyze(self, prompt: str, data: Dict[str, Any]) -> str:
        formatted_prompt = prompt.format(**data)
        return self.chat(formatted_prompt)
    
    def analyze_json(self, prompt: str, data: Dict[str, Any]) -> Optional[Dict]:
        response = self.analyze(prompt, data)
        
        if not response:
            return None
        
        try:
            json_match = response
            if "```json" in response:
                json_match = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_match = response.split("```")[1].split("```")[0]
            
            json_match = json_match.strip()
            
            if json_match.startswith("{") and json_match.endswith("}"):
                pass
            else:
                start = json_match.find("{")
                end = json_match.rfind("}") + 1
                if start != -1 and end > start:
                    json_match = json_match[start:end]
            
            return json.loads(json_match)
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] JSON解析失败: {e}, 原始响应: {response}")
            return None


class MockLLMClient(LLMClient):
    def __init__(self):
        self.provider = "mock"
        self.is_available = True
        logger.info("[LLM] 使用Mock客户端（测试模式）")
    
    def chat(self, prompt: str, system_prompt: str = None) -> str:
        if "市场环境" in prompt:
            return '{"env_type": "震荡市", "confidence": 0.75, "reason": "市场波动正常，无明显趋势"}'
        elif "信号" in prompt:
            return '{"decision": "pass", "reason": "信号有效，市场条件符合"}'
        elif "风险" in prompt:
            return '{"risk_level": "low", "affected_symbols": ["510300"], "reason": "无明显风险事件"}'
        elif "估值" in prompt:
            return '{"valuation": "合理", "suggestion": 0.8, "reason": "当前估值处于历史中位数"}'
        return '{"result": "mock"}'


def get_llm_client(use_mock: bool = False) -> LLMClient:
    if use_mock:
        return MockLLMClient()
    return LLMClient()


llm_client = get_llm_client()
