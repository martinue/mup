from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Order(BaseModel):
    symbol: str
    side: OrderSide
    price: float
    quantity: float
    amount: float
    
    class Config:
        use_enum_values = True


class Signal(BaseModel):
    symbol: str
    signal_type: OrderSide
    trigger_price: float
    current_price: float
    deviation: float
    grid_level: int
    timestamp: datetime = datetime.now()
    
    def to_order(self) -> Order:
        return Order(
            symbol=self.symbol,
            side=self.signal_type,
            price=self.current_price,
            quantity=0,
            amount=0
        )


class MarketEnv(str, Enum):
    OSCILLATION = "震荡市"
    BULL = "单边牛市"
    BEAR = "单边熊市"


class MarketEnvResult(BaseModel):
    env_type: MarketEnv
    confidence: float
    reason: str


class FilterResult(BaseModel):
    decision: str
    reason: str
    
    @property
    def passed(self) -> bool:
        return self.decision == "pass"


class AlertLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskAlertResult(BaseModel):
    risk_level: AlertLevel
    affected_symbols: list[str]
    reason: str


class ValuationResult(BaseModel):
    valuation: str
    suggestion: float
    reason: str


class Quote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: float
    amount: float
    high: float
    low: float
    open: float
    pre_close: float
    timestamp: datetime = datetime.now()


class Kline(BaseModel):
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


class News(BaseModel):
    title: str
    content: str
    source: str
    publish_time: datetime
    sentiment: Optional[str] = None
    risk_level: Optional[str] = None


class MarketData(BaseModel):
    index_value: float
    index_change: float
    volume: float
    north_flow: float
    symbol: str
    price: float
    change_20d: float
    volatility: float
    
    def to_dict(self) -> dict:
        return {
            "index_value": self.index_value,
            "index_change": self.index_change,
            "volume": self.volume,
            "north_flow": self.north_flow,
            "symbol": self.symbol,
            "price": self.price,
            "change_20d": self.change_20d,
            "volatility": self.volatility
        }


class SignalContext(BaseModel):
    symbol: str
    signal_type: str
    trigger_price: float
    current_price: float
    deviation: float
    market_env: str
    news_summary: str
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "trigger_price": self.trigger_price,
            "current_price": self.current_price,
            "deviation": self.deviation,
            "market_env": self.market_env,
            "news_summary": self.news_summary
        }
