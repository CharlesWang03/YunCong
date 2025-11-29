## Real Estate Assistant

面向房源数据的轻量实验项目：生成中文合成房源，预处理为 Parquet，基于条件筛选/排序，并提供 Gradio 界面与规则式 NLP 入口。

### 模块与层次功能
- 数据层（`data/`）
  - `data/raw/`: 生成的原始 Excel 房源。
  - `data/processed/`: 清洗后的 Parquet，作为查询输入。
- 文档层（`docs/`）
  - `design_overview.md`: 端到端流程、关键决策。
  - `data_schema.md`: 字段定义、预期分布范围。
- 核心代码（`src/`）
  - `config.py`: 路径、随机种子、默认生成条数等全局配置。
  - 模型（`src/models/`）：`listing.py` 定义房源结构，`search_filter.py` 定义筛选条件。
  - 数据管线（`src/data_pipeline/`）：
    - `generator.py`: 中文房源生成，包含城区/距离/中文描述，写入 Excel。
    - `preprocess.py`: 类型校正、去重、日期解析，输出 Parquet。
    - `repository.py`: 加载处理后数据，并封装 `search` 入口。
  - 检索/排序（`src/search/`）：
    - `filter_engine.py`: 价格/面积/户型/停车/位置/关键词筛选。
    - `ranking.py`: 价格升/降、新发房源等排序策略。
  - NLP（`src/nlp/`）：`rule_based_parser.py` 将短文本解析成 `SearchFilter`。
  - 应用（`src/app/`）：`gradio_app.py` 构建前端表单，串联解析、筛选、排序结果。
- 测试层（`tests/`）
  - `test_generator.py`: 生成数量与列完整性检查。
  - `test_preprocess.py`: 清洗后类型、日期有效性检查。
  - `test_filter_engine.py`: 筛选逻辑的核心断言。
- 分析层（`notebooks/`）
  - `01_data_exploration.ipynb`: 描述统计/分布探索的起点。

### 数据生成与字段结构（`src/data_pipeline/generator.py` → Excel）
- 列：`id`、`city`、`district`、`price`、`bedrooms`、`bathrooms`、`area_sqm`、`property_type`、`year_built`、`has_parking`、`distance_to_center_km`、`distance_to_school_km`、`description`、`listing_date`。
- 中文化：城市、城区、户型、描述均为中文，便于本地化展示。
- 距离：`distance_to_center_km`、`distance_to_school_km` 可用于筛选/排序或可视化。
- 描述：`description` 汇总城市、户型、面积、距离、停车位等信息，便于关键词匹配。

#### 价格模型要点
- 城市基准价：不同城市有不同的百万级基准总价。
- 市中心距离衰减：距中心越近，价格越高（指数衰减因子）。
- 学校距离加成：越靠近学校，价格略有上涨。
- 面积/户型/房间数：按面积、户型系数、卧/卫数量线性放大。
- 噪声：轻微随机扰动以增加多样性。

### 项目思路与技术选型
1) 配置集中：`config.py` 统一路径、随机种子、默认生成数，便于重定位数据目录和复现实验。
2) 数据生成：`generator.py` 用 Faker(`zh_CN`) + NumPy/Python 随机生成中文房源，加入距中心/学校字段，并在描述中汇总可读信息，输出 Excel（pandas）。
3) 数据清洗：`preprocess.py` 用 pandas 进行类型转换、去重、日期解析，写出 Parquet（pyarrow），保证读取性能。
4) 数据访问：`repository.py` 将 Parquet 读取为 DataFrame，并封装 `search`，可后续替换为数据库/向量库。
5) 检索与排序：`filter_engine.py` 在 DataFrame 上做布尔掩码筛选；`ranking.py` 提供简单排序策略（价格/最新），可扩展评分函数。
6) NLP 解析：`rule_based_parser.py` 用正则从短文本提取价格/卧室/卫生间/关键词等，转换成 `SearchFilter`，后续可换为大模型或更复杂规则。
7) 前端与编排：`gradio_app.py` 用 Gradio 组件收集输入，调用解析→筛选→排序，展示表格；首次运行自动生成/清洗数据。
8) 质量与验证：`tests/` 用 pytest 做生成/清洗/筛选的基本断言，`notebooks/` 提供探索起点。

### 运行说明（结合近期调试）
- 从仓库根目录运行，确保环境为 `llm_env`。
- 推荐命令（无警告）：
  ```bash
  cd D:\Coding\Python\LeetCode\YunCong\real-estate-assistant
  conda activate llm_env
  python -m src.data_pipeline.generator   # 生成 Excel
  python -m src.data_pipeline.preprocess  # 转 Parquet
  python -m src.app.gradio_app            # 启动 UI
  ```
- 若使用直接文件路径，也支持：`python src\data_pipeline\generator.py` 与 `python src\data_pipeline\preprocess.py`（已在脚本内注入根目录到 `sys.path`）。
- 在交互/重复运行时，`python -m ...` 可能出现 `found in sys.modules` 的 RuntimeWarning，可忽略；功能正常。

### 开发进度
- 目录结构与占位文件
- 中文合成数据生成、预处理、基础查询/排序
- 规则式 NLP 解析与 Gradio UI
- 基础单元测试与探索 notebook
- 进一步的数据质量校验与更丰富的排序策略（进行中）

### 下一步优化计划
1) 数据：异常值检测、更多城市/户型分布参数化；补充地理坐标便于地图/距离筛选。
2) 检索：支持模糊关键词、区间权重；增加多维排序（综合评分、距离地铁/学校）。
3) NLP：扩展规则到价格区间/面积区间，加入简单意图槽位回退；支持中英双语词典。
4) 应用：结果分页/导出 CSV；UI 增加图表（价格/面积分布）、表格格式化。
5) 工程：补充 CI 测试工作流，锁定依赖版本；添加配置化日志和错误可视化。
6) Notebook：内置示例分析（直方图、箱线图、相关性），便于快速 sanity check。
