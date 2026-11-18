from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.i2i import stream_i2i
from app.schemas import I2ICreate

router = APIRouter(prefix="/api/i2i-generations", tags=["i2i"])


@router.post("")
async def create_i2i(body: I2ICreate):
    """图生图提示词生成，响应为 SSE 流（step/result/error 事件）。

    与文生图的差异：不传原图，只传图片内容描述（PRD v0.2，原图由用户在即梦上传）。
    结果落库 generations 表，mode='i2i'，历史页可查。
    """
    return StreamingResponse(
        stream_i2i(body.model_dump()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
