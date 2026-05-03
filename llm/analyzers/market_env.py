from typing import Optional
from loguru import logger
from llm.client import LLMClient, get_llm_client
from config.prompts import MARKET_ENV_PROMPT
from core.models import MarketData, MarketEnv, MarketEnvResult
from data import storage


class MarketEnvAnalyzer:
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or get_llm_client()
    
    def analyze(self, market_data: MarketData) -> MarketEnvResult:
        if not self.llm.is_available:
            logger.warning("[市场环境] LLM不可用，返回默认结果")
            return MarketEnvResult(
                env_type=MarketEnv.OSCILLATION,
                confidence=0.5,
                reason="LLM不可用，使用默认值"
            )
        
        result = self.llm.analyze_json(MARKET_ENV_PROMPT, market_data.to_dict())
        
        if result is None:
            return MarketEnvResult(
                env_type=MarketEnv.OSCILLATION,
                confidence=0.5,
                reason="LLM解析失败，使用默认值"
            )
        
        try:
            env_type_str = result.get("env_type", "震荡市")
            env_type = MarketEnv.OSCILLATION
            if "牛市" in env_type_str:
                env_type = MarketEnv.BULL
            elif "熊市" in env_type_str:
                env_type = MarketEnv.BEAR
            
            analysis_result = MarketEnvResult(
                env_type=env_type,
                confidence=float(result.get("confidence", 0.5)),
                reason=result.get("reason", "")
            )
            
            storage.save_llm_analysis(
                analysis_type="market_env",
                input_data=str(market_data.to_dict()),
                output_data=str(result),
                model=self.llm.provider
            )
            
            logger.info(f"[市场环境] 分析结果: {env_type.value}, 置信度: {analysis_result.confidence}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"[市场环境] 解析结果失败: {e}")
            return MarketEnvResult(
                env_type=MarketEnv.OSCILLATION,
                confidence=0.5,
                reason=f"解析失败: {e}"
            )


market_env_analyzer = MarketEnvAnalyzer()
