from pydantic import BaseModel, Field


class GenerationCreate(BaseModel):
    selections: dict[str, object] = Field(default_factory=dict)
    theme: str = ""
    mode: str = "standard"  # standard / refine


class RefineCreate(BaseModel):
    instruction: str = Field(min_length=1)


class InspireCreate(BaseModel):
    selections: dict[str, object] = Field(default_factory=dict)


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
