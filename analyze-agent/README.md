# Analyze Agent

房产检索与智能助手多模态 Demo：支持硬条件筛选、BM25 词法检索、语义向量检索，以及 LLM 生成的分析报告。新增「模式4：上传 Excel 分析」，可对用户上传的房源表做临时索引与报告生成。

## 目标与能力
- 数据准备：生成+清洗示例房源到 Parquet；支持上传 Excel 后即时构建索引。
- 检索三路线：① 结构化硬过滤（城市/价格/面积/户型/学区等）；② 词法 BM25（TF-IDF + jieba）；③ 语义向量（bge-small-zh + FAISS）。
- 排序：质量分（多维归一化）+ BM25 + 语义分，叠加可控 promotion 加成。
- LLM 报告：对 TopN 结果做统计摘要（价格/面积/户型/地铁/学区等），生成结构化购房分析报告。

## 当前进展
- 数据管线：`generate_listings` 分层随机生成房源；`preprocess` 清洗；`build_bm25` 词法索引；`build_vectors` 语义索引。
- 检索/排序：Filter 模式仅硬过滤；Search/Assistant 融合 BM25+语义+质量分；promotion 乘性上限。
- 模式4：上传 Excel 后，在内存中构建 BM25/向量索引，复用助手模式完成检索与报告。
- UI：Gradio 提供 4 个模式；如需后台可自启 Streamlit 仪表盘。

## 模式说明
- 模式1 Filter：仅硬条件过滤；不走 BM25/语义，速度最快。
- 模式2 Search：文本查询 → BM25 + 语义检索 → 排序 → 列表返回。
- 模式3 Assistant：文本/过滤 → 检索 + 排序 → 统计摘要 → LLM 生成分析报告。
- 模式4 上传 Excel：上传房源表，构建会话级内存索引，在该数据集上运行模式3的分析与报告。

### 模式4工作流（核心步骤）
1) 上传文件：前端 `gr.File`；点击“加载 Excel”触发。
2) 解析清洗：`excel_parser.parse_uploaded_excel` 读取文件、映射常见中文列名，调用 `preprocess_dataframe` 对齐 schema。
3) 临时索引：`build_bm25_from_dataframe`、`build_vectors_from_dataframe` 返回 BM25/向量索引（不落盘）。
4) 会话上下文：封装为 `SessionDataContext`（df + bm25 + vector），仅当前会话有效。
5) 检索与报告：查询按钮复用 `Orchestrator.run_assistant`，数据源改用会话上下文，输出 TopN 表格 + LLM 报告；未上传则提示先上传。

## 评分策略概要
- 质量分：8 维（价格/面积/房龄/地铁/学区/楼层/朝向/装修），归一化到 [0,1] 后按权重线性组合。
- BM25/语义分：每次检索内做 min-max 归一化；默认权重 0.6 / 0.2 / 0.2。
- Promotion：乘性增益 `final = base * (1 + max_boost * sqrt(promotion_score))`，防止“花钱买榜”失控。

## 使用指南（conda 环境 llm_env）
```bash
cd analyze-agent
conda activate llm_env
pip install -r requirements.txt
# 若首次运行或数据/索引未生成，执行：
python -m src.pipeline.generate_listings   # 生成示例 Excel（分层覆盖）
python -m src.pipeline.preprocess          # 清洗为 Parquet
python -m src.pipeline.build_bm25          # 构建 BM25(TF-IDF+jieba)
python -m src.pipeline.build_vectors       # 构建语义索引(bge-small-zh + FAISS)
# 启动 Gradio（含模式1/2/3/4）
python -m src.app.gradio_app
```
> 如语义模型加载失败，请检查 torch/torchvision/transformers/sentence-transformers 版本是否与 requirements 匹配。

## 一键脚本
端到端（含生成数据与索引）：`bash run_all.sh`（Windows 可在 Git Bash/WSL 下执行）。已生成数据时可注释脚本中前四步，只保留 Gradio 启动。

## 已知问题与提示
- Gradio API schema 若遇到 boolean schema 报错，已在代码中对 gradio_client 的解析做兼容补丁；如仍异常，可重装依赖或清理缓存后再试。
- 上传 Excel 时请确保列名可映射到内部字段（城市/区县/总价/面积/户型/地铁/学区等），缺失字段将使用缺省值。

## 下一步优化方向
1) 前端体验：优化界面布局与样式，让四个模式的展示更直观美观（列表/卡片、颜色与字体统一）。  
2) 模式3/4 Prompt：重写 LLM 提示词，贴近“分析报告”格式，控制数字精度与语气。  
3) 评测与调参：设计 20 条随机输入的评测集，打通自动评测与权重调参工具，量化检索/排序准确度。  
4) 检索效率：缓存小模型、缩短向量维度、减少 top_k；必要时分“快速/深度”两级检索。  
5) 排序调优：A/B 调整质量权重、promotion 曲线，记录评分解释。  
6) UI 与可视化：补充 Streamlit 仪表盘、导出 CSV、评分解释面板。  
7) 预留模式5：上传数据稀疏时，考虑与默认全库混合召回与排序（入口已在代码注释中预留）。  
