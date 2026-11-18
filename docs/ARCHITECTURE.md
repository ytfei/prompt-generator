# 提示词工坊（Prompt Studio）技术架构设计

> 版本：v0.1 ｜ 日期：2026-11-18 ｜ 基线：docs/PRD.md v0.1
> 技术约束：前端 React + pnpm；后端 Python + uv + LangChain/LangGraph/DeepAgents；SQLite 存历史；Make 简化指令。

---

## 1. 技术选型总览

| 层 | 选型 | 版本基线 | 理由 |
|----|------|----------|------|
| 前端框架 | React + TypeScript | React 18, TS 5 | 生态成熟，组件化贴合选项系统 |
| 前端构建 | Vite | 5.x | 启动快，HMR 好，代理后端方便 |
| 包管理 | pnpm（workspace） | 9.x | 用户指定；磁盘省、安装快 |
| 服务端状态 | TanStack Query | 5.x | 历史记录/模板的请求缓存与失效 |
| 客户端状态 | zustand | 5.x | 轻量管理 14 维度选择状态 |
| 后端框架 | FastAPI | 0.11x | 原生 async、Pydantic、SSE 友好 |
| Python 管理 | uv | 最新 | 用户指定；替代 pip/venv/poetry，速度极快 |
| Agent 编排 | LangChain + LangGraph | 0.3.x / 0.2.x | 状态图工作流，天然支持流式与 checkpointer |
| 深度迭代模式 | DeepAgents | 0.0.x | 基于 LangGraph，内置计划/子代理/文件系统，用于 P2 深度打磨 |
| 数据库 | SQLite + SQLAlchemy 2.0 + aiosqlite | — | 用户指定；单文件零运维，历史记录量级完全够用 |
| 迁移 | Alembic | 1.1x | 表结构演进可控（P1 后期引入也可） |
| LLM 接入 | LangChain `init_chat_model`，OpenAI 兼容协议 | — | 火山方舟（豆包）/ DeepSeek / OpenAI 等一套代码切换 |
| 开发指令 | Make | — | 用户指定；统一前后端入口 |

## 2. 总体架构

```
┌─────────────────────────── 浏览器 ───────────────────────────┐
│  React SPA (Vite)                                            │
│  选项面板(14维度) / 主题描述 / Agent步骤流(SSE) / 历史与模板   │
└───────────────┬──────────────────────────────────────────────┘
                │ REST(JSON) + SSE(text/event-stream)
┌───────────────▼──────────────────────────────────────────────┐
│  FastAPI (server/)                                           │
│  ├─ api/        路由层：options / generations / templates     │
│  ├─ agent/      LangGraph 工作流（本文 §5）                   │
│  └─ db/         SQLAlchemy + SQLite (data/prompt_studio.db)  │
└───────────────┬──────────────────────────────────────────────┘
                │ OpenAI 兼容协议（服务端持有 Key，前端零接触）
        ┌───────▼────────┐
        │  LLM 提供方     │  火山方舟 / DeepSeek / OpenAI / 本地模拟
        └────────────────┘
```

要点：
- **API Key 只存在于后端环境变量**，前端不感知任何模型配置。
- 生成过程用 **SSE 流式推送**，前端实时渲染 Agent 分步状态（P0 原型的模拟动画升级为真实事件流）。
- 维度定义（选项、提示词模板片段）由**后端 `/api/options` 下发**，后续调优不用改前端。

## 3. 仓库结构（Monorepo）

```
prompt-generator/
├── Makefile                  # 唯一开发入口（本文 §9）
├── README.md
├── docs/                     # PRD、架构文档
├── prototype/                # P0 静态原型（归档保留）
├── web/                      # 前端（pnpm 项目）
│   ├── package.json
│   ├── vite.config.ts        # dev 代理 /api → localhost:8000
│   ├── index.html
│   └── src/
│       ├── api/              # 请求封装 + SSE 客户端
│       ├── components/       # ChipGroup / ThemeInput / StepStream / ResultCard / HistoryList
│       ├── stores/           # zustand：selections（14 维度选择态）
│       ├── pages/            # Studio（工作台）/ History / Templates
│       └── types/            # 与后端 Pydantic 对齐的 TS 类型
└── server/                   # 后端（uv 项目）
    ├── pyproject.toml        # 依赖与脚本；uv sync 即装环境
    ├── .env.example          # LLM_PROVIDER / API Key / MODEL / DB 路径
    ├── alembic/              # 迁移（引入 Alembic 后）
    ├── data/                 # SQLite 文件（gitignore）
    ├── tests/
    └── app/
        ├── main.py           # FastAPI 实例、CORS、路由注册
        ├── core/config.py    # pydantic-settings 读 .env
        ├── api/              # routers: options.py, generations.py, templates.py
        ├── agent/
        │   ├── graph.py      # LangGraph 编排（本文 §5）
        │   ├── state.py      # TypedDict 图状态
        │   ├── nodes/        # parse_intent / enrich / conflict / assemble / refine
        │   ├── prompts/      # 各节点提示词模板（Markdown，便于调优）
        │   └── rules.py      # 纯规则冲突检查（情绪×色调等，不烧 token）
        ├── db/
        │   ├── models.py     # ORM 模型
        │   └── session.py    # async engine + session
        └── schemas/          # Pydantic 请求/响应/SSE 事件模型
```

## 4. 前端架构

- **路由**：`/`（工作台）、`/history`（历史记录）、`/templates`（我的模板）。
- **状态分层**：
  - `selections`（14 维度 + 主题文本）→ zustand， persists 到 localStorage（与 P0 行为一致）；
  - 历史/模板/选项定义 → TanStack Query（服务端状态，不进 store）。
- **SSE 客户端**：`fetch` + `ReadableStream` 手动解析 SSE（生成是一次性 POST 流，`EventSource` 不支持 POST）。事件渲染到 `<StepStream>`，收尾写入 `<ResultCard>`。
- **类型安全**：后端 Pydantic schema 通过脚本或手动同步为 `src/types/`（P1 手动同步即可，量小）。
- **组件化**：P0 原型的选项数据结构直接平移为后端下发的 JSON，`ChipGroup` 通用组件支持单选/多选/自定义输入三种模式。

## 5. Agent 架构（核心）

### 5.1 两种模式

| 模式 | 编排 | 用途 |
|------|------|------|
| 标准生成（P1） | LangGraph 显式状态图 | 快速、确定性强、成本可控，覆盖 90% 场景 |
| 深度迭代（P2） | DeepAgents（`create_deep_agent`，基于 LangGraph） | 「充分发挥」档位或用户点"再打磨"时启用：计划 → 多轮自我评审 → 子代理专责（风格考证/冲突审查）→ 汇总 |

### 5.2 LangGraph 标准生成图

```
START
  │
  ▼
parse_intent ──── LLM：解析主题描述 → 结构化 {主体, 动作, 场景, 意图}
  │                （主题为空则跳过，标记 atmosphere_mode）
  ▼
enrich_details ── LLM：按创意自由度，为未选择的维度推断补全
  │
  ▼
conflict_check ── 纯 Python 规则引擎先行（rules.py，零 token）：
  │                情绪×色调 / 用途×画幅 / 文字×负向…
  │                命中后仅对冲突项调用 LLM 改写
  ▼
assemble ──────── 模板 + LLM：组装结构化中文提示词（即梦友好）
  │
  ▼
refine ────────── LLM：润色自检，输出 Pydantic 结构化结果
  │                FinalPrompt { prompt, notes[], warnings[], suggested_ratio }
  ▼
END → 落库 → SSE result 事件
```

- **State**（`state.py`）：`theme, selections, parsed, enriched, conflicts, draft, final, messages`，节点只读写自己负责的字段。
- **结构化输出**：节点统一用 Pydantic schema + `with_structured_output`，杜绝自由文本解析失败。
- **流式**：`graph.astream_events()` → 每个节点进入/退出转为 SSE `step` 事件，与 P0 原型的四步动画体验对齐。
- **Checkpointer（P2）**：`SqliteSaver` 以 generation id 为 `thread_id`，支持"基于上一条继续改"的多轮迭代，历史即会话。
- **模型接入**：`core/llm.py` 用 `init_chat_model` 按环境变量实例化，支持 OpenAI 兼容端点（火山方舟示例：`base_url=https://ark.cn-beijing.volces.com/api/v3`，`model=ep-xxx 或 doubao-xxx`）。提供 `provider=mock` 模式（规则拼装、不调网），保证无 Key 也能开发联调与跑测试。

### 5.3 提示词管理

各节点提示词放 `agent/prompts/*.md`，加载时渲染变量。与代码分离，便于凭出图效果持续调优（PRD 开放问题 3 的反馈闭环在 P2 直接服务于此）。

## 6. 数据库设计（SQLite）

```sql
-- 生成历史
CREATE TABLE generations (
  id            TEXT PRIMARY KEY,              -- uuid4
  created_at    TEXT NOT NULL,                 -- ISO8601
  selections    TEXT NOT NULL,                 -- 14 维度选择(JSON)
  theme         TEXT DEFAULT '',               -- 主题描述
  final_prompt  TEXT NOT NULL,                 -- 最终提示词
  notes         TEXT DEFAULT '[]',             -- Agent 优化说明(JSON数组)
  warnings      TEXT DEFAULT '[]',             -- 冲突警告(JSON数组)
  model         TEXT NOT NULL,                 -- 生成所用模型标识
  mode          TEXT NOT NULL DEFAULT 'standard',  -- standard / deep
  favorite      INTEGER NOT NULL DEFAULT 0
);

-- 我的模板（配置快照复用）
CREATE TABLE templates (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  selections    TEXT NOT NULL,
  created_at    TEXT NOT NULL
);

-- 出图反馈闭环（P2，PRD 开放问题 3）
CREATE TABLE feedback (
  id            TEXT PRIMARY KEY,
  generation_id TEXT NOT NULL REFERENCES generations(id),
  rating        INTEGER,                       -- 1~5 或 好/一般/差
  comment       TEXT DEFAULT '',
  created_at    TEXT NOT NULL
);
```

- selections 存 JSON 而非拆列：14 维度会持续演化（PRD 开放问题 4），JSON 免迁移；查询只需按时间/收藏过滤，无需按维度检索。
- 并发场景为单人本地使用，SQLite WAL 模式足够；`aiosqlite` 配合 FastAPI 异步栈。

## 7. API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/options` | 下发 14 维度定义（选项、联动规则、预设模板） |
| POST | `/api/generations` | 创建生成，**响应为 SSE 流**（body: selections + theme + mode） |
| GET | `/api/generations` | 历史列表（`?limit=&offset=&favorite=`） |
| GET | `/api/generations/{id}` | 历史详情 |
| PATCH | `/api/generations/{id}` | 切换收藏 |
| DELETE | `/api/generations/{id}` | 删除 |
| GET/POST | `/api/templates` | 模板列表 / 保存当前配置为模板 |
| DELETE | `/api/templates/{id}` | 删除模板 |
| POST | `/api/generations/{id}/refine` | P2：基于该条继续迭代（DeepAgents / checkpointer 线程） |

**SSE 事件协议**（`POST /api/generations` 响应）：

```
event: step     data: {"node":"parse_intent","status":"running"}
event: step     data: {"node":"parse_intent","status":"done","detail":{"主体":"..."}}
event: warn     data: {"rule":"mood_tone","message":"忧郁×高饱和冲突，已调整"}
event: result   data: {"id":"...","prompt":"...","notes":[...],"suggested_ratio":"16:9"}
event: error    data: {"message":"模型调用失败：..."}
```

前端据此渲染分步动画（与 P0 体验一致）、警告条与最终结果。

## 8. 配置与安全

`server/.env.example`（供应商与模型留空，由用户自行填写；未填写时使用 mock 模式开发）：

```bash
# ── LLM 配置（待填写；留空时自动回落 mock 模式，不调用真实模型）──
LLM_PROVIDER=               # mock | ark | openai | deepseek ...
LLM_BASE_URL=               # OpenAI 兼容端点，如火山方舟 https://ark.cn-beijing.volces.com/api/v3
LLM_API_KEY=                # 仅服务端持有
LLM_MODEL=                  # 模型名或接入点 ID
# ── 存储 ──
DATABASE_URL=sqlite+aiosqlite:///./data/prompt_studio.db
```

- Key 不进 Git（`.env` gitignore）；前端任何响应不回显 Key。
- CORS 仅放行 `http://localhost:5173`。
- SQLite 文件目录 `server/data/` gitignore。
- 日志：后端结构化日志（uvicorn + logging），Agent 各节点记录耗时与 token 用量，便于后续成本观测。

## 9. 开发工作流（Makefile）

根目录 `Makefile` 为唯一入口：

```makefile
.PHONY: install dev api web lint format test db-migrate clean

install:            ## 安装前后端依赖
	pnpm --dir web install
	cd server && uv sync

api:                ## 启动后端（热重载, :8100）
	cd server && uv run uvicorn app.main:app --reload --port 8100

web:                ## 启动前端（:5173）
	pnpm --dir web dev

dev:                ## 同时启动前后端
	$(MAKE) -j2 api web

lint:               ## 后端 ruff + 前端 eslint
	cd server && uv run ruff check app tests
	pnpm --dir web lint

format:             ## 统一格式化
	cd server && uv run ruff format app tests
	pnpm --dir web format

test:               ## 全部测试
	cd server && uv run pytest
	pnpm --dir web test

db-migrate:         ## 数据库迁移（引入 Alembic 后生效）
	cd server && uv run alembic upgrade head

clean:              ## 清理缓存与构建产物
	rm -rf web/dist web/node_modules/.vite server/.pytest_cache server/**/__pycache__
```

- 依赖变更统一走 `uv add`（后端）/ `pnpm add`（前端），lock 文件（`uv.lock`、`pnpm-lock.yaml`）入库。
- Python 版本由 `server/.python-version` 钉住，uv 自动管理解释器。

## 10. 实施计划（对齐 PRD P1）

| 里程碑 | 内容 | 验收 |
|--------|------|------|
| M1 脚手架 | Monorepo + Makefile + 前后端空应用跑通 `make dev` | 两端启动、代理连通、health 检查通过 |
| M2 选项与配置 | `/api/options` 下发维度；前端工作台还原 P0 全部交互；selections 入 store | 14 维度点选/联动/持久化与原型一致 |
| M3 生成链路（mock） | LangGraph 五节点 + rules.py + SSE；`provider=mock` 免 Key 跑通全流程 | 点击生成看到真实事件流，产出结构化提示词 |
| M4 真实 LLM | `init_chat_model` 接方舟/其他 OpenAI 兼容端点；refine 结构化输出 | 真实模型生成质量达标；Key 安全约定落实 |
| M5 历史与模板 | SQLite 三表 + generations/templates CRUD + 历史页 | 复制、收藏、删除、模板复用可用 |
| P2 起 | DeepAgents 深度迭代、checkpointer 多轮修改、feedback 闭环、双语 | 另行细化 |

## 11. 风险与决策记录

| 事项 | 决策 | 备选/说明 |
|------|------|-----------|
| DeepAgents 现在就上还是 P2 | P2 引入 | 标准生成是确定性工作流，LangGraph 显式图更可控；DeepAgents 的计划/子代理能力留给深度迭代 |
| 迁移工具 | M5 前用 `create_all`，M5 引入 Alembic | 表少，前期重建成本低 |
| 维度定义放前端还是后端 | 后端下发 | 调优选项/预设不发版；前端只做渲染 |
| 模型供应商 | 通过 `LLM_PROVIDER` 抽象 | 火山方舟/DeepSeek/OpenAI 均走 OpenAI 兼容协议，一套代码 |
| 无 Key 开发 | `provider=mock` | CI 与本地联调不依赖真实模型 |

## 12. 已确认决策（2026-11-18）

1. **LLM 供应商与模型**：不预选。写入 `server/.env`，由用户自行填写（`.env.example` 留空）；未填写时后端自动回落 mock 模式，开发与测试不受阻。
2. **用户体系**：不做。产品定位为单用户本地工具，无登录、无多租户，简化后端为无鉴权设计（仅绑定 localhost）。
3. **数据备份**：不做。SQLite 仅本地单文件，用户自行决定是否纳入系统级备份。
