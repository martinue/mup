from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from loguru import logger
import tushare as ts
from config.settings import settings
from core.models import Quote, Kline, News


class DataSource(ABC):
    @abstractmethod
    def get_realtime_quote(self, symbol: str) -> Optional[Quote]:
        pass
    
    @abstractmethod
    def get_history_klines(self, symbol: str, days: int = 30) -> List[Kline]:
        pass


class NewsSource(ABC):
    @abstractmethod
    def get_latest_news(self, limit: int = 50) -> List[News]:
        pass


class TushareDataSource(DataSource):
    def __init__(self, token: str = None):
        self.token = token or settings.TUSHARE_TOKEN
        if self.token:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            logger.info("[Tushare] 初始化成功")
        else:
            self.pro = None
            logger.warning("[Tushare] 未配置Token，数据源不可用")
    
    def is_available(self) -> bool:
        return self.pro is not None
    
    def get_realtime_quote(self, symbol: str) -> Optional[Quote]:
        if not self.is_available():
            return None
        
        try:
            df = ts.get_realtime_quotes(symbol)
            if df is None or df.empty:
                return None
            
            row = df.iloc[0]
            return Quote(
                symbol=symbol,
                name=row.get('name', symbol),
                price=float(row.get('price', 0)),
                change=float(row.get('b1_p', 0)) - float(row.get('pre_close', 0)),
                change_pct=(float(row.get('price', 0)) - float(row.get('pre_close', 0))) / float(row.get('pre_close', 1)) * 100,
                volume=float(row.get('volume', 0)),
                amount=float(row.get('amount', 0)),
                high=float(row.get('high', 0)),
                low=float(row.get('low', 0)),
                open=float(row.get('open', 0)),
                pre_close=float(row.get('pre_close', 0))
            )
        except Exception as e:
            logger.error(f"[Tushare] 获取实时行情失败: {e}")
            return None
    
    def get_history_klines(self, symbol: str, days: int = 30) -> List[Kline]:
        if not self.is_available():
            return []
        
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - __import__('datetime').timedelta(days=days)).strftime('%Y%m%d')
            
            df = self.pro.fund_daily(
                ts_code=f"{symbol}.OF",
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                df = ts.get_k_data(symbol, start=start_date, end=end_date)
            
            if df is None or df.empty:
                return []
            
            klines = []
            for _, row in df.iterrows():
                klines.append(Kline(
                    symbol=symbol,
                    date=str(row.get('trade_date', row.get('date', ''))),
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    volume=float(row.get('vol', row.get('volume', 0))),
                    amount=float(row.get('amount', 0))
                ))
            
            logger.info(f"[Tushare] 获取 {symbol} 历史 {len(klines)} 条K线")
            return klines
        except Exception as e:
            logger.error(f"[Tushare] 获取历史K线失败: {e}")
            return []
    
    def get_index_data(self, index_code: str = "000001.SH") -> dict:
        if not self.is_available():
            return {}
        
        try:
            df = self.pro.index_daily(ts_code=index_code)
            if df is None or df.empty:
                return {}
            
            row = df.iloc[0]
            return {
                "index_value": float(row.get('close', 0)),
                "index_change": float(row.get('pct_chg', 0)),
                "volume": float(row.get('vol', 0)) / 1e8,
                "amount": float(row.get('amount', 0)) / 1e8
            }
        except Exception as e:
            logger.error(f"[Tushare] 获取指数数据失败: {e}")
            return {}
    
    def get_north_flow(self) -> float:
        if not self.is_available():
            return 0.0
        
        try:
            df = ts.moneyflow_hsgt()
            if df is None or df.empty:
                return 0.0
            
            row = df.iloc[0]
            return float(row.get('north_money', 0))
        except Exception as e:
            logger.error(f"[Tushare] 获取北向资金失败: {e}")
            return 0.0


tushare_source = TushareDataSource()
