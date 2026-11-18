from pydantic import BaseModel, Field


class GenerationCreate(BaseModel):
    selections: dict[str, object] = Field(default_factory=dict)
    theme: str = ""
    mode: str = "standard"  # standard / refine
    model_tier: str = "default"  # default / nano / mid / pro（未配置的档位回落默认模型）


class RefineCreate(BaseModel):
    instruction: str = Field(min_length=1)
    model_tier: str = "default"


class InspireCreate(BaseModel):
    selections: dict[str, object] = Field(default_factory=dict)
    model_tier: str = "default"
    theme: str = ""  # 已填写时围绕主题生成变体，留空时按配置发散


class FeedbackCreate(BaseModel):
    rating: int  # 1=出图好，-1=出图差
    comment: str = ""


class GenerationUpdate(BaseModel):
    favorite: bool | None = None
    tags: list[str] | None = None
    note: str | None = None


class GenerationOut(BaseModel):
    id: str
    created_at: str
    selections: dict[str, object]
    theme: str
    final_prompt: str
    notes: list[dict]
    warnings: list[dict]
    model: str
    mode: str
    favorite: bool
    parent_id: str | None = None
    rating: int | None = None
    tags: list[str] = Field(default_factory=list)
    note: str = ""


class TemplateCreate(BaseModel):
    name: str
    selections: dict[str, object]


class TemplateOut(BaseModel):
    id: str
    name: str
    selections: dict[str, object]
    created_at: str
