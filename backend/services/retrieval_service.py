from pathlib import Path
import re
from typing import List, Dict, Any

from backend.models import Job
from backend.utils.path_utils import resolve_project_path


DOMAIN_TERMS = [
    "注册图片",
    "注册比例",
    "稀疏",
    "3D 点",
    "3D点",
    "COLMAP",
    "模糊",
    "风险",
    "建议",
    "3DGS",
    "报告",
    "相机轨迹",
    "质量",
    "评分",
    "错误",
    "日志",
    "READY",
    "NOT_READY",
    "READY_WITH_WARNINGS",
    "sparse",
    "points3D",
    "camera",
    "trajectory",
    "reconstruction",
    "readiness",
]


def read_text_if_exists(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""

    return path.read_text(encoding="utf-8", errors="ignore")


def split_markdown_sections(source: str, content: str) -> List[Dict[str, Any]]:
    """
    按 Markdown 标题切分报告。

    每个 section 包含：
    - source: 来源文件类型
    - title: 标题
    - content: 标题下正文
    """
    sections = []

    current_title = "document_start"
    current_lines = []

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("#"):
            if current_lines:
                sections.append({
                    "source": source,
                    "title": current_title,
                    "content": "\n".join(current_lines).strip()
                })

            current_title = stripped.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "source": source,
            "title": current_title,
            "content": "\n".join(current_lines).strip()
        })

    return [
        section for section in sections
        if section["content"] or section["title"]
    ]


def build_query_terms(question: str) -> List[str]:
    """
    简单关键词提取。
    v1 版本先不用向量数据库，使用英文 token + 领域关键词匹配。
    """
    terms = set()

    lower_question = question.lower()

    english_tokens = re.findall(r"[a-zA-Z0-9_]+", lower_question)
    for token in english_tokens:
        if len(token) >= 2:
            terms.add(token)

    for term in DOMAIN_TERMS:
        if term.lower() in lower_question or term in question:
            terms.add(term)

    # 如果用户问题很短，但没有命中领域词，保留一些常用触发词
    if not terms:
        for fallback in ["质量", "风险", "建议", "报告", "COLMAP", "3DGS"]:
            if fallback in question:
                terms.add(fallback)

    return list(terms)


def score_section(section: Dict[str, Any], query_terms: List[str]) -> float:
    title = section["title"]
    content = section["content"]

    haystack = f"{title}\n{content}".lower()
    title_lower = title.lower()

    score = 0.0

    for term in query_terms:
        term_lower = term.lower()

        count = haystack.count(term_lower)

        if count > 0:
            score += count * max(len(term_lower), 1)

        if term_lower in title_lower:
            score += 10

    # 一些重要 section 的轻微加权
    important_titles = [
        "总体结论",
        "重建质量诊断",
        "风险提示",
        "建议",
        "COLMAP 重建结果",
        "COLMAP 模型分析结果",
        "数据准备检查结果",
    ]

    for important_title in important_titles:
        if important_title in title:
            score += 2

    return score


def get_report_sections(job: Job) -> List[Dict[str, Any]]:
    output_path = resolve_project_path(job.output_path)

    report_files = [
        ("reconstruction_report", output_path / "reconstruction_report.md"),
        ("readiness_report", output_path / "training_data_readiness_report.md"),
    ]

    all_sections = []

    for source, path in report_files:
        content = read_text_if_exists(path)

        if not content:
            continue

        sections = split_markdown_sections(source, content)
        all_sections.extend(sections)

    return all_sections


def search_job_reports(
    job: Job,
    question: str,
    top_k: int = 5,
    max_section_chars: int = 1500
) -> List[Dict[str, Any]]:
    """
    从任务报告中检索与用户问题最相关的 section。
    """
    sections = get_report_sections(job)
    query_terms = build_query_terms(question)

    scored_sections = []

    for section in sections:
        score = score_section(section, query_terms)

        scored_sections.append({
            "source": section["source"],
            "title": section["title"],
            "score": score,
            "content": section["content"][:max_section_chars]
        })

    scored_sections = sorted(
        scored_sections,
        key=lambda x: x["score"],
        reverse=True
    )

    positive_sections = [
        section for section in scored_sections
        if section["score"] > 0
    ]

    if positive_sections:
        return positive_sections[:top_k]

    # 如果没有命中关键词，就返回前几个重要 section，避免空上下文
    return scored_sections[:top_k]