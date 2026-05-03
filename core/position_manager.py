from typing import Optional, List
from datetime import datetime
from loguru import logger
from config.settings import settings
from core.models import Quote
from data import storage


class PositionManager:
    def __init__(self, initial_capital: float = None):
        self.initial_capital = initial_capital or settings.INITIAL_CAPITAL
        self.available_cash = self.initial_capital
        self.positions: dict = {}
        self._load_state()
    
    def _load_state(self):
        positions = storage.get_all_positions()
        for pos in positions:
            if pos.symbol not in self.positions:
                self.positions[pos.symbol] = {
                    "quantity": 0,
                    "cost_price": 0,
                    "market_value": 0
                }
            self.positions[pos.symbol]["quantity"] += pos.quantity
            self.positions[pos.symbol]["cost_price"] = pos.cost_price
        
        today = datetime.now().date().isoformat()
        stats = storage.get_daily_stats(today)
        if stats:
            self.available_cash = stats.available_cash
        
        logger.info(f"[仓位] 加载仓位: {self.positions}, 可用资金: {self.available_cash}")
    
    def get_total_capital(self, current_prices: dict) -> float:
        total_position = 0
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                total_position += pos["quantity"] * current_prices[symbol]
        return self.available_cash + total_position
    
    def get_position(self, symbol: str) -> Optional[dict]:
        return self.positions.get(symbol)
    
    def get_position_value(self, symbol: str, current_price: float) -> float:
        pos = self.positions.get(symbol)
        if not pos:
            return 0
        return pos["quantity"] * current_price
    
    def get_position_profit(self, symbol: str, current_price: float) -> dict:
        pos = self.positions.get(symbol)
        if not pos or pos["quantity"] == 0:
            return {"profit": 0, "profit_pct": 0}
        
        market_value = pos["quantity"] * current_price
        cost = pos["quantity"] * pos["cost_price"]
        profit = market_value - cost
        profit_pct = profit / cost if cost > 0 else 0
        
        return {"profit": profit, "profit_pct": profit_pct}
    
    def can_buy(self, amount: float) -> bool:
        return self.available_cash >= amount
    
    def buy(self, symbol: str, price: float, quantity: float, amount: float):
        if not self.can_buy(amount):
            raise ValueError(f"可用资金不足: {self.available_cash} < {amount}")
        
        self.available_cash -= amount
        
        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": 0, "cost_price": 0, "market_value": 0}
        
        old_quantity = self.positions[symbol]["quantity"]
        old_cost = self.positions[symbol]["cost_price"] * old_quantity
        new_cost = old_cost + amount
        new_quantity = old_quantity + quantity
        
        self.positions[symbol]["quantity"] = new_quantity
        self.positions[symbol]["cost_price"] = new_cost / new_quantity if new_quantity > 0 else 0
        self.positions[symbol]["market_value"] = new_quantity * price
        
        storage.save_position(
            symbol=symbol,
            quantity=quantity,
            cost_price=price,
            grid_level=0
        )
        
        logger.info(f"[仓位] 买入: {symbol} {quantity}股 @ {price}, 金额 {amount}")
    
    def sell(self, symbol: str, price: float, quantity: float, amount: float):
        if symbol not in self.positions:
            raise ValueError(f"无持仓: {symbol}")
        
        if self.positions[symbol]["quantity"] < quantity:
            raise ValueError(f"持仓不足: {self.positions[symbol]['quantity']} < {quantity}")
        
        self.available_cash += amount
        self.positions[symbol]["quantity"] -= quantity
        self.positions[symbol]["market_value"] = self.positions[symbol]["quantity"] * price
        
        if self.positions[symbol]["quantity"] == 0:
            self.positions[symbol]["cost_price"] = 0
        
        logger.info(f"[仓位] 卖出: {symbol} {quantity}股 @ {price}, 金额 {amount}")
    
    def update_prices(self, current_prices: dict):
        for symbol, price in current_prices.items():
            if symbol in self.positions:
                self.positions[symbol]["market_value"] = self.positions[symbol]["quantity"] * price
                storage.update_position_price(symbol, price)
    
    def save_daily_stats(self, current_prices: dict):
        today = datetime.now().date().isoformat()
        total_asset = self.get_total_capital(current_prices)
        total_position = sum(
            self.positions[s]["quantity"] * current_prices.get(s, 0)
            for s in self.positions
        )
        
        trades = storage.get_trades(limit=1000)
        today_trades = [t for t in trades if t.created_at.date() == datetime.now().date()]
        
        daily_profit = total_asset - self.initial_capital
        daily_profit_pct = daily_profit / self.initial_capital
        
        storage.save_daily_stats(
            date_str=today,
            total_asset=total_asset,
            total_position=total_position,
            available_cash=self.available_cash,
            daily_profit=daily_profit,
            daily_profit_pct=daily_profit_pct,
            trade_count=len(today_trades)
        )
        
        logger.info(f"[仓位] 保存每日统计: 总资产 {total_asset}, 持仓 {total_position}")
    
    def get_summary(self, current_prices: dict) -> dict:
        total_asset = self.get_total_capital(current_prices)
        total_position = 0
        total_profit = 0
        
        for symbol, pos in self.positions.items():
            if pos["quantity"] > 0:
                current_price = current_prices.get(symbol, pos["cost_price"])
                position_value = pos["quantity"] * current_price
                cost = pos["quantity"] * pos["cost_price"]
                
                total_position += position_value
                total_profit += position_value - cost
        
        return {
            "total_asset": total_asset,
            "total_position": total_position,
            "available_cash": self.available_cash,
            "total_profit": total_profit,
            "total_profit_pct": total_profit / self.initial_capital if self.initial_capital > 0 else 0,
            "positions": self.positions
        }


position_manager = PositionManager()
