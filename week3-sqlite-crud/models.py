from pydantic import BaseModel, field_validator

class TaskIn(BaseModel):
    title: str
    done: bool = False

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v
