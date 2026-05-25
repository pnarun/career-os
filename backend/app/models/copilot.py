"""Pydantic models for Career Copilot API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = ""


class RecommendationCard(BaseModel):
    type: str
    title: str
    subtitle: str = ""
    reasons: list[str] = Field(default_factory=list)


class CopilotChatResponse(BaseModel):
    session_id: str
    message: str
    intent: str
    reasons: list[str] = Field(default_factory=list)
    recommendations: list[RecommendationCard] = Field(default_factory=list)
    context_summary: dict[str, Any] = Field(default_factory=dict)
    source: str = "grounded"


class QuickActionRequest(BaseModel):
    action_id: str
    session_id: str = ""


class CopilotOverviewResponse(BaseModel):
    context_summary: dict[str, Any] = Field(default_factory=dict)
    quick_actions: list[dict[str, str]] = Field(default_factory=list)
    top_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    gemini_enabled: bool = False
