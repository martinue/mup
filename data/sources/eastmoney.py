from typing import List, Optional
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
from loguru import logger
from core.models import Quote, Kline, News


class EastMoneyDataSource:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://quote.eastmoney.com/"
        }
        self.quote_url = "https://push2.eastmoney.com/api/qt/stock/get"
        self.kline_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        logger.info("[东方财富] 初始化成功")
    
    def _get_secid(self, symbol: str) -> str:
        if symbol.startswith("5"):
            return f"1.{symbol}"
        elif symbol.startswith("0") or symbol.startswith("3"):
            return f"0.{symbol}"
        return f"1.{symbol}"
    
    def get_realtime_quote(self, symbol: str) -> Optional[Quote]:
        try:
            secid = self._get_secid(symbol)
            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f58,f60,f169,f170",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b"
            }
            
            response = requests.get(self.quote_url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            if data.get("data") is None:
                return None
            
            d = data["data"]
            return Quote(
                symbol=symbol,
                name="",
                price=d.get("f43", 0) / 1000 if d.get("f43") else 0,
                change=d.get("f169", 0) / 1000 if d.get("f169") else 0,
                change_pct=d.get("f170", 0) / 100 if d.get("f170") else 0,
                volume=d.get("f47", 0),
                amount=d.get("f48", 0),
                high=d.get("f44", 0) / 1000 if d.get("f44") else 0,
                low=d.get("f45", 0) / 1000 if d.get("f45") else 0,
                open=d.get("f46", 0) / 1000 if d.get("f46") else 0,
                pre_close=d.get("f60", 0) / 1000 if d.get("f60") else 0
            )
        except Exception as e:
            logger.error(f"[东方财富] 获取实时行情失败: {e}")
            return None
    
    def get_history_klines(self, symbol: str, days: int = 30) -> List[Kline]:
        try:
            secid = self._get_secid(symbol)
            params = {
                "secid": secid,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57",
                "klt": "101",
                "fqt": "1",
                "end": "20500101",
                "lmt": str(days)
            }
            
            response = requests.get(self.kline_url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            if data.get("data") is None or data["data"].get("klines") is None:
                return []
            
            klines = []
            for line in data["data"]["klines"]:
                parts = line.split(",")
                klines.append(Kline(
                    symbol=symbol,
                    date=parts[0],
                    open=float(parts[1]),
                    close=float(parts[2]),
                    high=float(parts[3]),
                    low=float(parts[4]),
                    volume=float(parts[5]),
                    amount=float(parts[6])
                ))
            
            logger.info(f"[东方财富] 获取 {symbol} 历史 {len(klines)} 条K线")
            return klines
        except Exception as e:
            logger.error(f"[东方财富] 获取历史K线失败: {e}")
            return []
    
    def get_index_data(self) -> dict:
        try:
            params = {
                "secid": "1.000001",
                "fields": "f43,f169,f170,f47,f48",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b"
            }
            
            response = requests.get(self.quote_url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            if data.get("data") is None:
                return {}
            
            d = data["data"]
            return {
                "index_value": d.get("f43", 0) / 100,
                "index_change": d.get("f170", 0) / 100 if d.get("f170") else 0,
                "volume": d.get("f47", 0) / 1e8,
                "amount": d.get("f48", 0) / 1e8
            }
        except Exception as e:
            logger.error(f"[东方财富] 获取指数数据失败: {e}")
            return {}


eastmoney_source = EastMoneyDataSource()
