from fastapi import APIRouter, HTTPException
from app.schemas.partner import PartnerCreate, PartnerOut
from app.db.database import Database
from typing import Any

router = APIRouter()

@router.post(
    "/", 
    response_model=PartnerOut, 
    summary="Register a New Partner", 
    description="Register a partner with the system. Only the name field is required. The transfermarktUrl and notes fields are optional.",
    responses={
        201: {"description": "Partner successfully registered"},
        422: {"description": "Validation error in request data"},
        500: {"description": "Database error"}
    },
    status_code=201,
    tags=["partners"]
)
async def register_partner(partner: PartnerCreate):
    # Convert to dict and handle HttpUrl conversion to string
    data = {
        "name": partner.name,
        "notes": partner.notes
    }
    
    # Convert HttpUrl to string if present
    if partner.transfermarktUrl:
        data["transfermarktUrl"] = str(partner.transfermarktUrl)
    
    # Insert into MongoDB
    inserted_id = await Database.insert_one("partners", data)
    data["id"] = str(inserted_id)
    return PartnerOut(**data)
