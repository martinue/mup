from typing import Optional, List
from datetime import datetime
from loguru import logger
from core.models import Order, Quote
from data import storage


class PaperTrading:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.available_cash = initial_capital
        self.positions: dict = {}
        self.trades: List[dict] = []
        logger.info(f"[模拟盘] 初始化成功，初始资金: {initial_capital}")
    
    def get_account_info(self) -> dict:
        total_position = sum(
            pos["quantity"] * pos["current_price"]
            for pos in self.positions.values()
        )
        return {
            "total_value": self.available_cash + total_position,
            "available_cash": self.available_cash,
            "positions": list(self.positions.values())
        }
    
    def get_positions(self) -> List[dict]:
        return list(self.positions.values())
    
    def update_price(self, symbol: str, price: float):
        if symbol in self.positions:
            self.positions[symbol]["current_price"] = price
            self.positions[symbol]["market_value"] = self.positions[symbol]["quantity"] * price
    
    def place_order(self, order: Order) -> dict:
        if order.side == "buy":
            return self._buy(order)
        else:
            return self._sell(order)
    
    def _buy(self, order: Order) -> dict:
        if order.amount > self.available_cash:
            logger.warning(f"[模拟盘] 资金不足: {self.available_cash} < {order.amount}")
            return {"status": "failed", "message": "资金不足"}
        
        quantity = order.amount / order.price
        self.available_cash -= order.amount
        
        if order.symbol not in self.positions:
            self.positions[order.symbol] = {
                "symbol": order.symbol,
                "quantity": 0,
                "cost_price": 0,
                "current_price": order.price,
                "market_value": 0
            }
        
        pos = self.positions[order.symbol]
        old_value = pos["quantity"] * pos["cost_price"]
        new_value = old_value + order.amount
        pos["quantity"] += quantity
        pos["cost_price"] = new_value / pos["quantity"]
        pos["current_price"] = order.price
        pos["market_value"] = pos["quantity"] * order.price
        
        trade = {
            "symbol": order.symbol,
            "side": "buy",
            "price": order.price,
            "quantity": quantity,
            "amount": order.amount,
            "time": datetime.now()
        }
        self.trades.append(trade)
        
        logger.info(f"[模拟盘] 买入: {order.symbol} {quantity:.2f}股 @ {order.price}")
        return {"status": "success", "quantity": quantity}
    
    def _sell(self, order: Order) -> dict:
        if order.symbol not in self.positions:
            logger.warning(f"[模拟盘] 无持仓: {order.symbol}")
            return {"status": "failed", "message": "无持仓"}
        
        pos = self.positions[order.symbol]
        if pos["quantity"] < order.quantity:
            logger.warning(f"[模拟盘] 持仓不足: {pos['quantity']} < {order.quantity}")
            return {"status": "failed", "message": "持仓不足"}
        
        sell_amount = order.quantity * order.price
        self.available_cash += sell_amount
        
        pos["quantity"] -= order.quantity
        pos["market_value"] = pos["quantity"] * order.price
        
        if pos["quantity"] <= 0:
            del self.positions[order.symbol]
        
        trade = {
            "symbol": order.symbol,
            "side": "sell",
            "price": order.price,
            "quantity": order.quantity,
            "amount": sell_amount,
            "time": datetime.now()
        }
        self.trades.append(trade)
        
        logger.info(f"[模拟盘] 卖出: {order.symbol} {order.quantity:.2f}股 @ {order.price}")
        return {"status": "success", "amount": sell_amount}
    
    def get_trade_history(self, limit: int = 100) -> List[dict]:
        return self.trades[-limit:]
    
    def reset(self):
        self.available_cash = self.initial_capital
        self.positions = {}
        self.trades = []
        logger.info("[模拟盘] 已重置")


paper_trading = PaperTrading()
