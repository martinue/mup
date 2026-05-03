from typing import List, Optional
from loguru import logger
from llm.client import LLMClient, get_llm_client
from config.prompts import RISK_ALERT_PROMPT
from core.models import News, AlertLevel, RiskAlertResult
from data import storage


class RiskAlertAnalyzer:
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or get_llm_client()
    
    def analyze(self, news_list: List[News]) -> RiskAlertResult:
        if not news_list:
            return RiskAlertResult(
                risk_level=AlertLevel.LOW,
                affected_symbols=[],
                reason="无新闻数据"
            )
        
        if not self.llm.is_available:
            logger.warning("[风险预警] LLM不可用，返回低风险")
            return RiskAlertResult(
                risk_level=AlertLevel.LOW,
                affected_symbols=[],
                reason="LLM不可用"
            )
        
        news_text = "\n".join([
            f"- [{n.publish_time.strftime('%Y-%m-%d %H:%M')}] {n.title}"
            for n in news_list[:20]
        ])
        
        result = self.llm.analyze_json(RISK_ALERT_PROMPT, {"news_list": news_text})
        
        if result is None:
            return RiskAlertResult(
                risk_level=AlertLevel.LOW,
                affected_symbols=[],
                reason="LLM解析失败"
            )
        
        try:
            risk_level_str = result.get("risk_level", "low").lower()
            risk_level = AlertLevel.LOW
            if risk_level_str == "high":
                risk_level = AlertLevel.HIGH
            elif risk_level_str == "medium":
                risk_level = AlertLevel.MEDIUM
            
            alert_result = RiskAlertResult(
                risk_level=risk_level,
                affected_symbols=result.get("affected_symbols", []),
                reason=result.get("reason", "")
            )
            
            storage.save_llm_analysis(
                analysis_type="risk_alert",
                input_data=news_text,
                output_data=str(result),
                model=self.llm.provider
            )
            
            logger.info(f"[风险预警] 等级: {risk_level.value}, 理由: {alert_result.reason}")
            return alert_result
            
        except Exception as e:
            logger.error(f"[风险预警] 解析结果失败: {e}")
            return RiskAlertResult(
                risk_level=AlertLevel.LOW,
                affected_symbols=[],
                reason=f"解析失败: {e}"
            )
    
    def check_keywords(self, news_list: List[News], 
                       high_keywords: List[str] = None,
                       medium_keywords: List[str] = None) -> AlertLevel:
        if not high_keywords:
            high_keywords = ["暴跌", "熔断", "崩盘", "战争", "制裁", "金融危机", "黑天鹅"]
        if not medium_keywords:
            medium_keywords = ["下跌", "调整", "风险", "警告", "监管", "政策收紧"]
        
        for news in news_list:
            text = f"{news.title} {news.content}"
            for keyword in high_keywords:
                if keyword in text:
                    logger.warning(f"[风险预警] 发现高风险关键词: {keyword}")
                    return AlertLevel.HIGH
            
            for keyword in medium_keywords:
                if keyword in text:
                    logger.warning(f"[风险预警] 发现中风险关键词: {keyword}")
                    return AlertLevel.MEDIUM
        
        return AlertLevel.LOW


risk_alert_analyzer = RiskAlertAnalyzer()
