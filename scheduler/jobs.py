from datetime import datetime
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from trading.executor import create_executor
from data.processors import data_processor
from core.risk_manager import risk_manager


class JobScheduler:
    def __init__(self, symbol: str = None, use_paper: bool = True):
        self.symbol = symbol or settings.BASE_SYMBOL
        self.use_paper = use_paper
        self.scheduler = BackgroundScheduler()
        self.executor = None
        logger.info(f"[调度器] 初始化完成, 标的: {self.symbol}")
    
    def setup_jobs(self):
        self.scheduler.add_job(
            self.trading_cycle,
            CronTrigger(hour='9-11,13-15', minute=5),
            id='trading_cycle',
            name='交易检查',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.daily_update,
            CronTrigger(hour=15, minute=30),
            id='daily_update',
            name='每日数据更新',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.weekly_rebalance,
            CronTrigger(day_of_week='sun', hour=20),
            id='weekly_rebalance',
            name='每周再平衡',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.risk_monitor,
            CronTrigger(minute='*/30'),
            id='risk_monitor',
            name='风险监控',
            replace_existing=True
        )
        
        logger.info("[调度器] 任务设置完成")
    
    def start(self):
        if self.executor is None:
            self.executor = create_executor(self.symbol, self.use_paper)
        
        self.setup_jobs()
        self.scheduler.start()
        logger.info("[调度器] 已启动")
    
    def stop(self):
        self.scheduler.shutdown()
        logger.info("[调度器] 已停止")
    
    def trading_cycle(self):
        logger.info("[调度器] 执行交易检查")
        try:
            now = datetime.now()
            if now.weekday() >= 5:
                logger.info("[调度器] 周末不交易")
                return
            
            hour = now.hour
            if hour < 9 or (hour == 11 and now.minute > 30) or (hour == 12) or hour >= 15:
                logger.info("[调度器] 非交易时间")
                return
            
            result = self.executor.execute_cycle()
            logger.info(f"[调度器] 交易检查完成: {len(result.get('trades', []))} 笔交易")
            
        except Exception as e:
            logger.error(f"[调度器] 交易检查异常: {e}")
    
    def daily_update(self):
        logger.info("[调度器] 执行每日更新")
        try:
            risk_manager.reset_daily()
            
            quote = data_processor.get_quote(self.symbol)
            if quote:
                current_prices = {self.symbol: quote.price}
                from core.position_manager import position_manager
                position_manager.update_prices(current_prices)
                position_manager.save_daily_stats(current_prices)
            
            logger.info("[调度器] 每日更新完成")
            
        except Exception as e:
            logger.error(f"[调度器] 每日更新异常: {e}")
    
    def weekly_rebalance(self):
        logger.info("[调度器] 执行每周再平衡")
        try:
            klines = data_processor.get_klines(self.symbol, 30)
            if klines:
                from core.grid_strategy import GridStrategy
                prices = [k.close for k in klines[-20:]]
                new_base = sum(prices) / len(prices)
                
                if self.executor and self.executor.strategy:
                    self.executor.strategy.update_base_price(new_base)
                    logger.info(f"[调度器] 基准价更新为: {new_base:.3f}")
            
            logger.info("[调度器] 每周再平衡完成")
            
        except Exception as e:
            logger.error(f"[调度器] 每周再平衡异常: {e}")
    
    def risk_monitor(self):
        logger.debug("[调度器] 执行风险监控")
        try:
            from llm.analyzers import risk_alert_analyzer
            from data.processors import data_processor
            
            news_list = data_processor.get_news(20)
            alert_result = risk_alert_analyzer.analyze(news_list)
            
            if alert_result.risk_level.value == "high":
                risk_manager.handle_risk_alert(alert_result.risk_level)
                logger.warning(f"[调度器] 高风险预警: {alert_result.reason}")
            
        except Exception as e:
            logger.error(f"[调度器] 风险监控异常: {e}")
    
    def run_once(self):
        logger.info("[调度器] 手动执行一次")
        return self.trading_cycle()


scheduler = JobScheduler()
