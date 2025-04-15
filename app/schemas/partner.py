from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class PartnerCreate(BaseModel):
    name: str = Field(..., description="Partner name")
    transfermarktUrl: Optional[HttpUrl] = Field(None, description="Transfermarkt profile URL")
    notes: Optional[str] = Field(None, description="Additional notes")

class PartnerOut(BaseModel):
    id: str = Field(..., description="Partner ID")
    name: str = Field(..., description="Partner name")
    transfermarktUrl: Optional[HttpUrl] = Field(None, description="Transfermarkt profile URL")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        # Allow conversion from string to HttpUrl when creating the model
        json_encoders = {
            HttpUrl: str
        }
