from typing import Optional
from loguru import logger
from llm.client import LLMClient, get_llm_client
from config.prompts import VALUATION_PROMPT
from core.models import ValuationResult
from data import storage


class ValuationAnalyzer:
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or get_llm_client()
    
    def analyze(self, symbol: str, pe: float, pe_percentile: float,
                pb: float, pb_percentile: float, dividend_yield: float) -> ValuationResult:
        if not self.llm.is_available:
            logger.warning("[估值分析] LLM不可用，返回默认结果")
            return self._default_result(symbol)
        
        data = {
            "symbol": symbol,
            "pe": pe,
            "pe_percentile": pe_percentile,
            "pb": pb,
            "pb_percentile": pb_percentile,
            "dividend_yield": dividend_yield
        }
        
        result = self.llm.analyze_json(VALUATION_PROMPT, data)
        
        if result is None:
            return self._default_result(symbol)
        
        try:
            valuation_result = ValuationResult(
                valuation=result.get("valuation", "合理"),
                suggestion=float(result.get("suggestion", 1.0)),
                reason=result.get("reason", "")
            )
            
            storage.save_llm_analysis(
                analysis_type="valuation",
                input_data=str(data),
                output_data=str(result),
                model=self.llm.provider
            )
            
            logger.info(f"[估值分析] 结果: {valuation_result.valuation}, 建议: {valuation_result.suggestion}")
            return valuation_result
            
        except Exception as e:
            logger.error(f"[估值分析] 解析结果失败: {e}")
            return self._default_result(symbol)
    
    def _default_result(self, symbol: str) -> ValuationResult:
        return ValuationResult(
            valuation="合理",
            suggestion=1.0,
            reason="使用默认估值"
        )
    
    def get_investment_ratio(self, valuation: str, suggestion: float) -> float:
        if valuation == "低估":
            return min(1.0, suggestion)
        elif valuation == "高估":
            return min(0.5, suggestion)
        else:
            return min(0.8, suggestion)


valuation_analyzer = ValuationAnalyzer()
