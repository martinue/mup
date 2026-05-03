from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel
from core.models import Signal, OrderSide, MarketEnv, Quote
from data import storage


class GridConfig(BaseModel):
    symbol: str = "510300"
    base_price: float = 0.0
    grid_spacing: float = 0.03
    grid_amount: float = 1000.0
    take_profit: float = 0.08
    stop_loss: float = 0.10
    max_grids: int = 10


class GridStrategy:
    def __init__(self, config: GridConfig):
        self.config = config
        self.grids: List[dict] = []
        self._load_grids()
    
    def _load_grids(self):
        active_grids = storage.get_active_grids(self.config.symbol)
        self.grids = [
            {
                "level": g.grid_level,
                "buy_price": g.buy_price,
                "buy_amount": g.buy_amount,
                "buy_quantity": g.buy_quantity,
                "id": g.id
            }
            for g in active_grids
        ]
        logger.info(f"[网格] 加载 {len(self.grids)} 个活跃网格")
    
    def calculate_signals(self, current_price: float) -> List[Signal]:
        signals = []
        
        if self.config.base_price == 0:
            logger.warning("[网格] 基准价未设置，无法计算信号")
            return signals
        
        deviation = (current_price - self.config.base_price) / self.config.base_price
        logger.debug(f"[网格] 当前价格 {current_price}, 基准价 {self.config.base_price}, 偏离度 {deviation:.2%}")
        
        if deviation <= -self.config.grid_spacing:
            buy_signal = self._generate_buy_signal(current_price, deviation)
            if buy_signal:
                signals.append(buy_signal)
        
        if self.grids and deviation >= self.config.grid_spacing:
            sell_signal = self._generate_sell_signal(current_price, deviation)
            if sell_signal:
                signals.append(sell_signal)
        
        return signals
    
    def _generate_buy_signal(self, current_price: float, deviation: float) -> Optional[Signal]:
        if len(self.grids) >= self.config.max_grids:
            logger.warning(f"[网格] 已达最大网格数 {self.config.max_grids}")
            return None
        
        next_level = len(self.grids) + 1
        trigger_price = self.config.base_price * (1 - self.config.grid_spacing * next_level)
        
        if current_price > trigger_price:
            return None
        
        signal = Signal(
            symbol=self.config.symbol,
            signal_type=OrderSide.BUY,
            trigger_price=trigger_price,
            current_price=current_price,
            deviation=deviation,
            grid_level=next_level
        )
        
        logger.info(f"[网格] 生成买入信号: 价格 {current_price}, 网格层级 {next_level}")
        return signal
    
    def _generate_sell_signal(self, current_price: float, deviation: float) -> Optional[Signal]:
        if not self.grids:
            return None
        
        last_grid = self.grids[-1]
        sell_trigger = last_grid["buy_price"] * (1 + self.config.grid_spacing)
        
        if current_price < sell_trigger:
            return None
        
        signal = Signal(
            symbol=self.config.symbol,
            signal_type=OrderSide.SELL,
            trigger_price=sell_trigger,
            current_price=current_price,
            deviation=deviation,
            grid_level=last_grid["level"]
        )
        
        logger.info(f"[网格] 生成卖出信号: 价格 {current_price}, 网格层级 {last_grid['level']}")
        return signal
    
    def execute_buy(self, price: float, quantity: float, amount: float, grid_level: int):
        grid_record = storage.save_grid_record(
            symbol=self.config.symbol,
            grid_level=grid_level,
            buy_price=price,
            buy_amount=amount,
            buy_quantity=quantity
        )
        
        self.grids.append({
            "level": grid_level,
            "buy_price": price,
            "buy_amount": amount,
            "buy_quantity": quantity,
            "id": grid_record.id
        })
        
        logger.info(f"[网格] 执行买入: 价格 {price}, 数量 {quantity}, 金额 {amount}, 层级 {grid_level}")
    
    def execute_sell(self, price: float, quantity: float, amount: float, grid_level: int) -> float:
        grid_to_sell = None
        for grid in self.grids:
            if grid["level"] == grid_level:
                grid_to_sell = grid
                break
        
        if not grid_to_sell:
            logger.warning(f"[网格] 未找到层级 {grid_level} 的网格")
            return 0
        
        profit = amount - grid_to_sell["buy_amount"]
        
        storage.close_grid(
            grid_id=grid_to_sell["id"],
            sell_price=price,
            sell_amount=amount,
            profit=profit
        )
        
        self.grids.remove(grid_to_sell)
        
        logger.info(f"[网格] 执行卖出: 价格 {price}, 数量 {quantity}, 金额 {amount}, 盈亏 {profit:.2f}")
        return profit
    
    def update_base_price(self, new_base: float):
        old_base = self.config.base_price
        self.config.base_price = new_base
        logger.info(f"[网格] 更新基准价: {old_base} -> {new_base}")
    
    def adjust_parameters(self, market_env: MarketEnv, confidence: float = 0.8):
        if market_env == MarketEnv.BEAR:
            self.config.grid_spacing = 0.05
            self.config.grid_amount = 500
            logger.info("[网格] 熊市调整: 网格间距 5%, 每格金额 500")
        elif market_env == MarketEnv.BULL:
            self.config.grid_spacing = 0.06
            logger.info("[网格] 牛市调整: 网格间距 6%")
        else:
            self.config.grid_spacing = 0.03
            self.config.grid_amount = 1000
            logger.info("[网格] 震荡市调整: 网格间距 3%, 每格金额 1000")
    
    def get_grid_status(self) -> dict:
        total_invested = sum(g["buy_amount"] for g in self.grids)
        total_quantity = sum(g["buy_quantity"] for g in self.grids)
        avg_cost = total_invested / total_quantity if total_quantity > 0 else 0
        
        return {
            "symbol": self.config.symbol,
            "base_price": self.config.base_price,
            "grid_spacing": self.config.grid_spacing,
            "grid_amount": self.config.grid_amount,
            "active_grids": len(self.grids),
            "total_invested": total_invested,
            "total_quantity": total_quantity,
            "avg_cost": avg_cost,
            "grids": self.grids
        }
    
    def calculate_base_price_from_history(self, quotes: List[Quote]) -> float:
        if not quotes:
            return self.config.base_price
        
        prices = [q.price for q in quotes[-20:]]
        avg_price = sum(prices) / len(prices)
        return round(avg_price, 3)


def create_grid_strategy(symbol: str = "510300", base_price: float = 0.0) -> GridStrategy:
    config = GridConfig(symbol=symbol, base_price=base_price)
    return GridStrategy(config)
