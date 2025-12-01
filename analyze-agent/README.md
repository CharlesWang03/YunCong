# **Analyze Agent — 房产检索与智能分析助手**

一个可扩展的房产搜索与分析 Demo，支持**结构化过滤、BM25 词法检索、语义向量检索、LLM 分析报告生成、Excel 上传解析**等能力。
面向“数据分析助手”类任务构建，具备工程化管线、可插拔索引、可扩展模式设计。

---

## **核心能力概览**

### 🔍 **多路线检索管线**

系统同时支持三类主流检索方式：

1. **结构化硬过滤**：按城市、区域、价格区间、面积、户型、学区等字段进行约束过滤
2. **词法检索（BM25）**：TF-IDF + jieba 分词，对房源描述文本执行词法匹配
3. **语义检索（向量）**：bge-small-zh + FAISS，对自然语言需求执行语义召回

三路信号可融合排序，得到更可靠的 TopN 结果。

---

### 🧮 **可解释排序机制**

最终评分包含：

| 信号               | 作用                     | 特点             |
| ---------------- | ---------------------- | -------------- |
| **质量分**          | 房龄/单价/面积/地铁/学区等八维特征归一化 | 体现“性价比”与“宜居度”  |
| **BM25 分数**      | 文本词法相关性                | 对显式关键词强敏感      |
| **语义分数**         | 需求与房源描述的 embedding 相似度 | 处理模糊需求与语义召回    |
| **Promotion 加成** | 可控曝光加权（不失控）            | 防止“买榜”，乘性且上限约束 |

默认权重：`0.6（质量） + 0.2（BM25） + 0.2（语义）`。

---

### 🧠 **LLM 分析报告**

提供结构化购房助手能力：

* 自动统计 TopN 房源的**价格区间、面积分布、主流户型、地铁比率、学区率**
* 输出自然语言报告（推荐理由、优缺点、是否满足用户需求）
* 支持默认库与上传 Excel 的分析

---

### 📄 **文件解析（模式 4）**

用户可上传自己的 Excel 房源表：系统将自动完成：

1. 字段映射与清洗
2. 构建会话级 BM25/向量索引（不落盘）
3. 基于上传数据执行筛选 / 检索 / 报告生成

---

## **系统模块结构**

```
analyze-agent/
│
├── data/                         # 示例 Excel & 清洗后 Parquet
├── src/
│   ├── pipeline/                 # 数据处理与索引构建
│   │   ├── generate_listings.py
│   │   ├── preprocess.py
│   │   ├── build_bm25.py
│   │   ├── build_vectors.py
│   │   └── excel_parser.py       # 上传文件解析
│   │
│   ├── retrieval/                # 检索逻辑：过滤、BM25、向量
│   ├── ranking/                  # 打分策略与融合排序
│   ├── agent/                    # Orchestrator 与 LLM 报告生成
│   └── app/
│       ├── gradio_app.py         # 前端 UI（4 模式）
│       └── assistant_api.py
│
├── scripts/                      # 一键构建/启动脚本
├── config.py                     # 全局配置与可调参数
└── README.md
```

---

## **四大模式（产品化能力）**

### **模式 1 — Filter（结构化过滤）**

* 按字段筛选（城市/价格/面积/户型/学区等）
* 不走文本检索，延迟最低
* 适合运营或规则化查询

---

### **模式 2 — Search（多模态搜索）**

* 文本查询 → BM25 + 语义向量召回
* 融合排序后展示 TopN 房源
* 适合自然语言搜索（例如：“北京海淀 两室 地铁附近”）

---

### **模式 3 — Assistant（智能分析报告）**

基于查询 → 检索 → 排序的候选结果，生成：

* 房源总结
* 推荐逻辑
* 风险提示（房龄、楼层、噪声因素）
* 建议预算或区位调整

---

### **模式 4 — 上传 Excel（文件工作流）**

1. 接受一份任意用户 Excel
2. 自适应解析列名 → 内部 schema
3. 在内存中构建 BM25/向量索引
4. 对上传数据集运行完整助手流程

> 一个支持“临时数据源”的分析 Agent（文件级 RAG 工作流）。

---

## **评分策略**

```
final_score = (0.6 * quality_score) +
               (0.2 * bm25_score_norm) +
               (0.2 * semantic_score_norm)

final_score = final_score * (1 + max_boost * sqrt(promotion_score))
```

* 所有检索信号 min-max 归一化
* 业务质量分可解释、可调
* Promotion 为乘性且上限约束，避免异常曝光

---

## **运行方式（完整流程）**

### **1. 环境准备**

```bash
cd analyze-agent
conda activate llm_env
pip install -r requirements.txt

cp .env.example .env       # 填入 OPENAI_API_KEY
```

---

### **2. 构建数据与索引（首次运行需执行）**

```bash
python -m src.pipeline.generate_listings
python -m src.pipeline.preprocess
python -m src.pipeline.build_bm25
python -m src.pipeline.build_vectors
```

---

### **3. 启动 Gradio UI**

```bash
python -m src.app.gradio_app
```

访问：`http://127.0.0.1:7860`

---

## **自动化脚本**

* **scripts/setup.sh**
  一键安装依赖、生成示例数据、构建索引
* **scripts/start_gradio.sh**
  检查索引 → 启动 Gradio UI

---

## **已知限制**

* 某些 Gradio 版本的 boolean schema 会导致 API 解析报错，已在代码中加入兼容补丁
* 上传 Excel 若字段命名过于非标准，需要手动补齐映射表

---

## **未来可扩展方向**

1. Excel结构化入库优化
2. LLM生成优化
3. 设计评测、调参，用于优化推荐策略
4. 用户搜索日志留存
5. 模式4对话历史管理
6. 模式 5：上传 Excel 与默认库混合召回
7. 添加系统运行信息显示，方便报错调试
