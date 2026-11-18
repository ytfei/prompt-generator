from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.refine import setup_refine, teardown_refine
from app.api import generations, inspire, options, templates
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # refine 图的 checkpointer 与业务库同目录
    db_file = settings.database_url.split("///")[-1]
    await setup_refine(db_file.rsplit("/", 1)[0] + "/checkpoints.db")
    yield
    await teardown_refine()


app = FastAPI(title="Prompt Studio API", version="0.1.0", lifespan=lifespan)

# 单用户本地工具：仅放行本地前端 dev 地址，无鉴权
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(options.router)
app.include_router(generations.router)
app.include_router(templates.router)
app.include_router(inspire.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
