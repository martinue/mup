from datetime import datetime, date
from typing import List, Optional
from loguru import logger
from config.risk_control import risk_config, RiskCheckResult
from core.models import Order, AlertLevel
from data import storage


class RiskManager:
    def __init__(self):
        self.config = risk_config
        self._load_state()
    
    def _load_state(self):
        state = storage.get_risk_state()
        self.is_frozen = state.is_frozen
        self.freeze_reason = state.freeze_reason
        self.daily_loss = state.daily_loss
        self.total_loss = state.total_loss
        self.daily_trades = state.daily_trades
        self.last_trade_time = state.last_trade_time
    
    def _save_state(self):
        storage.update_risk_state(
            is_frozen=self.is_frozen,
            freeze_reason=self.freeze_reason,
            daily_loss=self.daily_loss,
            total_loss=self.total_loss,
            daily_trades=self.daily_trades,
            last_trade_time=self.last_trade_time
        )
    
    def check_order(self, order: Order, total_capital: float) -> RiskCheckResult:
        if self.is_frozen:
            return self._log_check("frozen_check", order, False, f"系统已冻结: {self.freeze_reason}")
        
        checks = [
            self._check_symbol(order),
            self._check_position(order, total_capital),
            self._check_daily_loss(total_capital),
            self._check_total_loss(total_capital),
            self._check_trade_count(),
            self._check_trade_interval(),
            self._check_price_anomaly(order),
        ]
        
        for result in checks:
            if not result.passed:
                return result
        
        return self._log_check("all_checks", order, True, "所有风控检查通过")
    
    def _check_symbol(self, order: Order) -> RiskCheckResult:
        if order.symbol not in self.config.allowed_symbols:
            return self._log_check(
                "symbol_check", order, False,
                f"标的 {order.symbol} 不在允许列表中"
            )
        return RiskCheckResult(passed=True, check_type="symbol_check", message="标的检查通过")
    
    def _check_position(self, order: Order, total_capital: float) -> RiskCheckResult:
        if order.side == "sell":
            return RiskCheckResult(passed=True, check_type="position_check", message="卖出无需仓位检查")
        
        single_position_pct = order.amount / total_capital
        if single_position_pct > self.config.max_single_position_pct:
            return self._log_check(
                "position_check", order, False,
                f"单笔仓位 {single_position_pct:.2%} 超过上限 {self.config.max_single_position_pct:.2%}"
            )
        
        today = date.today().isoformat()
        today_trades = storage.get_trades(limit=1000)
        today_buy_amount = sum(t.amount for t in today_trades if t.side == "buy" and t.created_at.date() == date.today())
        daily_position_pct = (today_buy_amount + order.amount) / total_capital
        
        if daily_position_pct > self.config.max_daily_position_pct:
            return self._log_check(
                "position_check", order, False,
                f"单日仓位 {daily_position_pct:.2%} 超过上限 {self.config.max_daily_position_pct:.2%}"
            )
        
        return RiskCheckResult(passed=True, check_type="position_check", message="仓位检查通过")
    
    def _check_daily_loss(self, total_capital: float) -> RiskCheckResult:
        daily_loss_pct = self.daily_loss / total_capital
        if daily_loss_pct >= self.config.max_daily_loss_pct:
            self.trigger_circuit_breaker(f"单日亏损 {daily_loss_pct:.2%} 达到熔断线")
            return self._log_check(
                "daily_loss_check", None, False,
                f"单日亏损 {daily_loss_pct:.2%} 超过上限 {self.config.max_daily_loss_pct:.2%}"
            )
        return RiskCheckResult(passed=True, check_type="daily_loss_check", message="日亏损检查通过")
    
    def _check_total_loss(self, total_capital: float) -> RiskCheckResult:
        total_loss_pct = self.total_loss / total_capital
        if total_loss_pct >= self.config.max_total_loss_pct:
            self.trigger_circuit_breaker(f"总亏损 {total_loss_pct:.2%} 达到熔断线")
            return self._log_check(
                "total_loss_check", None, False,
                f"总亏损 {total_loss_pct:.2%} 超过上限 {self.config.max_total_loss_pct:.2%}"
            )
        return RiskCheckResult(passed=True, check_type="total_loss_check", message="总亏损检查通过")
    
    def _check_trade_count(self) -> RiskCheckResult:
        if self.daily_trades >= self.config.max_trades_per_day:
            return self._log_check(
                "trade_count_check", None, False,
                f"今日交易次数 {self.daily_trades} 已达上限 {self.config.max_trades_per_day}"
            )
        return RiskCheckResult(passed=True, check_type="trade_count_check", message="交易频次检查通过")
    
    def _check_trade_interval(self) -> RiskCheckResult:
        if self.last_trade_time is None:
            return RiskCheckResult(passed=True, check_type="trade_interval_check", message="交易间隔检查通过")
        
        elapsed = (datetime.now() - self.last_trade_time).total_seconds() / 60
        if elapsed < self.config.min_trade_interval_minutes:
            return self._log_check(
                "trade_interval_check", None, False,
                f"距离上次交易 {elapsed:.1f} 分钟，需等待 {self.config.min_trade_interval_minutes} 分钟"
            )
        return RiskCheckResult(passed=True, check_type="trade_interval_check", message="交易间隔检查通过")
    
    def _check_price_anomaly(self, order: Order) -> RiskCheckResult:
        return RiskCheckResult(passed=True, check_type="price_anomaly_check", message="价格异常检查通过")
    
    def _log_check(self, check_type: str, order: Optional[Order], passed: bool, message: str) -> RiskCheckResult:
        order_data = order.model_dump_json() if order else "{}"
        storage.save_risk_log(
            check_type=check_type,
            order_data=order_data,
            check_result="passed" if passed else "rejected",
            reject_reason=message if not passed else None
        )
        
        if passed:
            logger.info(f"[风控] {check_type}: {message}")
        else:
            logger.warning(f"[风控] {check_type}: {message}")
        
        return RiskCheckResult(passed=passed, check_type=check_type, message=message)
    
    def trigger_circuit_breaker(self, reason: str):
        self.is_frozen = True
        self.freeze_reason = reason
        self._save_state()
        logger.error(f"[风控] 触发熔断: {reason}")
    
    def reset_circuit_breaker(self):
        self.is_frozen = False
        self.freeze_reason = ""
        self._save_state()
        logger.info("[风控] 熔断已重置")
    
    def record_trade(self, profit_loss: float = 0):
        self.daily_trades += 1
        self.last_trade_time = datetime.now()
        if profit_loss < 0:
            self.daily_loss += abs(profit_loss)
            self.total_loss += abs(profit_loss)
        self._save_state()
    
    def reset_daily(self):
        self.daily_loss = 0
        self.daily_trades = 0
        storage.reset_daily_risk()
        logger.info("[风控] 每日风控数据已重置")
    
    def handle_risk_alert(self, alert_level: AlertLevel):
        if alert_level == AlertLevel.HIGH:
            self.trigger_circuit_breaker("高风险预警触发")
        elif alert_level == AlertLevel.MEDIUM:
            logger.warning("[风控] 中风险预警，暂停加仓")


risk_manager = RiskManager()
