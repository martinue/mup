from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime


class RiskConfig(BaseModel):
    max_single_position_pct: float = 0.10
    max_daily_position_pct: float = 0.50
    max_total_position_pct: float = 0.80
    
    max_daily_loss_pct: float = 0.05
    max_total_loss_pct: float = 0.15
    
    max_trades_per_day: int = 10
    min_trade_interval_minutes: int = 30
    
    allowed_symbols: List[str] = ["510300"]
    
    price_change_alert_pct: float = 0.05
    price_change_limit_pct: float = 0.10
    
    class Config:
        frozen = True


class RiskCheckResult(BaseModel):
    passed: bool
    check_type: str
    message: str
    timestamp: datetime = datetime.now()


class RiskStatus(BaseModel):
    is_frozen: bool = False
    freeze_reason: str = ""
    daily_loss: float = 0.0
    total_loss: float = 0.0
    daily_trades: int = 0
    last_trade_time: datetime = None


risk_config = RiskConfig()
