# Analyze Agent

面向房产检索/分析的智能助手。目标：硬条件过滤 + 词法 BM25 + 语义检索融合，并用 LLM 生成回答，形成混合搜索与分析流程。

## 项目目的
- 构建可检索的房产数据基座：Excel→清洗→Parquet/索引（BM25、向量）。
- 三条技术路线并行：
  1) 结构化硬过滤（城市/价格/面积/户型等）。
  2) 词法相关性（BM25/TF-IDF）。
  3) 语义匹配（向量检索或 LLM 解析）。
- 混合排序：硬过滤后融合 BM25 分、语义分、质量分，并支持投送量加权。
- LLM 回答：将 TopN 结果与用户问题交给 LLM，总结推荐并解释理由（RAG 风格）。

## 当前进展
- 完整骨架与占位实现：
  - `src/schema/listing_schema.py` 完整 Listing 字段（含公司、投送量）。
  - `src/pipeline/`：生成样例数据、预处理、BM25 索引、向量索引。
  - `src/retrieval/`：硬过滤、BM25/Tf-idf 召回、语义（Tf-idf 向量）召回、查询解析。
  - `src/ranking/`：质量分与多路得分融合、排序器。
  - `src/agent/`：编排器与回答生成模板（可接入真实 LLM）。
  - `src/app/gradio_app.py`：简单检索 UI。
  - `dashboards/admin.py`：Streamlit 后台数据浏览/筛选/分布。
  - `config.py`、`utils/`、`prompts/`、`tests/` 占位。

## 使用指南（本地）
```bash
cd analyze-agent
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m src.pipeline.generate_listings   # 生成示例 Excel
python -m src.pipeline.preprocess          # 清洗为 Parquet
python -m src.pipeline.build_bm25          # 构建 BM25(TF-IDF) 索引
python -m src.pipeline.build_vectors       # 构建语义(TF-IDF) 索引
python -m src.app.gradio_app               # 运行检索 UI
# 或：streamlit run dashboards/admin.py    # 后台数据浏览
```

## 下一步计划
1) 完善索引与检索：BM25/向量索引持久化优化，加入分词/中文停用词表。
2) 语义能力：可替换 TF-IDF 为本地 embedding（如 bge-mini）或在线向量服务。
3) LLM 集成：在 `AnswerGenerator` 中接入真实 LLM，并增加引用/解释。
4) 排序调优：调整质量分与 BM25/语义权重，支持投送量干预、A/B 配置。
5) 测试与监控：补充单测与示例查询集，增加日志/指标。
