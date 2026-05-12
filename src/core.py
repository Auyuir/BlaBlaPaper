"""
核心业务逻辑模块 - 组装各模块实现报告生成流程
"""
import json
import os
import copy

from . import config
from . import prompts
from . import llm_client
from . import utils
from . import parser


def build_full_context(text_content, image_paths):
    """
    构建完整的 LLM 上下文消息（包含文本和图片）

    Args:
        text_content: 论文文本内容
        image_paths: 图片文件路径列表

    Returns:
        消息列表，用于 LLM API 调用
    """
    # [Cache Optimization] 统一 System Prompt
    messages = [{"role": "system", "content": config.UNIFIED_SYSTEM_PROMPT}]

    # [Cache Optimization] Marker 1: Text Base
    user_content = [
        {
            "type": "text",
            "text": utils.format_document_content(text_content),
            "cache_control": {"type": "ephemeral"}
        }
    ]

    seen = set()
    for p in image_paths:
        if p in seen:
            continue
        seen.add(p)
        try:
            b64 = utils.encode_image_to_base64(p)
            user_content.append({"type": "text", "text": f"图片文件名: {os.path.basename(p)}"})
            user_content.append({
                "type": "image_url",
                "image_url": {"url": b64, "detail": "auto"}
            })
        except Exception:
            pass

    # [Cache Optimization] Marker 2: Full Context
    if len(user_content) > 1:
        if "cache_control" not in user_content[-1]:
            user_content[-1]["cache_control"] = {"type": "ephemeral"}

    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": "我已阅读文档和图片。"})
    return messages


def extract_tech_points(context_messages, model_name):
    """
    提取核心技术点列表
    [Structured Output] 使用 JSON 模式以确保解析稳定。
    """
    print(f"\n--- [核心技术提取] 正在提取关键技术点列表 (Model: {model_name}) ---")

    # [Structured Output] 提示词中必须包含 'JSON' 关键词
    prompt = """
    任务：提炼本文的**核心技术模块或关键实现细节 (3-6个)**。

    **Output Restriction**:
    The output **MUST** be a valid JSON object. Do not include any markdown formatting or explanatory text outside the JSON.

    JSON Format:
    {
        "points": [
            {
                "name": "技术点名称 (如: Cross-Attention Mechanism)",
                "context": "原文关键描述 (1句话)"
            }
        ]
    }

    请严格按照上述 JSON 格式提取。
    """

    # [Structured Output] 显式开启 json_mode=True
    json_str = llm_client.call_llm_with_cache(
        context_messages,
        prompt,
        config.API_KEY,
        config.API_URL,
        model_name,
        json_mode=True
    )

    if not json_str:
        return []

    try:
        # 尽管 json_mode 保证了 JSON 格式，但为了保险起见，还是移除可能存在的 markdown 标记
        clean = json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data.get("points", [])
    except json.JSONDecodeError as e:
        print(f"[解析错误] JSON 解析失败: {e}\n原始内容: {json_str}")
        return []
    except Exception as e:
        print(f"[未知错误] {e}")
        return []


def analyze_bibliographic_info(info_data):
    """
    从 info_data 中提取并组织论文基本信息

    Args:
        info_data: 包含 metadata 字段的字典

    Returns:
        格式化的论文基本信息文本
    """
    print(f"\n--- 正在提取: 论文基本信息 ---")

    if not info_data or "metadata" not in info_data:
        return "未能提取到论文基本信息。"

    metadata = info_data.get("metadata", {})
    parts = []

    # 1. 作者信息
    authors = metadata.get("authors", [])
    if authors:
        authors_str = ", ".join(authors) if isinstance(authors, list) else str(authors)
        parts.append(f"**作者 (Authors)**: {authors_str}")

    # 2. 发表期刊/会议
    venue = metadata.get("venue", "")
    if venue:
        parts.append(f"**发表期刊/会议 (Journal/Conference)**: {venue}")

    # 3. 发表年份
    year = metadata.get("year", "")
    if year:
        parts.append(f"**发表年份 (Publication Year)**: {year}")

    # 4. 机构信息（如果有）
    affiliations = metadata.get("affiliations", [])
    if affiliations:
        affil_str = ", ".join(affiliations) if isinstance(affiliations, list) else str(affiliations)
        parts.append(f"**研究机构 (Affiliations)**: {affil_str}")

    return "\n\n".join(parts) if parts else "未能提取到论文基本信息。"


def generate_tech_deep_dive(context_messages, innovation_data, valid_filenames, model_name, caption_map):
    """
    基于已提取的点生成技术深挖报告

    Args:
        context_messages: LLM 上下文消息
        innovation_data: 技术点数据列表
        valid_filenames: 有效图片文件名集合
        model_name: 使用的模型名称
        caption_map: 图片说明映射

    Returns:
        技术深挖报告文本
    """
    if not innovation_data:
        return "未能提取到核心技术细节。"

    print(f"\n--- [核心技术细节] 开始深度挖掘 (Model: {model_name}) ---")
    sections = []

    # 0. 概览
    summary_prompt = f"请概括本文的**整体技术架构** (Overall Architecture)。\n{prompts.GLOBAL_STYLE_PROMPT}"
    summary = llm_client.call_llm_with_cache(
        context_messages,
        summary_prompt,
        config.API_KEY,
        config.API_URL,
        model_name
    )
    sections.append(f"### 0. 技术架构概览\n\n{utils.correct_image_references(summary, valid_filenames, caption_map)}\n")

    # 1. 逐点分析
    for idx, item in enumerate(innovation_data, 1):
        name = item.get("name", "未知点")
        ctx = item.get("context", "")
        print(f"   -> Tech Deep Dive: {name} ...")

        prompt = f"""
        任务：深度剖析技术细节 **"{name}"**。
        参考线索：{ctx}
        {prompts.GLOBAL_STYLE_PROMPT}
        要求：
        1. 解释实现原理、算法流程、参数设置。
        2. 说明输入输出关系及在整体中的作用。
        """
        detail = llm_client.call_llm_with_cache(
            context_messages,
            prompt,
            config.API_KEY,
            config.API_URL,
            model_name
        )
        sections.append(f"### {idx}. {name}\n\n{utils.correct_image_references(detail, valid_filenames, caption_map)}\n")

    return "\n".join(sections)


def analyze_eli5_innovations(context_messages, innovation_data, valid_filenames, model_name, caption_map):
    """
    [新增] 生成通俗易懂的解释报告

    Args:
        context_messages: LLM 上下文消息
        innovation_data: 技术点数据列表
        valid_filenames: 有效图片文件名集合
        model_name: 使用的模型名称
        caption_map: 图片说明映射

    Returns:
        通俗解释报告文本
    """
    print(f"\n--- [通俗解释] 开始生成通俗解释 (Model: {model_name}) ---")

    sections = []

    # 0. 整体创新的通俗解释
    print("   -> 通俗解释: 整体创新点 ...")
    overall_prompt = f"""
    {prompts.ELI5_ROLE_PROMPT}

    任务：请对这篇论文的**核心创新点/整体贡献**进行"直觉性解读"。
    不要陷入细节，而是解释整篇论文主要想解决什么大问题，用了什么巧妙的思路。

    {prompts.GLOBAL_STYLE_PROMPT}
    """
    overall_res = llm_client.call_llm_with_cache(
        context_messages,
        overall_prompt,
        config.API_KEY,
        config.API_URL,
        model_name
    )
    sections.append(f"### 0. 整体创新点通俗解读\n\n{utils.correct_image_references(overall_res, valid_filenames, caption_map)}\n")

    # 1. 逐个技术点的通俗解释
    for idx, item in enumerate(innovation_data, 1):
        name = item.get("name", "未知点")
        ctx = item.get("context", "")
        print(f"   -> 通俗解释: {name} ...")

        prompt = f"""
        {prompts.ELI5_ROLE_PROMPT}

        任务：请对技术点 **"{name}"** 进行"直觉性解读"。
        参考线索：{ctx}
        {prompts.GLOBAL_STYLE_PROMPT}
        """

        res = llm_client.call_llm_with_cache(
            context_messages,
            prompt,
            config.API_KEY,
            config.API_URL,
            model_name
        )
        sections.append(f"### {idx}. {name}\n\n{utils.correct_image_references(res, valid_filenames, caption_map)}\n")

    return "\n".join(sections)


def generate_info_json_data(context_messages, model_name, additional_context=None):
    """
    生成 info.json 所需的元数据和描述信息

    Args:
        context_messages: 基础上下文消息列表
        model_name: 使用的模型名称
        additional_context: 可选的追加上下文文本，将被添加为新的用户消息

    Returns:
        包含 metadata 和 description 的字典，失败时返回 None
    """
    print(f"\n--- [信息提取] 正在生成元数据和描述 (Model: {model_name}) ---")

    # 如果有追加上下文，添加到消息列表中
    enhanced_messages = copy.deepcopy(context_messages)
    if additional_context:
        enhanced_messages.append({"role": "user", "content": additional_context})

    json_str = llm_client.call_llm_with_cache(
        enhanced_messages,
        prompts.INFO_JSON_PROMPT,
        config.API_KEY,
        config.API_URL,
        model_name,
        json_mode=True
    )

    if not json_str:
        return None

    try:
        # 清理可能的 markdown 标记
        clean = json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data
    except json.JSONDecodeError as e:
        print(f"[解析错误] JSON 解析失败: {e}\n原始内容: {json_str}")
        return None
    except Exception as e:
        print(f"[未知错误] {e}")
        return None


def analyze_section(title, task_prompt, context_messages, valid_filenames, model_name, caption_map):
    """
    分析论文的特定章节

    Args:
        title: 章节标题（用于日志输出）
        task_prompt: 任务提示词
        context_messages: LLM 上下文消息
        valid_filenames: 有效图片文件名集合
        model_name: 使用的模型名称
        caption_map: 图片说明映射

    Returns:
        分析结果文本
    """
    print(f"--- 正在分析: {title} ---")
    full_prompt = f"{task_prompt}\n{prompts.GLOBAL_STYLE_PROMPT}"
    res = llm_client.call_llm_with_cache(
        context_messages,
        full_prompt,
        config.API_KEY,
        config.API_URL,
        model_name
    )
    return utils.correct_image_references(res, valid_filenames, caption_map)


def analyze_single_figure_isolated(image_path, full_text, valid_filenames, model_name, caption=None):
    """
    单独分析单个图片

    Args:
        image_path: 图片文件路径
        full_text: 完整论文文本
        valid_filenames: 有效图片文件名集合
        model_name: 使用的模型名称
        caption: 可选的图片说明

    Returns:
        图片分析结果文本，失败时返回 None
    """
    filename = os.path.basename(image_path)
    print(f"   -> 单图分析: {filename} ...")

    prompt = f"""
    任务：详细分析图片 {filename}。
    图片说明：{caption or ''}
    {prompts.FIGURE_STYLE_PROMPT}
    """

    msgs = [{"role": "system", "content": config.UNIFIED_SYSTEM_PROMPT}]

    content = [
        {
            "type": "text",
            "text": utils.format_document_content(full_text),
            "cache_control": {"type": "ephemeral"}
        },
        {"type": "text", "text": f"Target Image: {filename}"},
        {
            "type": "image_url",
            "image_url": {"url": utils.encode_image_to_base64(image_path), "detail": "high"}
        },
        {"type": "text", "text": prompt}
    ]
    msgs.append({"role": "user", "content": content})

    try:
        raw = llm_client.call_llm_with_cache(
            msgs,
            [],
            config.API_KEY,
            config.API_URL,
            model_name
        )
        return utils.correct_image_references(raw, valid_filenames, None)
    except Exception as e:
        print(f"图表分析失败: {e}")
        return None
