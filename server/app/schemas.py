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


class FeedbackCreate(BaseModel):
    rating: int  # 1=出图好，-1=出图差
    comment: str = ""


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


class TemplateCreate(BaseModel):
    name: str
    selections: dict[str, object]


class TemplateOut(BaseModel):
    id: str
    name: str
    selections: dict[str, object]
    created_at: str
