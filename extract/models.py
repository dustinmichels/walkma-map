from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Theme(BaseModel):
    theme_id: str
    theme: Optional[str] = None


class Organization(BaseModel):
    org_id: str
    organization: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None


class Facilitator(BaseModel):
    facilitator_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None


class WalkAuditExport(BaseModel):
    """Represents a cleaned walk audit record for CSV export."""

    @model_validator(mode="before")
    @classmethod
    def strip_strings(cls, data):
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}

    audit_id: Optional[Any] = None
    city_or_town: Optional[str] = None
    audit_date: Optional[str] = None
    report_date: Optional[str] = None
    year: Optional[Any] = None
    summary: Optional[str] = None
    long_term_rec: Optional[str] = None
    short_term_rec: Optional[str] = None
    area_covered: Optional[str] = None
    start_address: Optional[str] = None
    lat_lon: Optional[str] = None
    themes: Optional[str] = None
    organizations: Optional[str] = None
    facilitators: Optional[str] = None
    instigating_incident: Optional[str] = None
    applied_for_grant: Optional[str] = None
    name_of_grant: Optional[str] = None
    audit_pdf: Optional[str] = None
    grant_pdf: Optional[str] = None
    gpx_file: Optional[str] = None


class WalkAuditDownload(BaseModel):
    """Represents a single walk audit record from the new spreadsheet structure."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    audit_id: Optional[Any] = Field(None, alias="audit_id")
    city_town: Optional[str] = Field(None, alias="CITY/TOWN")
    year: Optional[Any] = Field(None, alias="YEAR")
    neighborhood: Optional[str] = Field(None, alias="NEIGHBORHOOD")
    summary: Optional[str] = Field(None, alias="SUMMARY")
    long_term_recommendations: Optional[str] = Field(
        None, alias="LONG TERM RECOMMENDATIONS"
    )
    short_term_recommendations: Optional[str] = Field(
        None, alias="SHORT TERM RECOMMENDATIONS"
    )
    streets_area_covered: Optional[str] = Field(
        None, alias="STREETS, INNTERSECTIONS + AREA COVERED"
    )
    themes: Optional[str] = Field(None, alias="THEMES")

    # View fields (Custom logic for links)
    view_text: Optional[str] = Field(None, alias="VIEW")
    view_link: Optional[str] = Field(None)

    facilitator_author: Optional[str] = Field(None, alias="FACILITATOR/AUTHOR")
    organizations: Optional[str] = Field(None, alias="ORGANIZATIONS")
    plain_text: Optional[str] = Field(None, alias="Plain Text")
    audit_date: Optional[Any] = Field(None, alias="audit_date")
    report_date: Optional[Any] = Field(None, alias="report_date")
    start_address: Optional[str] = Field(None, alias="start_address")
    google_maps: Optional[str] = Field(None, alias="google_maps")
    neighborhood_parsed: Optional[str] = Field(None, alias="neighborhood_parsed")
