# 提示词工坊（Prompt Studio）

文生图提示词工作台：参数化选项 + 主题描述 + Agent 生成优化，产出可粘贴到「即梦」的高质量提示词。

- 需求文档：`docs/PRD.md`
- 架构设计：`docs/ARCHITECTURE.md`
- P0 静态原型（归档）：`prototype/index.html`

## 快速开始

```bash
make install   # 安装前后端依赖（pnpm + uv）
make dev       # 同时启动后端 :8100 与前端 :5173
```

打开 http://localhost:5173 即可使用。

## LLM 配置

后端默认 mock 模式（本地规则/模板生成，不联网）。要接入真实模型，复制并填写：

```bash
cd server
cp .env.example .env
# 填写 LLM_PROVIDER / LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
```

任何 OpenAI 兼容端点均可（火山方舟、DeepSeek、OpenAI 等）。

## 常用指令

| 指令 | 说明 |
|------|------|
| `make dev` | 前后端并行启动 |
| `make test` | 运行后端 pytest |
| `make lint` | ruff + 前端类型检查 |
| `make clean` | 清理缓存与本地数据库 |
