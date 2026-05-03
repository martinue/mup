from typing import List, Optional
from datetime import datetime
from loguru import logger
from core.models import Quote, Kline, News, MarketData
from data.sources import tushare_source, eastmoney_source, cls_news_source, social_media_source
from data import storage


class DataProcessor:
    def __init__(self):
        self.tushare = tushare_source
        self.eastmoney = eastmoney_source
        self.cls_news = cls_news_source
        self.social_media = social_media_source
    
    def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[Quote]:
        quote = self.eastmoney.get_realtime_quote(symbol)
        
        if quote is None and self.tushare.is_available():
            quote = self.tushare.get_realtime_quote(symbol)
        
        if quote:
            logger.info(f"[数据] 获取 {symbol} 行情: 价格 {quote.price}, 涨跌 {quote.change_pct:.2f}%")
        
        return quote
    
    def get_klines(self, symbol: str, days: int = 30) -> List[Kline]:
        klines = self.eastmoney.get_history_klines(symbol, days)
        
        if not klines and self.tushare.is_available():
            klines = self.tushare.get_history_klines(symbol, days)
        
        return klines
    
    def get_market_data(self, symbol: str) -> MarketData:
        index_data = self.eastmoney.get_index_data()
        if not index_data and self.tushare.is_available():
            index_data = self.tushare.get_index_data()
        
        north_flow = 0.0
        if self.tushare.is_available():
            north_flow = self.tushare.get_north_flow()
        
        quote = self.get_quote(symbol)
        klines = self.get_klines(symbol, 30)
        
        change_20d = 0.0
        volatility = 0.0
        
        if len(klines) >= 20:
            prices = [k.close for k in klines[-20:]]
            change_20d = (prices[-1] - prices[0]) / prices[0] * 100
            
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 * 100
        
        return MarketData(
            index_value=index_data.get("index_value", 0),
            index_change=index_data.get("index_change", 0),
            volume=index_data.get("volume", 0),
            north_flow=north_flow,
            symbol=symbol,
            price=quote.price if quote else 0,
            change_20d=change_20d,
            volatility=volatility
        )
    
    def get_news(self, limit: int = 50, use_cache: bool = True) -> List[News]:
        news_list = self.cls_news.get_latest_news(limit)
        
        for news in news_list:
            storage.save_news(
                source=news.source,
                title=news.title,
                content=news.content,
                publish_time=news.publish_time
            )
        
        return news_list
    
    def get_market_news(self, limit: int = 20) -> List[News]:
        return self.cls_news.get_market_news()
    
    def calculate_volatility(self, klines: List[Kline], period: int = 20) -> float:
        if len(klines) < period:
            return 0.0
        
        prices = [k.close for k in klines[-period:]]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 * 100
        return volatility
    
    def calculate_ma(self, klines: List[Kline], period: int = 20) -> float:
        if len(klines) < period:
            return 0.0
        
        prices = [k.close for k in klines[-period:]]
        return sum(prices) / len(prices)


data_processor = DataProcessor()
