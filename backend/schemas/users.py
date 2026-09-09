from pydantic import BaseModel, Field

class UpdateProfileInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str
