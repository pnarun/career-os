"""Pydantic models for career analytics API responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SalarySkillItem(BaseModel):
    skill: str
    avg_salary: int
    job_count: int = 0
    estimated_premium: int | None = None


class SalaryInsightsResponse(BaseModel):
    average_salary: str
    salary_range: str = ""
    top_paying_skills: list[SalarySkillItem] = Field(default_factory=list)
    salary_growth_trend: str
    remote_salary_premium: str
    provider_salary_distribution: list[dict[str, Any]] = Field(default_factory=list)
    primary_role: str = ""
    salary_data_points: int = 0


class CareerGrowthResponse(BaseModel):
    career_growth_score: int
    primary_role: str = ""
    insights: list[str] = Field(default_factory=list)
    avg_market_match: int = 0
    high_match_roles: int = 0
    skill_coverage_score: int = 0
    market_fit_score: int = 0


class WeeklyInsightsResponse(BaseModel):
    strongest_opportunities: list[str] = Field(default_factory=list)
    top_missing_skill: str = ""
    career_growth_score: int = 0
    headline: str = ""
    summary_lines: list[str] = Field(default_factory=list)


class CareerAnalyticsDashboard(BaseModel):
    salary_insights: dict[str, Any] = Field(default_factory=dict)
    market_trends: dict[str, Any] = Field(default_factory=dict)
    skill_demand: dict[str, Any] = Field(default_factory=dict)
    application_funnel: dict[str, Any] = Field(default_factory=dict)
    provider_performance: dict[str, Any] = Field(default_factory=dict)
    career_growth: dict[str, Any] = Field(default_factory=dict)
    role_transitions: dict[str, Any] = Field(default_factory=dict)
    market_heatmap: dict[str, Any] = Field(default_factory=dict)
    weekly_insights: dict[str, Any] = Field(default_factory=dict)
    career_growth_score: int = 0
