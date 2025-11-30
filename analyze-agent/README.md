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
- 数据与生成：`generate_listings` 支持分层覆盖（每城/区/户型至少若干条）+ 随机补充；`preprocess` 清洗到 Parquet。
- 检索：查询解析支持城市/城区识别、精确“X室Y厅”过滤；硬过滤按等值/区间筛选；BM25/语义（TF-IDF+jieba，向量用 bge-small-zh + FAISS）召回。
- 排序：质量分 + BM25/语义/投送量融合；支持 TopN 排序。
- 编排/UI：Orchestrator 串联解析→召回→排序，Gradio UI；Streamlit 后台可视化。
- 配置/占位：config、utils、prompts、tests 等骨架。

## 使用指南（复用 conda 环境 llm_env）
```bash
cd analyze-agent
conda activate llm_env
pip install -r requirements.txt          # 会安装 torch/torchvision/transformers/sentence-transformers 指定版本
python -m src.pipeline.generate_listings   # 生成示例 Excel（分层+随机）
python -m src.pipeline.preprocess          # 清洗为 Parquet
python -m src.pipeline.build_bm25          # 构建 BM25(TF-IDF+jieba) 索引
python -m src.pipeline.build_vectors       # 构建语义索引（bge-small-zh + FAISS）
python -m src.app.gradio_app               # 运行检索 UI
# 或：streamlit run dashboards/admin.py    # 后台数据浏览
```
> 如提示“数据未准备”，说明 Parquet/索引未生成，按上述顺序跑完管线。
> 如加载 bge-small-zh 失败，请确认 torch/torchvision/transformers/sentence-transformers 已按 requirements 安装，并重新安装依赖后再跑 build_vectors。

## 下一步计划
1) 索引与检索：加入中文停用词表，优化权重调优；可选本地 jieba 自定义词典。
2) 排序调优：调整权重，支持投送干预配置；增加一致性过滤（城市/城区、户型）优先于排序。
3) LLM 集成：在 `AnswerGenerator` 中接入真实 LLM，生成解释/理由。
4) 评价与测试：构造示例查询集，补单测，记录召回/排序指标。
5) 部署体验：优化 Gradio/Streamlit 交互，考虑 FastAPI 接口。
