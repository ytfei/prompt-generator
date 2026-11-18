from pydantic import BaseModel, Field


class GenerationCreate(BaseModel):
    selections: dict[str, object] = Field(default_factory=dict)
    theme: str = ""
    mode: str = "standard"  # standard（P2 增加 deep）


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


class TemplateCreate(BaseModel):
    name: str
    selections: dict[str, object]


class TemplateOut(BaseModel):
    id: str
    name: str
    selections: dict[str, object]
    created_at: str
