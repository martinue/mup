from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from data.storage import (
    SessionLocal, Position, GridRecord, Trade, LLMAnalysis,
    RiskLog, DailyStats, NewsCache, SystemConfig, RiskState, init_db
)


class DataStorage:
    def __init__(self):
        init_db()
    
    def get_session(self) -> Session:
        return SessionLocal()
    
    def save_position(self, symbol: str, quantity: float, cost_price: float, 
                      grid_level: int = 0) -> Position:
        with self.get_session() as session:
            position = Position(
                symbol=symbol,
                quantity=quantity,
                cost_price=cost_price,
                grid_level=grid_level
            )
            session.add(position)
            session.commit()
            session.refresh(position)
            return position
    
    def get_position(self, symbol: str) -> Optional[Position]:
        with self.get_session() as session:
            return session.query(Position).filter(
                Position.symbol == symbol
            ).order_by(Position.created_at.desc()).first()
    
    def get_all_positions(self) -> List[Position]:
        with self.get_session() as session:
            return session.query(Position).all()
    
    def update_position_price(self, symbol: str, current_price: float):
        with self.get_session() as session:
            position = session.query(Position).filter(
                Position.symbol == symbol
            ).order_by(Position.created_at.desc()).first()
            if position:
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.profit_loss = position.market_value - (position.quantity * position.cost_price)
                position.profit_loss_pct = position.profit_loss / (position.quantity * position.cost_price)
                position.updated_at = datetime.now()
                session.commit()
    
    def save_grid_record(self, symbol: str, grid_level: int, buy_price: float,
                         buy_amount: float, buy_quantity: float) -> GridRecord:
        with self.get_session() as session:
            record = GridRecord(
                symbol=symbol,
                grid_level=grid_level,
                buy_price=buy_price,
                buy_amount=buy_amount,
                buy_quantity=buy_quantity,
                buy_time=datetime.now(),
                status="holding"
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
    
    def get_active_grids(self, symbol: str) -> List[GridRecord]:
        with self.get_session() as session:
            return session.query(GridRecord).filter(
                GridRecord.symbol == symbol,
                GridRecord.status == "holding"
            ).all()
    
    def close_grid(self, grid_id: int, sell_price: float, sell_amount: float, profit: float):
        with self.get_session() as session:
            grid = session.query(GridRecord).filter(GridRecord.id == grid_id).first()
            if grid:
                grid.sell_price = sell_price
                grid.sell_amount = sell_amount
                grid.profit = profit
                grid.status = "sold"
                grid.sell_time = datetime.now()
                session.commit()
    
    def save_trade(self, symbol: str, side: str, price: float, quantity: float,
                   amount: float, signal_source: str = None, llm_analysis: str = None,
                   risk_check: str = None) -> Trade:
        with self.get_session() as session:
            trade = Trade(
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                amount=amount,
                signal_source=signal_source,
                llm_analysis=llm_analysis,
                risk_check=risk_check,
                status="pending"
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade
    
    def get_trades(self, symbol: str = None, limit: int = 100) -> List[Trade]:
        with self.get_session() as session:
            query = session.query(Trade)
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            return query.order_by(Trade.created_at.desc()).limit(limit).all()
    
    def update_trade_status(self, trade_id: int, status: str):
        with self.get_session() as session:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                trade.status = status
                if status == "filled":
                    trade.filled_at = datetime.now()
                session.commit()
    
    def save_llm_analysis(self, analysis_type: str, input_data: str, output_data: str,
                          model: str, tokens_used: int = 0, cost: float = 0) -> LLMAnalysis:
        with self.get_session() as session:
            analysis = LLMAnalysis(
                analysis_type=analysis_type,
                input_data=input_data,
                output_data=output_data,
                model=model,
                tokens_used=tokens_used,
                cost=cost
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis
    
    def save_risk_log(self, check_type: str, order_data: str, check_result: str,
                      reject_reason: str = None) -> RiskLog:
        with self.get_session() as session:
            log = RiskLog(
                check_type=check_type,
                order_data=order_data,
                check_result=check_result,
                reject_reason=reject_reason
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
    
    def save_daily_stats(self, date_str: str, total_asset: float, total_position: float,
                         available_cash: float, daily_profit: float, daily_profit_pct: float,
                         trade_count: int) -> DailyStats:
        with self.get_session() as session:
            stats = session.query(DailyStats).filter(DailyStats.date == date_str).first()
            if stats:
                stats.total_asset = total_asset
                stats.total_position = total_position
                stats.available_cash = available_cash
                stats.daily_profit = daily_profit
                stats.daily_profit_pct = daily_profit_pct
                stats.trade_count = trade_count
            else:
                stats = DailyStats(
                    date=date_str,
                    total_asset=total_asset,
                    total_position=total_position,
                    available_cash=available_cash,
                    daily_profit=daily_profit,
                    daily_profit_pct=daily_profit_pct,
                    trade_count=trade_count
                )
                session.add(stats)
            session.commit()
            session.refresh(stats)
            return stats
    
    def get_daily_stats(self, date_str: str) -> Optional[DailyStats]:
        with self.get_session() as session:
            return session.query(DailyStats).filter(DailyStats.date == date_str).first()
    
    def save_news(self, source: str, title: str, content: str, publish_time: datetime = None) -> NewsCache:
        with self.get_session() as session:
            existing = session.query(NewsCache).filter(
                NewsCache.title == title,
                NewsCache.source == source
            ).first()
            if existing:
                return existing
            news = NewsCache(
                source=source,
                title=title,
                content=content,
                publish_time=publish_time or datetime.now()
            )
            session.add(news)
            session.commit()
            session.refresh(news)
            return news
    
    def get_recent_news(self, limit: int = 50) -> List[NewsCache]:
        with self.get_session() as session:
            return session.query(NewsCache).order_by(
                NewsCache.publish_time.desc()
            ).limit(limit).all()
    
    def update_news_analysis(self, news_id: int, sentiment: str, risk_level: str, llm_analysis: str):
        with self.get_session() as session:
            news = session.query(NewsCache).filter(NewsCache.id == news_id).first()
            if news:
                news.sentiment = sentiment
                news.risk_level = risk_level
                news.llm_analysis = llm_analysis
                session.commit()
    
    def get_risk_state(self) -> RiskState:
        with self.get_session() as session:
            state = session.query(RiskState).first()
            if not state:
                state = RiskState()
                session.add(state)
                session.commit()
                session.refresh(state)
            return state
    
    def update_risk_state(self, is_frozen: bool = None, freeze_reason: str = None,
                          daily_loss: float = None, total_loss: float = None,
                          daily_trades: int = None, last_trade_time: datetime = None):
        with self.get_session() as session:
            state = session.query(RiskState).first()
            if not state:
                state = RiskState()
                session.add(state)
            if is_frozen is not None:
                state.is_frozen = is_frozen
            if freeze_reason is not None:
                state.freeze_reason = freeze_reason
            if daily_loss is not None:
                state.daily_loss = daily_loss
            if total_loss is not None:
                state.total_loss = total_loss
            if daily_trades is not None:
                state.daily_trades = daily_trades
            if last_trade_time is not None:
                state.last_trade_time = last_trade_time
            state.updated_at = datetime.now()
            session.commit()
    
    def reset_daily_risk(self):
        with self.get_session() as session:
            state = session.query(RiskState).first()
            if state:
                state.daily_loss = 0
                state.daily_trades = 0
                state.updated_at = datetime.now()
                session.commit()


storage = DataStorage()
