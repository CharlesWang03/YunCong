# Analyze Agent

面向房产检索/分析的智能助手骨架。目标：将硬条件过滤、词法 BM25、语义检索和 LLM 回答编排成混合搜索 + 答复流程，便于演示与扩展。

## 项目目的
- 构建可检索的房产数据基座：Excel→清洗→Parquet/索引（BM25、向量）。
- 三条技术路线并行：
  1) 结构化硬过滤（城市/价格/面积/户型等）。
  2) 词法相关性（BM25/TF-IDF）。
  3) 语义匹配（向量检索或 LLM 解析）。
- 混合排序：硬过滤后融合 BM25 分、语义分、质量分，支持投流加权。
- LLM 回答：将 TopN 结果与用户问题交给 LLM，总结推荐并解释理由（RAG 风格）。

## 当前进展（骨架）
- 目录结构与空模块创建完毕：
  - `data/raw`, `data/processed` 占位。
  - `src/config.py` 路径配置占位。
  - `src/schema/listing_schema.py` 定义完整 Listing 字段（含公司、投送量）。
  - `src/pipeline/` 占位：数据生成、预处理、BM25 索引、向量索引。
  - `src/retrieval/` 占位：过滤引擎、BM25 引擎、语义引擎、查询解析。
  - `src/ranking/` 占位：质量/融合打分、排序器。
  - `src/agent/` 占位：编排器、LLM 答案生成。
  - `src/app/gradio_app.py` 占位：UI 入口。
  - `src/utils/logging_utils.py` 占位：日志工具。
  - `dashboards/admin.py` 占位：Streamlit 后台可视化（加载 Parquet，筛选/概览/分布）。
  - `prompts/`, `tests/` 占位。

## 下一步计划
1) 数据：从 Excel 构造示例数据 → 清洗为 Parquet；设计文本字段供 BM25/向量索引。
2) 索引：实现 BM25 构建/加载；选择本地或在线 embedding，搭建向量检索。
3) 检索：完成硬过滤、BM25/语义召回；合并去重并产出候选。
4) 排序：实现质量分 & 投送量加权；融合 BM25/语义分，返回 TopN。
5) 编排与回答：在 orchestrator 中串联解析→召回→精排；用 LLM 生成解释性回答。
6) UI/接口：完成 Gradio/FastAPI 入口；提供基本搜索 Demo；后台 Streamlit 用于数据浏览与监测。
