from typing import Optional, Union, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

class PlayerRegistration(BaseModel):
    """Schema for registering a player with additional metadata."""
    transfermarktId: Optional[str] = Field(None, description="Transfermarkt player ID")
    transfermarkt: Optional[str] = Field(None, description="Transfermarkt player ID (alternative field name)")
    youtubeUrl: Optional[str] = Field(None, description="YouTube URL for player videos")
    notes: Optional[str] = Field(None, description="Additional notes about the player")
    partnerId: Optional[str] = Field(None, description="ID of the associated partner")
    
    @model_validator(mode='after')
    def validate_transfermarkt_id(self) -> 'PlayerRegistration':
        """Ensure either transfermarktId or transfermarkt is provided."""
        if not self.transfermarktId and not self.transfermarkt:
            raise ValueError("Either transfermarktId or transfermarkt must be provided")
        
        # If transfermarktId is not provided but transfermarkt is, use transfermarkt value
        if not self.transfermarktId and self.transfermarkt:
            self.transfermarktId = self.transfermarkt
            
        return self
    
    @field_validator('youtubeUrl')
    @classmethod
    def validate_youtube_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate and format YouTube URL."""
        if not v:
            return None
            
        # If URL doesn't start with http:// or https://, add https://
        if not v.startswith(('http://', 'https://')):
            v = f"https://{v}"
            
        return v
