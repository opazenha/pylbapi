from fastapi import APIRouter, HTTPException
from app.schemas.partner import PartnerCreate, PartnerOut
from app.db.database import Database
from typing import Any
from urllib.parse import urljoin

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

@router.delete(
    "/{partner_name}",
    response_model=PartnerOut,
    summary="Delete Partner by Name",
    description="Deletes a partner by name and returns the deleted partner info.",
    responses={
        200: {"description": "Partner successfully deleted"},
        404: {"description": "Partner not found"},
        500: {"description": "Database error"}
    },
    tags=["partners"]
)
async def delete_partner(partner_name: str):
    # Trim whitespace and find partner by exact name
    partner_name = partner_name.strip()
    partner = await Database.find_one("partners", {"name": partner_name})
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    # Delete partner
    await Database.delete_one("partners", {"name": partner_name})
    # Convert MongoDB _id to id field
    if "_id" in partner:
        partner["id"] = str(partner["_id"])
        del partner["_id"]
    # Ensure transfermarktUrl is absolute for Pydantic validation
    if "transfermarktUrl" in partner and partner["transfermarktUrl"] and partner["transfermarktUrl"].startswith("/"):
        partner["transfermarktUrl"] = urljoin("https://www.transfermarkt.com", partner["transfermarktUrl"])
    return PartnerOut(**partner)