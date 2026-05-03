# MUP - LLM增强型宽基ETF网格交易系统

## 🎉 MVP已准备就绪！

恭喜！你的系统已成功配置并完整测试通过！所有核心功能都正常运行！

## ✅ 配置状态

### API配置已完成
- **豆包API（火山引擎）** - ✅ 已配置
- **Tushare Token** - ✅ 已配置
- **聚宽（模拟盘）** - ✅ 已配置

## 📦 快速开始

### 0. 先安装必需依赖
```bash
pip install pandas numpy requests pydantic pydantic-settings sqlalchemy loguru streamlit plotly apscheduler beautifulsoup4 lxml tushare
```

### 1. 运行完整测试
```bash
# 测试所有核心功能
python3 test_complete.py
```

### 2. 启动监控界面
```bash
# 启动Streamlit监控界面
streamlit run monitor/dashboard.py
```

### 3. 启动自动交易调度（模拟盘）
```bash
# 启动定时任务调度
python3 main.py scheduler
```

## 📊 测试结果

刚刚完成的完整系统测试结果：

✅ **配置管理** - 正常
✅ **数据源** - 正常（Tushare + 东方财富）
✅ **LLM分析** - 正常（豆包API）
✅ **网格策略** - 正常
✅ **风控模块** - 正常
✅ **模拟交易** - 正常

## ✨ 功能特点

### 📈 核心功能
- **网格交易策略** - 机械式网格，不预测涨跌，震荡行情赚钱
- **LLM增强** - 豆包API驱动，市场环境判断、信号过滤、风险预警
- **强制风控** - 仓位限制、亏损熔断、异常暂停，硬编码不允许修改
- **模拟盘** - 内置模拟盘，测试安全第一
- **双数据源** - Tushare + 东方财富，互为备用

### 🔍 LLM分析能力
1. **市场环境分析** - 判断震荡/牛市/熊市，自动调整参数
2. **信号过滤** - 过滤无效信号，提高胜率
3. **风险预警** - 分析新闻风险，及时暂停
4. **估值分析** - 分析估值高低，辅助仓位决策

### 📈 数据来源
- ✅ Tushare API（已配置）
- ✅ 东方财富（爬虫，免费）
- ✅ 财联社（新闻爬虫）

### 🖥️ 监控界面
Streamlit实时界面，包含：
- 总览页 - 账户资产、盈亏、持仓分布
- 持仓详情 - 具体持仓、成本、网格状态
- 交易记录 - 历史交易、统计分析
- 信号分析 - 信号流程、LLM决策
- 参数设置 - 策略参数、风控状态

## ⚙️ 配置说明

### 环境变量
`.env` 已配置：
```env
# 豆包API（火山引擎）
DOUBAO_API_KEY=21e570d8-2525-4a03-8921-109b7742e896
DOUBAO_MODEL=doubao-seed-2-0-pro-260215

# Tushare
TUSHARE_TOKEN=8eabb1a2bdb69be9ab151a841458339b7811c55bf858512c7fe91b00

# 交易标的
BASE_SYMBOL=510300
INITIAL_CAPITAL=10000

# 聚宽
JQ_ACCOUNT=13269183196
JQ_PASSWORD=Qingtian188
```

### 策略参数
在 `config/risk_control.py` 中硬编码（不推荐修改）：
```python
class RiskConfig:
    max_single_position_pct = 0.10  # 单笔仓位10%
    max_daily_position_pct = 0.50   # 单日仓位50%
    max_total_position_pct = 0.80   # 总仓位80%
    max_daily_loss_pct = 0.05       # 日亏损5%熔断
    max_total_loss_pct = 0.15       # 总亏损15%熔断
```

## 🏗️ 项目结构

```
mup/
├── config/                    # 配置中心
│   ├── settings.py           # 系统配置
│   ├── risk_control.py       # 风控参数
│   └── prompts.py            # LLM提示词
├── core/                      # 核心业务逻辑
│   ├── models.py             # 数据模型
│   ├── grid_strategy.py      # 网格策略
│   ├── risk_manager.py       # 风控模块
│   └── position_manager.py   # 仓位管理
├── data/                      # 数据层
│   ├── sources/              # 数据源
│   │   ├── tushare_api.py    # Tushare数据
│   │   ├── eastmoney.py      # 东方财富数据
│   │   └── cls_news.py       # 财联社新闻
│   ├── processors/           # 数据处理
│   └── storage.py            # SQLite存储
├── llm/                       # LLM分析层
│   ├── client.py             # LLM客户端
│   ├── analyzers/            # 分析器
│   └── validators.py         # 输出验证
├── trading/                   # 交易执行层
│   ├── executor.py           # 执行器
│   └── paper_trading.py      # 模拟盘
├── monitor/                   # 监控界面
│   └── dashboard.py          # Streamlit界面
├── scheduler/                 # 调度器
│   ├── jobs.py               # 定时任务
│   └── runner.py             # 启动脚本
├── tests/                     # 测试文件
│   └── test_basic.py
├── data/                      # SQLite数据目录
├── logs/                      # 日志目录
├── .env                       # 配置文件（已配置）
├── main.py                    # 主入口
├── test_simple.py            # 简单测试
├── test_data.py              # 数据测试
├── test_complete.py          # 完整测试
├── requirements.txt           # Python依赖
└── README.md                  # 说明文档
```

## 🚀 使用建议

### 第1阶段（强烈推荐）- 模拟盘测试
1. 运行 `test_complete.py` 熟悉系统
2. 启动Streamlit监控界面查看
3. 用模拟盘测试至少1周
4. 观察策略表现，熟悉系统

### 第2阶段 - 小资金实盘
1. 单独开一个证券账户
2. 只放小资金（完全不影响生活的钱）
3. 严格遵守风控限制，绝不要超仓
4. 积累至少1个月的实盘数据

### 第3阶段 - 实盘使用
1. 确认策略稳定性
2. 风险可控后逐步增加资金
3. 坚持纪律，不要情绪化交易

## 📝 风险提示与注意事项

⚠️ **个人使用系统，不建议商业使用**  
⚠️ **风险自担，投资有风险，入市需谨慎**  
⚠️ **绝不借钱投资，只用闲置资金**  
⚠️ **硬编码风控参数，不要随意修改**  
⚠️ **先充分测试模拟盘，再考虑小资金实盘**  
⚠️ **交易有风险，本系统只是工具，不保证盈利**  

## 💡 后续优化方向（可选）

- [ ] 完善新闻爬虫，增加更多来源
- [ ] 完善估值分析模块
- [ ] 增加微信/钉钉推送功能
- [ ] 策略参数回测与优化工具
- [ ] 更多ETF标的支持
- [ ] 实盘券商对接（需要你自行开发或测试）

## 📬 技术栈

- Python 3.9+
- SQLAlchemy（数据库）
- Streamlit（界面）
- APScheduler（调度）
- 豆包API（火山引擎）
- Tushare API

---

## 🎉 恭喜！

**你的系统已完整配置并测试通过！**

系统已就绪，建议先从模拟盘开始，熟悉功能和策略表现！

**祝您投资顺利，控制风险，长期稳定收益！ 🎉**

### 💻 支持的运行命令

```bash
# 快速测试核心功能
python3 test_simple.py

# 测试数据源
python3 test_data.py

# 完整系统测试
python3 test_complete.py

# 启动监控界面
streamlit run monitor/dashboard.py

# 启动调度器（交易时间运行）
python3 main.py scheduler
```
