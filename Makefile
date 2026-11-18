.PHONY: install dev api web lint format test db-migrate clean help

help:              ## 显示可用指令
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

install:           ## 安装前后端依赖
	pnpm --dir web install
	cd server && uv sync

api:               ## 启动后端（热重载, :8100）
	cd server && uv run uvicorn app.main:app --reload --port 8100

web:               ## 启动前端（:5173）
	pnpm --dir web dev

dev:               ## 同时启动前后端
	$(MAKE) -j2 api web

lint:              ## 后端 ruff 检查 + 前端类型检查
	cd server && uv run ruff check app tests
	pnpm --dir web lint

format:            ## 后端格式化
	cd server && uv run ruff format app tests

test:              ## 全部测试（后端 pytest + 前端占位）
	cd server && uv run pytest
	pnpm --dir web test

db-migrate:        ## 数据库迁移（引入 Alembic 后生效）
	cd server && uv run alembic upgrade head

clean:             ## 清理缓存与构建产物
	rm -rf web/dist web/node_modules/.vite server/.pytest_cache server/data
	find server -name __pycache__ -type d -exec rm -rf {} +
