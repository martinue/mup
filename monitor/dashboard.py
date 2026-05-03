import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

from config.settings import settings
from data import storage
from data.processors import data_processor
from core.grid_strategy import create_grid_strategy
from trading.executor import create_executor


st.set_page_config(
    page_title="MUP - ETF网格交易系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_executor():
    if "executor" not in st.session_state:
        st.session_state.executor = create_executor(
            symbol=settings.BASE_SYMBOL,
            use_paper=True
        )
    return st.session_state.executor


def show_overview():
    st.header("📊 总览")
    
    executor = get_executor()
    status = executor.get_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_value = status["account"].get("total_value", 0)
        st.metric(
            label="总资产",
            value=f"¥{total_value:,.2f}"
        )
    
    with col2:
        positions = status["account"].get("positions", [])
        total_position = sum(p.get("market_value", 0) for p in positions)
        st.metric(
            label="持仓市值",
            value=f"¥{total_position:,.2f}"
        )
    
    with col3:
        available = status["account"].get("available_cash", 0)
        st.metric(
            label="可用资金",
            value=f"¥{available:,.2f}"
        )
    
    with col4:
        daily_trades = status["risk"].get("daily_trades", 0)
        st.metric(
            label="今日交易次数",
            value=f"{daily_trades}/{settings.INITIAL_CAPITAL}"
        )
    
    st.divider()
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("持仓分布")
        
        if positions:
            df = pd.DataFrame(positions)
            fig = px.pie(df, values='market_value', names='symbol', 
                        title='持仓分布')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无持仓")
    
    with col_right:
        st.subheader("系统状态")
        
        is_frozen = status["risk"].get("is_frozen", False)
        if is_frozen:
            st.error(f"⚠️ 系统已冻结\n原因: {status['risk'].get('freeze_reason', '')}")
        else:
            st.success("✅ 系统正常运行")
        
        st.write(f"**市场环境:** {status.get('market_env', '未知')}")
        st.write(f"**活跃网格:** {status['grid'].get('active_grids', 0)}")
        
        last_time = status.get("last_execute_time")
        if last_time:
            st.write(f"**上次执行:** {last_time}")
    
    st.divider()
    
    st.subheader("近期交易")
    trades = storage.get_trades(limit=10)
    if trades:
        df = pd.DataFrame([{
            "时间": t.created_at.strftime("%Y-%m-%d %H:%M"),
            "标的": t.symbol,
            "方向": "买入" if t.side == "buy" else "卖出",
            "价格": f"¥{t.price:.3f}",
            "数量": f"{t.quantity:.0f}",
            "金额": f"¥{t.amount:.2f}",
            "状态": t.status
        } for t in trades])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无交易记录")


def show_positions():
    st.header("💼 持仓详情")
    
    executor = get_executor()
    status = executor.get_status()
    
    positions = status["account"].get("positions", [])
    
    if positions:
        df_data = []
        for pos in positions:
            profit = pos.get("market_value", 0) - pos.get("quantity", 0) * pos.get("cost_price", 0)
            profit_pct = profit / (pos.get("quantity", 0) * pos.get("cost_price", 1)) * 100
            
            df_data.append({
                "标的": pos.get("symbol"),
                "数量": f"{pos.get('quantity', 0):.0f}",
                "成本价": f"¥{pos.get('cost_price', 0):.3f}",
                "现价": f"¥{pos.get('current_price', 0):.3f}",
                "市值": f"¥{pos.get('market_value', 0):.2f}",
                "盈亏": f"¥{profit:.2f}",
                "盈亏%": f"{profit_pct:.2f}%"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无持仓")
    
    st.divider()
    
    st.subheader("网格状态")
    grid_status = status["grid"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("基准价", f"¥{grid_status.get('base_price', 0):.3f}")
    with col2:
        st.metric("网格间距", f"{grid_status.get('grid_spacing', 0)*100:.1f}%")
    with col3:
        st.metric("每格金额", f"¥{grid_status.get('grid_amount', 0):.0f}")
    
    grids = grid_status.get("grids", [])
    if grids:
        st.subheader("活跃网格")
        grid_df = pd.DataFrame([{
            "层级": g["level"],
            "买入价": f"¥{g['buy_price']:.3f}",
            "买入数量": f"{g['buy_quantity']:.0f}",
            "买入金额": f"¥{g['buy_amount']:.2f}"
        } for g in grids])
        st.dataframe(grid_df, use_container_width=True, hide_index=True)


def show_trades():
    st.header("📜 交易记录")
    
    date_range = st.date_input(
        "选择日期范围",
        value=(datetime.now() - timedelta(days=7), datetime.now()),
        max_value=datetime.now()
    )
    
    trades = storage.get_trades(limit=100)
    
    if trades:
        df_data = [{
            "时间": t.created_at,
            "标的": t.symbol,
            "方向": "买入" if t.side == "buy" else "卖出",
            "价格": t.price,
            "数量": t.quantity,
            "金额": t.amount,
            "状态": t.status
        } for t in trades]
        
        df = pd.DataFrame(df_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_buy = df[df["方向"] == "买入"]["金额"].sum()
            st.metric("总买入", f"¥{total_buy:,.2f}")
        with col2:
            total_sell = df[df["方向"] == "卖出"]["金额"].sum()
            st.metric("总卖出", f"¥{total_sell:,.2f}")
        with col3:
            st.metric("交易次数", len(df))
        
        st.divider()
        
        df["时间"] = df["时间"].dt.strftime("%Y-%m-%d %H:%M")
        df["价格"] = df["价格"].apply(lambda x: f"¥{x:.3f}")
        df["金额"] = df["金额"].apply(lambda x: f"¥{x:.2f}")
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无交易记录")


def show_signals():
    st.header("📡 信号分析")
    
    executor = get_executor()
    
    if st.button("刷新数据", type="primary"):
        with st.spinner("正在获取数据..."):
            result = executor.execute_cycle()
            st.session_state.last_result = result
            st.success("数据刷新完成")
    
    if "last_result" in st.session_state:
        result = st.session_state.last_result
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("市场环境分析")
            env = result.get("market_env")
            if env:
                st.write(f"**环境类型:** {env.get('env_type', '未知')}")
                st.write(f"**置信度:** {env.get('confidence', 0)*100:.1f}%")
                st.write(f"**理由:** {env.get('reason', '')}")
        
        with col2:
            st.subheader("风险预警")
            alert = result.get("risk_alert")
            if alert:
                level = alert.get("risk_level", "low")
                if level == "high":
                    st.error(f"⚠️ 高风险")
                elif level == "medium":
                    st.warning(f"⚡ 中风险")
                else:
                    st.success(f"✅ 低风险")
                st.write(f"**理由:** {alert.get('reason', '')}")
        
        st.divider()
        
        st.subheader("信号处理流程")
        
        signals = result.get("signals", [])
        filtered = result.get("filtered_signals", [])
        approved = result.get("approved_signals", [])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("原始信号", len(signals))
        with col2:
            st.metric("LLM过滤后", len(filtered))
        with col3:
            st.metric("风控通过", len(approved))
        
        if signals:
            st.subheader("信号详情")
            signal_df = pd.DataFrame(signals)
            st.dataframe(signal_df, use_container_width=True)
    else:
        st.info("点击刷新按钮获取最新数据")


def show_settings():
    st.header("⚙️ 参数设置")
    
    st.warning("⚠️ 修改参数需要谨慎，部分参数修改后需要重启系统生效")
    
    st.subheader("策略参数")
    
    col1, col2 = st.columns(2)
    
    with col1:
        grid_spacing = st.number_input(
            "网格间距 (%)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5
        )
        
        grid_amount = st.number_input(
            "每格金额 (元)",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100
        )
    
    with col2:
        take_profit = st.number_input(
            "止盈比例 (%)",
            min_value=1.0,
            max_value=20.0,
            value=8.0,
            step=0.5
        )
        
        stop_loss = st.number_input(
            "止损比例 (%)",
            min_value=1.0,
            max_value=20.0,
            value=10.0,
            step=0.5
        )
    
    st.divider()
    
    st.subheader("风控参数 (只读)")
    
    from config.risk_control import risk_config
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**单笔仓位上限:** {risk_config.max_single_position_pct*100:.0f}%")
        st.write(f"**单日仓位上限:** {risk_config.max_daily_position_pct*100:.0f}%")
        st.write(f"**总仓位上限:** {risk_config.max_total_position_pct*100:.0f}%")
    
    with col2:
        st.write(f"**单日亏损上限:** {risk_config.max_daily_loss_pct*100:.0f}%")
        st.write(f"**总亏损上限:** {risk_config.max_total_loss_pct*100:.0f}%")
        st.write(f"**每日交易上限:** {risk_config.max_trades_per_day}次")
    
    st.divider()
    
    st.subheader("系统操作")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("重置每日风控", type="secondary"):
            from core.risk_manager import risk_manager
            risk_manager.reset_daily()
            st.success("每日风控已重置")
    
    with col2:
        if st.button("重置熔断状态", type="secondary"):
            from core.risk_manager import risk_manager
            risk_manager.reset_circuit_breaker()
            st.success("熔断状态已重置")


def main():
    st.sidebar.title("📈 MUP")
    st.sidebar.caption("ETF网格交易系统")
    
    page = st.sidebar.radio(
        "导航",
        ["📊 总览", "💼 持仓详情", "📜 交易记录", "📡 信号分析", "⚙️ 参数设置"]
    )
    
    st.sidebar.divider()
    
    st.sidebar.caption(f"版本: 1.0.0")
    st.sidebar.caption(f"标的: {settings.BASE_SYMBOL}")
    
    if "📊" in page:
        show_overview()
    elif "💼" in page:
        show_positions()
    elif "📜" in page:
        show_trades()
    elif "📡" in page:
        show_signals()
    elif "⚙️" in page:
        show_settings()


if __name__ == "__main__":
    main()
