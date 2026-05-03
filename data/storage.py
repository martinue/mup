from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import settings

Base = declarative_base()


class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    current_price = Column(Float)
    market_value = Column(Float)
    profit_loss = Column(Float)
    profit_loss_pct = Column(Float)
    grid_level = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class GridRecord(Base):
    __tablename__ = "grid_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    grid_level = Column(Integer, nullable=False)
    buy_price = Column(Float)
    buy_amount = Column(Float)
    buy_quantity = Column(Float)
    sell_price = Column(Float)
    sell_amount = Column(Float)
    profit = Column(Float)
    status = Column(String(20), default="holding")
    buy_time = Column(DateTime)
    sell_time = Column(DateTime)


class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    commission = Column(Float, default=0)
    signal_source = Column(String(50))
    llm_analysis = Column(Text)
    risk_check = Column(Text)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.now)
    filled_at = Column(DateTime)


class LLMAnalysis(Base):
    __tablename__ = "llm_analysis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_type = Column(String(50), nullable=False)
    input_data = Column(Text)
    output_data = Column(Text)
    model = Column(String(50))
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)


class RiskLog(Base):
    __tablename__ = "risk_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_type = Column(String(50), nullable=False)
    order_data = Column(Text)
    check_result = Column(String(20))
    reject_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class DailyStats(Base):
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(20), unique=True, nullable=False)
    total_asset = Column(Float)
    total_position = Column(Float)
    available_cash = Column(Float)
    daily_profit = Column(Float)
    daily_profit_pct = Column(Float)
    trade_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class NewsCache(Base):
    __tablename__ = "news_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    publish_time = Column(DateTime)
    sentiment = Column(String(20))
    risk_level = Column(String(20))
    llm_analysis = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class RiskState(Base):
    __tablename__ = "risk_state"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    is_frozen = Column(Boolean, default=False)
    freeze_reason = Column(Text)
    daily_loss = Column(Float, default=0)
    total_loss = Column(Float, default=0)
    daily_trades = Column(Integer, default=0)
    last_trade_time = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
