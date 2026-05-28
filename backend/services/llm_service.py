import os
import json
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI


def build_agent_prompt(
    question: str,
    diagnose_result: Dict[str, Any],
    rule_answer: str,
    text_context: Optional[Dict[str, str]] = None
) -> str:
    if text_context is None:
        text_context = {}

    context = {
        "job_id": diagnose_result.get("job_id"),
        "job_status": diagnose_result.get("job_status"),
        "quality": diagnose_result.get("quality"),
        "main_problems": diagnose_result.get("main_problems"),
        "suggestions": diagnose_result.get("suggestions"),
        "next_actions": diagnose_result.get("next_actions"),
        "evidence": diagnose_result.get("evidence"),
        "rule_answer": rule_answer,
        "text_context": text_context
    }

    return f"""
你是一个三维重建数据处理后端系统中的智能诊断助手。

回答要求：
1. 必须基于系统提供的结构化证据和报告内容回答；
2. 结构化 evidence 是主要判断依据，报告和日志内容作为补充；
3. 不要编造不存在的文件、指标、按钮、页面、命令或结果；
4. 如果系统没有提供某个操作入口，不要说“点击继续”“点击按钮”等 UI 操作；
5. 可以建议用户调用已有 API，例如 GET /api/v1/jobs/{{job_id}}/report；
6. 可以建议用户运行已有命令，例如 run_colmap.bat；
7. 如果证据不足，要明确说明；
8. 回答要适合初学者理解；
9. 优先给出可执行的下一步建议；
10. 如果报告内容和结构化 evidence 冲突，优先相信结构化 evidence，并指出可能存在报告解析或统计问题。

用户问题：
{question}

系统诊断结果 JSON：
{json.dumps(context, ensure_ascii=False, indent=2)}

请用中文回答。
"""


def generate_llm_answer(
    question: str,
    diagnose_result: Dict[str, Any],
    rule_answer: str,
    text_context: Optional[Dict[str, str]] = None
):
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    provider = os.getenv("LLM_PROVIDER", "deepseek")

    if not api_key:
        return None, "LLM_API_KEY is not set.", provider, model

    try:
        if base_url:
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
        else:
            client = OpenAI(api_key=api_key)

        prompt = build_agent_prompt(
            question=question,
            diagnose_result=diagnose_result,
            rule_answer=rule_answer,
            text_context=text_context
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个严谨的三维重建数据诊断助手，必须基于给定证据回答。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=False
        )

        answer = response.choices[0].message.content

        return answer, None, provider, model

    except Exception as e:
        return None, str(e), provider, model

def get_llm_status():
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    provider = os.getenv("LLM_PROVIDER", "deepseek")

    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key_configured": api_key is not None and len(api_key) > 0
    }