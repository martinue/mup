from typing import List, Optional
from datetime import datetime
from loguru import logger
from core.models import Quote, Kline, News, MarketData
from data.sources import tushare_source, eastmoney_source, cls_news_source
from data import storage


class DataValidator:
    @staticmethod
    def validate_quote(quote: Quote) -> bool:
        if quote is None:
            return False
        
        if quote.price <= 0:
            return False
        
        if quote.volume < 0 or quote.amount < 0:
            return False
        
        return True
    
    @staticmethod
    def validate_kline(kline: Kline) -> bool:
        if kline is None:
            return False
        
        if kline.open <= 0 or kline.close <= 0:
            return False
        
        if kline.high < kline.low:
            return False
        
        if kline.high < kline.open or kline.high < kline.close:
            return False
        
        if kline.low > kline.open or kline.low > kline.close:
            return False
        
        return True
    
    @staticmethod
    def validate_news(news: News) -> bool:
        if news is None:
            return False
        
        if not news.title and not news.content:
            return False
        
        return True
    
    @staticmethod
    def compare_quotes(quote1: Quote, quote2: Quote, tolerance: float = 0.01) -> bool:
        if quote1 is None or quote2 is None:
            return False
        
        price_diff = abs(quote1.price - quote2.price) / quote1.price
        
        return price_diff <= tolerance


validator = DataValidator()
