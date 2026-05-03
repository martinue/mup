from loguru import logger
import sys
from pathlib import Path

from config.settings import settings
from scheduler.jobs import JobScheduler


def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.remove()
    
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    logger.add(
        "logs/mup_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="00:00",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("日志系统初始化完成")


def run_scheduler():
    setup_logging()
    logger.info("启动MUP系统...")
    
    from data.storage import init_db
    init_db()
    logger.info("数据库初始化完成")
    
    scheduler = JobScheduler()
    scheduler.start()
    logger.info("调度器启动完成")
    
    return scheduler


def run_dashboard():
    import subprocess
    subprocess.run(["streamlit", "run", "monitor/dashboard.py"])


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="MUP - ETF网格交易系统")
    parser.add_argument(
        "command",
        choices=["scheduler", "dashboard", "all"],
        help="运行模式: scheduler(调度器), dashboard(监控界面), all(全部)"
    )
    parser.add_argument("--symbol", default="510300", help="交易标的")
    parser.add_argument("--paper", action="store_true", help="使用模拟盘")
    
    args = parser.parse_args()
    
    if args.command == "scheduler":
        scheduler = run_scheduler()
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
            logger.info("系统已停止")
    
    elif args.command == "dashboard":
        run_dashboard()
    
    elif args.command == "all":
        import multiprocessing
        
        scheduler_process = multiprocessing.Process(target=run_scheduler)
        scheduler_process.start()
        
        run_dashboard()
        
        scheduler_process.terminate()


if __name__ == "__main__":
    main()
