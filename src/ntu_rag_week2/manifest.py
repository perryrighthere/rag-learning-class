from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

from .models import AuditIssue, DomainBlueprint, ManifestAudit, SourceRecord


def load_domain_blueprint(path: Path) -> DomainBlueprint:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return DomainBlueprint(**raw)


def load_source_records(path: Path) -> list[SourceRecord]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    return [SourceRecord(**item) for item in raw_items]


def resolve_source_path(scope_dir: Path, record: SourceRecord) -> Path:
    source_path = Path(record.path)
    if source_path.is_absolute():
        return source_path
    return scope_dir / source_path


class CorpusManifestAuditor:
    def __init__(self, blueprint: DomainBlueprint, scope_dir: Path) -> None:
        self.blueprint = blueprint
        self.scope_dir = scope_dir
        self.preferred_formats = {item.lower() for item in blueprint.preferred_formats}

    def audit(self, records: list[SourceRecord]) -> ManifestAudit:
        issues: list[AuditIssue] = []
        total_sources = len(records)
        if total_sources < self.blueprint.minimum_source_count:
            issues.append(
                AuditIssue(
                    severity="error",
                    message=(
                        f"语料数量不足：当前 {total_sources} 篇，"
                        f"低于最低要求 {self.blueprint.minimum_source_count}。"
                    ),
                )
            )
        if total_sources > self.blueprint.maximum_source_count:
            issues.append(
                AuditIssue(
                    severity="warning",
                    message=(
                        f"语料数量偏多：当前 {total_sources} 篇，"
                        f"超过建议上限 {self.blueprint.maximum_source_count}。"
                    ),
                )
            )

        seen_ids: set[str] = set()
        seen_paths: set[str] = set()
        format_counts: Counter[str] = Counter()
        authority_counts: Counter[str] = Counter()
        parsed_dates: list[date] = []

        for record in records:
            if record.source_id in seen_ids:
                issues.append(AuditIssue("error", f"存在重复 source_id：{record.source_id}。"))
            seen_ids.add(record.source_id)

            if record.path in seen_paths:
                issues.append(AuditIssue("warning", f"存在重复 path：{record.path}。"))
            seen_paths.add(record.path)

            format_name = record.format.lower()
            authority_name = record.authority_type.lower()
            format_counts[format_name] += 1
            authority_counts[authority_name] += 1

            if format_name not in self.preferred_formats:
                issues.append(
                    AuditIssue(
                        "warning",
                        f"{record.source_id} 使用了未列入本周首选范围的格式：{record.format}。",
                    )
                )

            path = resolve_source_path(self.scope_dir, record)
            if not path.exists():
                issues.append(
                    AuditIssue("error", f"{record.source_id} 缺少本地样例文件：{path}.")
                )
            elif path.suffix.lstrip(".").lower() != format_name:
                issues.append(
                    AuditIssue(
                        "warning",
                        f"{record.source_id} 的格式声明为 {record.format}，但文件后缀是 {path.suffix}。",
                    )
                )

            try:
                parsed_dates.append(date.fromisoformat(record.published_at))
            except ValueError:
                issues.append(
                    AuditIssue(
                        "error",
                        f"{record.source_id} 的 published_at 不是 ISO 日期：{record.published_at}。",
                    )
                )

            if len(record.summary.strip()) < 12:
                issues.append(
                    AuditIssue(
                        "warning",
                        f"{record.source_id} 的 summary 过短，后续不利于老师快速验收。",
                    )
                )
            if len(record.reason_to_include.strip()) < 12:
                issues.append(
                    AuditIssue(
                        "warning",
                        f"{record.source_id} 的 reason_to_include 过短，领域边界不够清楚。",
                    )
                )

        if len(format_counts) < 2:
            issues.append(
                AuditIssue("warning", "语料格式过于单一，学生可能误以为后续只需要处理一种来源。")
            )
        if len(authority_counts) < 2:
            issues.append(
                AuditIssue("warning", "语料权威类型过于单一，后续问题覆盖面可能不足。")
            )

        earliest_date = min(parsed_dates).isoformat() if parsed_dates else ""
        latest_date = max(parsed_dates).isoformat() if parsed_dates else ""

        return ManifestAudit(
            total_sources=total_sources,
            format_counts=dict(sorted(format_counts.items())),
            authority_counts=dict(sorted(authority_counts.items())),
            earliest_date=earliest_date,
            latest_date=latest_date,
            issues=issues,
        )
