from typing import List, Optional
from datetime import datetime
from loguru import logger
from config.settings import settings
from core.models import Signal, Order, OrderSide, MarketEnv
from core.grid_strategy import GridStrategy
from core.risk_manager import risk_manager
from core.position_manager import position_manager
from data.processors import data_processor
from llm.analyzers import (
    market_env_analyzer, signal_filter_analyzer,
    risk_alert_analyzer, valuation_analyzer
)
from trading.joinquant import joinquant_trader
from trading.paper_trading import paper_trading
from data import storage


class TradingExecutor:
    def __init__(self, strategy: GridStrategy, use_paper: bool = True):
        self.strategy = strategy
        self.use_paper = use_paper
        self.trader = paper_trading if use_paper else joinquant_trader
        self.market_env = MarketEnv.OSCILLATION
        self.last_execute_time = None
        logger.info(f"[执行器] 初始化完成, 模式: {'模拟盘' if use_paper else '实盘'}")
    
    def execute_cycle(self) -> dict:
        logger.info("[执行器] 开始执行交易周期")
        
        result = {
            "signals": [],
            "filtered_signals": [],
            "approved_signals": [],
            "trades": [],
            "market_env": None,
            "risk_alert": None
        }
        
        try:
            quote = data_processor.get_quote(self.strategy.config.symbol)
            if not quote:
                logger.warning("[执行器] 无法获取行情")
                return result
            
            current_price = quote.price
            
            market_data = data_processor.get_market_data(self.strategy.config.symbol)
            env_result = market_env_analyzer.analyze(market_data)
            self.market_env = env_result.env_type
            result["market_env"] = env_result.model_dump()
            
            self.strategy.adjust_parameters(env_result.env_type, env_result.confidence)
            
            news_list = data_processor.get_news(20)
            alert_result = risk_alert_analyzer.analyze(news_list)
            result["risk_alert"] = alert_result.model_dump()
            
            if alert_result.risk_level.value == "high":
                risk_manager.handle_risk_alert(alert_result.risk_level)
                logger.warning("[执行器] 高风险预警，暂停交易")
                return result
            
            signals = self.strategy.calculate_signals(current_price)
            result["signals"] = [s.model_dump() for s in signals]
            
            if not signals:
                logger.info("[执行器] 无交易信号")
                return result
            
            news_summary = "\n".join([n.title for n in news_list[:5]])
            filtered_signals = signal_filter_analyzer.batch_filter(
                signals, self.market_env.value, news_summary
            )
            result["filtered_signals"] = [s.model_dump() for s in filtered_signals]
            
            account = self.trader.get_account_info()
            total_capital = account.get("total_value", settings.INITIAL_CAPITAL)
            
            approved_signals = []
            for signal in filtered_signals:
                order = self._create_order(signal, current_price)
                check_result = risk_manager.check_order(order, total_capital)
                
                if check_result.passed:
                    approved_signals.append(signal)
                else:
                    logger.warning(f"[执行器] 信号被风控拒绝: {check_result.message}")
            
            result["approved_signals"] = [s.model_dump() for s in approved_signals]
            
            for signal in approved_signals:
                trade_result = self._execute_signal(signal, current_price)
                result["trades"].append(trade_result)
            
            self.last_execute_time = datetime.now()
            
        except Exception as e:
            logger.error(f"[执行器] 执行异常: {e}")
        
        return result
    
    def _create_order(self, signal: Signal, current_price: float) -> Order:
        if signal.signal_type == OrderSide.BUY:
            amount = self.strategy.config.grid_amount
            quantity = amount / current_price
        else:
            quantity = 0
            for grid in self.strategy.grids:
                if grid["level"] == signal.grid_level:
                    quantity = grid["buy_quantity"]
                    break
            amount = quantity * current_price
        
        return Order(
            symbol=signal.symbol,
            side=signal.signal_type,
            price=current_price,
            quantity=quantity,
            amount=amount
        )
    
    def _execute_signal(self, signal: Signal, current_price: float) -> dict:
        order = self._create_order(signal, current_price)
        
        trade_result = self.trader.place_order(order)
        
        if trade_result.get("status") == "success":
            if signal.signal_type == OrderSide.BUY:
                self.strategy.execute_buy(
                    price=current_price,
                    quantity=order.quantity,
                    amount=order.amount,
                    grid_level=signal.grid_level
                )
                position_manager.buy(
                    symbol=signal.symbol,
                    price=current_price,
                    quantity=order.quantity,
                    amount=order.amount
                )
            else:
                profit = self.strategy.execute_sell(
                    price=current_price,
                    quantity=order.quantity,
                    amount=order.amount,
                    grid_level=signal.grid_level
                )
                position_manager.sell(
                    symbol=signal.symbol,
                    price=current_price,
                    quantity=order.quantity,
                    amount=order.amount
                )
                risk_manager.record_trade(profit)
            
            storage.save_trade(
                symbol=signal.symbol,
                side=signal.signal_type,
                price=current_price,
                quantity=order.quantity,
                amount=order.amount,
                signal_source="grid_strategy",
                risk_check="passed"
            )
            
            logger.info(f"[执行器] 交易成功: {signal.signal_type} {signal.symbol}")
        else:
            logger.error(f"[执行器] 交易失败: {trade_result}")
        
        return trade_result
    
    def get_status(self) -> dict:
        account = self.trader.get_account_info()
        grid_status = self.strategy.get_grid_status()
        risk_state = storage.get_risk_state()
        
        return {
            "account": account,
            "grid": grid_status,
            "risk": {
                "is_frozen": risk_state.is_frozen,
                "freeze_reason": risk_state.freeze_reason,
                "daily_loss": risk_state.daily_loss,
                "daily_trades": risk_state.daily_trades
            },
            "market_env": self.market_env.value,
            "last_execute_time": self.last_execute_time.isoformat() if self.last_execute_time else None
        }
    
    def reset_daily(self):
        risk_manager.reset_daily()
        logger.info("[执行器] 每日重置完成")


def create_executor(symbol: str = "510300", base_price: float = 0.0, 
                    use_paper: bool = True) -> TradingExecutor:
    from core.grid_strategy import create_grid_strategy
    strategy = create_grid_strategy(symbol, base_price)
    return TradingExecutor(strategy, use_paper)
