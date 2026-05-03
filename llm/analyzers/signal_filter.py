from typing import Optional, List
from loguru import logger
from llm.client import LLMClient, get_llm_client
from config.prompts import SIGNAL_FILTER_PROMPT
from core.models import Signal, FilterResult, SignalContext
from data import storage


class SignalFilterAnalyzer:
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or get_llm_client()
    
    def filter(self, signal: Signal, market_env: str = "震荡市", 
               news_summary: str = "") -> FilterResult:
        if not self.llm.is_available:
            logger.warning("[信号过滤] LLM不可用，默认通过")
            return FilterResult(decision="pass", reason="LLM不可用，默认通过")
        
        context = SignalContext(
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            trigger_price=signal.trigger_price,
            current_price=signal.current_price,
            deviation=signal.deviation,
            market_env=market_env,
            news_summary=news_summary[:500] if news_summary else "无重大新闻"
        )
        
        result = self.llm.analyze_json(SIGNAL_FILTER_PROMPT, context.to_dict())
        
        if result is None:
            return FilterResult(
                decision="pass",
                reason="LLM解析失败，默认通过"
            )
        
        try:
            filter_result = FilterResult(
                decision=result.get("decision", "pass"),
                reason=result.get("reason", "")
            )
            
            storage.save_llm_analysis(
                analysis_type="signal_filter",
                input_data=str(context.to_dict()),
                output_data=str(result),
                model=self.llm.provider
            )
            
            logger.info(f"[信号过滤] 结果: {filter_result.decision}, 理由: {filter_result.reason}")
            return filter_result
            
        except Exception as e:
            logger.error(f"[信号过滤] 解析结果失败: {e}")
            return FilterResult(decision="pass", reason=f"解析失败: {e}")
    
    def batch_filter(self, signals: List[Signal], market_env: str = "震荡市",
                     news_summary: str = "") -> List[Signal]:
        filtered = []
        for signal in signals:
            result = self.filter(signal, market_env, news_summary)
            if result.passed:
                filtered.append(signal)
        
        logger.info(f"[信号过滤] 批量过滤: {len(signals)} -> {len(filtered)}")
        return filtered


signal_filter_analyzer = SignalFilterAnalyzer()
