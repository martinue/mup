from typing import Optional, List
from datetime import datetime
from loguru import logger

from config.settings import settings
from core.models import Order, Quote


class JoinQuantTrader:
    def __init__(self, account: str = None, password: str = None):
        self.account = account or settings.JQ_ACCOUNT
        self.password = password or settings.JQ_PASSWORD
        self.is_connected = False
        self._connect()
    
    def _connect(self):
        # 聚宽SDK暂时不用，直接使用模拟盘模式
        logger.info("[聚宽] 聚宽模式已禁用，使用模拟盘")
        self.is_connected = False
    
    def is_available(self) -> bool:
        return self.is_connected
    
    def get_account_info(self) -> dict:
        return {"total_value": 0, "available_cash": 0, "positions": []}
    
    def get_positions(self) -> List[dict]:
        return []
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        return None
    
    def place_order(self, order: Order) -> dict:
        return {"status": "failed", "message": "聚宽模式已禁用"}


joinquant_trader = JoinQuantTrader()
