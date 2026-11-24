from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class UpdatePreferencesSchema(BaseModel):
    """Schema for updating user preferences and hard dealbreakers."""
    preferred_roles: Optional[List[str]] = Field(default=None, description="Target job titles or role keywords")
    preferred_skills: Optional[List[str]] = Field(default=None, description="Preferred programming languages or frameworks")
    company_preference: Optional[List[str]] = Field(default=None, description="Preferred company types e.g. Startup, Enterprise")
    work_mode: Optional[List[str]] = Field(default=None, description="Preferred work modes: Remote, Hybrid, Onsite")
    preferred_locations: Optional[List[str]] = Field(default=None, description="Target cities or regions")
    excluded_locations: Optional[List[str]] = Field(default=None, description="Cities explicitly prohibited")
    prohibited_companies: Optional[List[str]] = Field(default=None, description="Companies candidate refuses to work for")
    no_unpaid: Optional[bool] = Field(default=None, description="Whether unpaid internships are strictly prohibited (Dealbreaker)")
    relocation_allowed: Optional[bool] = Field(default=None, description="Willingness to relocate to another city")


class SearchOpportunitiesSchema(BaseModel):
    """Schema for searching job and internship opportunities."""
    query: str = Field(description="Search keywords or semantic intention")
    work_mode: Optional[str] = Field(default=None, description="Filter by Remote, Hybrid, or Onsite")
    location: Optional[str] = Field(default=None, description="Filter by city name")
    exclude_unpaid: Optional[bool] = Field(default=True, description="Whether to filter out unpaid postings")
    limit: Optional[int] = Field(default=5, description="Maximum number of results to return")


class CompareOpportunitiesSchema(BaseModel):
    """Schema for side-by-side opportunity comparison."""
    opportunity_ids: List[str] = Field(description="List of 2 to 4 opportunity UUIDs to compare")


class ExplainRecommendationSchema(BaseModel):
    """Schema for explaining why an opportunity was recommended."""
    opportunity_id: str = Field(description="UUID of the opportunity to explain")


class IdentifySkillGapsSchema(BaseModel):
    """Schema for analyzing market skill gaps."""
    target_role: Optional[str] = Field(default=None, description="Target job role to tailor gap analysis")


class GetUserProfileSchema(BaseModel):
    """Schema for retrieving active candidate profile metadata."""
    include_resume: Optional[bool] = Field(default=True, description="Whether to include parsed resume skills")
