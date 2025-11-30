# Analyze Agent

面向房产检索/分析的智能助手：硬条件过滤 + 词法 BM25 + 语义检索融合，并用 LLM 生成回答，形成混合搜索与分析流程。

## 项目目的
- 构建可检索的房产数据基座：Excel→清洗→Parquet/索引（BM25、向量）。
- 三条技术路线并行：
  1) 结构化硬过滤（城市/价格/面积/户型等）。
  2) 词法相关性（BM25/TF-IDF+jieba）。
  3) 语义匹配（bge-small-zh 向量检索/FAISS）。
- 混合排序：硬过滤后融合 BM25 分、语义分、质量分，并支持投送量加权。
- LLM 回答：将 TopN 结果与用户问题交给 LLM，总结推荐并解释理由（RAG 风格）。

## 当前进展
- 数据：`generate_listings` 分层覆盖（每城/区/1-4 室至少若干条）+ 随机补充；`preprocess` 清洗至 Parquet。
- 检索：解析支持城市/城区、精确“X室Y厅”；硬过滤按等值/区间；BM25（TF-IDF+jieba）与语义（bge-small-zh+FAISS）召回。
- 排序：质量分 + BM25/语义/投送量融合，TopN 输出。
- 编排/UI：Gradio 提供 Filter/搜索/助手三模式（Filter 模式禁用 BM25/语义以保证速度）；Streamlit 后台可视化。
- 依赖与配置：torch/torchvision/transformers/sentence-transformers 已固定版本；config/utils/prompts/tests 骨架就绪。

## 使用指南（复用 conda 环境 llm_env）
```bash
cd analyze-agent
conda activate llm_env
pip install -r requirements.txt          # 安装固定版本的 torch/torchvision/transformers/sentence-transformers 等
# 如已生成数据/索引，可跳过下列四步
python -m src.pipeline.generate_listings   # 生成示例 Excel（分层+随机）
python -m src.pipeline.preprocess          # 清洗为 Parquet
python -m src.pipeline.build_bm25          # 构建 BM25(TF-IDF+jieba) 索引
python -m src.pipeline.build_vectors       # 构建语义索引（bge-small-zh + FAISS）
python -m src.app.gradio_app               # 运行检索 UI（三模式）
# 或：streamlit run dashboards/admin.py    # 后台数据浏览
```
> 如提示“数据未准备”，说明 Parquet/索引未生成，按上述顺序跑完管线。
> 如加载 bge-small-zh 失败，请确认 torch/torchvision/transformers/sentence-transformers 已按 requirements 安装，并重新运行 build_vectors。

## 性能现状
- Filter 模式：仅硬过滤+排序，响应较快。
- 搜索/助手模式：包含 BM25 + 语义编码/FAISS，耗时较高；可减小 top_k、更换小模型或缓存结果。

## 下一步优化方向（推荐）
1) 检索效率：
   - 语义检索 top_k 调低、改用 bge-mini；热门查询向量/结果缓存；提供“仅 BM25”开关。
   - 索引层优化：中文停用词、自定义词典，BM25 参数调优。
2) 智能助手（模式三）：
   - 接入真实 LLM（API/本地），在 `AnswerGenerator` 中增加引用/解释；控制上下文长度、TopK、输出格式。
   - Prompt 优化：明确角色、输出格式、引用字段，避免幻觉；加入安全提示和失败回退。
3) 排序/加权：
   - 调整质量分、BM25、语义、投送量权重；可配置 A/B；一致性过滤（城市/户型）优先于排序。
   - 设计更细的 promotion 策略（上限、衰减），避免过度干预。
4) 评测与监控：
   - 构造查询-期望结果集，补单测；记录响应时间、召回率、TopK 点击/满意度指标。
   - 日志与可观测性：检索耗时拆解（过滤/BM25/语义/排序），异常告警。
5) 体验与接口：
   - Gradio/Streamlit UI 优化：提示、预填、结果说明；提供 FastAPI 接口便于集成。
