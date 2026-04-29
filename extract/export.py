import csv
import json
import os
import random
import re
import string

from models import Facilitator, Organization, Theme, WalkAuditDownload, WalkAuditExport

JSON_INPUT_PATH = "data/download/sheet.json"
TSV_OUTPUT_PATH = "data/output/audits.tsv"
FACILITATORS_OUTPUT_PATH = "data/output/facilitators.tsv"
ORGANIZATIONS_OUTPUT_PATH = "data/output/organizations.tsv"
THEMES_OUTPUT_PATH = "data/output/themes.tsv"


def split_list(value: str) -> list[str]:
    return [
        p.strip().strip('"').strip()
        for p in re.split(r"\s*[&,]\s*", value)
        if p.strip().strip('"').strip()
    ]


def normalize_list(value: str | None) -> str | None:
    if not value:
        return value
    seen = {}
    for p in split_list(value):
        seen.setdefault(p.lower(), p)
    parts = list(seen.values())
    quoted = [f'"{p}"' if " " in p else p for p in parts]
    return ", ".join(quoted)


def random_id(prefix: str) -> str:
    chars = string.ascii_letters + string.digits
    return prefix + "".join(random.choices(chars, k=8))


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [p.strip().strip('"') for p in value.split(",") if p.strip().strip('"')]


def extract_themes(exports: list[WalkAuditExport]) -> list[Theme]:
    seen: dict[str, Theme] = {}
    for row in exports:
        for name in parse_list(row.themes):
            if name not in seen:
                seen[name] = Theme(theme_id=random_id("thm-"), theme=name)
    return list(seen.values())


def extract_organizations(exports: list[WalkAuditExport]) -> list[Organization]:
    seen: dict[str, Organization] = {}
    for row in exports:
        for name in parse_list(row.organizations):
            if name not in seen:
                seen[name] = Organization(org_id=random_id("org-"), organization=name)
    return list(seen.values())


def extract_facilitators(exports: list[WalkAuditExport]) -> list[Facilitator]:
    seen: dict[str, Facilitator] = {}
    for row in exports:
        for name in parse_list(row.facilitators):
            if name == "WalkMass":
                name = "WalkMassachusetts"
            if name not in seen:
                parts = name.split(None, 1)
                seen[name] = Facilitator(
                    facilitator_id=random_id("fac-"),
                    first_name=parts[0] if parts else None,
                    last_name=parts[1] if len(parts) > 1 else None,
                )
    return list(seen.values())


def to_export(record: WalkAuditDownload) -> WalkAuditExport:
    return WalkAuditExport(
        audit_id=record.audit_id,
        city_or_town=record.city_town,
        audit_date=record.audit_date,
        report_date=record.report_date,
        year=record.year,
        summary=record.summary,
        long_term_rec=record.long_term_recommendations,
        short_term_rec=record.short_term_recommendations,
        area_covered=record.streets_area_covered,
        start_address=record.start_address,
        lat_lon=None,
        themes=normalize_list(record.themes),
        organizations=normalize_list(record.organizations),
        facilitators=normalize_list(
            record.facilitator_author
            and re.sub(r"\bWalkMass\b", "WalkMassachusetts", record.facilitator_author)
        ),
    )


def run():
    with open(JSON_INPUT_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    records = [WalkAuditDownload.model_validate(item) for item in raw]
    exports = [to_export(r) for r in records]

    os.makedirs(os.path.dirname(TSV_OUTPUT_PATH), exist_ok=True)

    fieldnames = list(WalkAuditExport.model_fields.keys())
    with open(TSV_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in exports:
            writer.writerow(row.model_dump())

    print(f"Exported {len(exports)} records to {TSV_OUTPUT_PATH}")

    facilitators = extract_facilitators(exports)
    fac_fieldnames = list(Facilitator.model_fields.keys())
    with open(FACILITATORS_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fac_fieldnames, delimiter="\t")
        writer.writeheader()
        for fac in facilitators:
            writer.writerow(fac.model_dump())

    print(f"Exported {len(facilitators)} facilitators to {FACILITATORS_OUTPUT_PATH}")

    organizations = extract_organizations(exports)
    org_fieldnames = list(Organization.model_fields.keys())
    with open(ORGANIZATIONS_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=org_fieldnames, delimiter="\t")
        writer.writeheader()
        for org in organizations:
            writer.writerow(org.model_dump())

    print(f"Exported {len(organizations)} organizations to {ORGANIZATIONS_OUTPUT_PATH}")

    themes = extract_themes(exports)
    theme_fieldnames = list(Theme.model_fields.keys())
    with open(THEMES_OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=theme_fieldnames, delimiter="\t")
        writer.writeheader()
        for theme in themes:
            writer.writerow(theme.model_dump())

    print(f"Exported {len(themes)} themes to {THEMES_OUTPUT_PATH}")


if __name__ == "__main__":
    run()
