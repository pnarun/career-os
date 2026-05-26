"""Autocomplete suggestions for settings (roles, skills, companies)."""

from fastapi import APIRouter, Query

from app.data.search_suggestions import (
    suggest_companies,
    suggest_locations,
    suggest_roles,
    suggest_skills,
)

router = APIRouter(tags=["suggestions"])


@router.get("/suggestions/roles")
async def get_role_suggestions(q: str = Query(default=""), limit: int = Query(default=12, le=20)) -> dict:
    return {"suggestions": suggest_roles(q, limit=limit)}


@router.get("/suggestions/skills")
async def get_skill_suggestions(q: str = Query(default=""), limit: int = Query(default=12, le=20)) -> dict:
    return {"suggestions": suggest_skills(q, limit=limit)}


@router.get("/suggestions/companies")
async def get_company_suggestions(q: str = Query(default=""), limit: int = Query(default=12, le=20)) -> dict:
    return {"suggestions": suggest_companies(q, limit=limit)}


@router.get("/suggestions/locations")
async def get_location_suggestions(q: str = Query(default=""), limit: int = Query(default=12, le=20)) -> dict:
    return {"suggestions": suggest_locations(q, limit=limit)}
