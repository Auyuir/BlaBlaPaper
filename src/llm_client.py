"""
LLM API 客户端模块 - 封装 OpenAI-compatible API 调用
"""
import requests
import time
import json
import copy

from . import config
from .utils import clean_llm_output


def _strip_cache_control(value):
    if isinstance(value, dict):
        return {
            key: _strip_cache_control(val)
            for key, val in value.items()
            if key != "cache_control"
        }
    if isinstance(value, list):
        return [_strip_cache_control(item) for item in value]
    return value


def _content_to_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                chunks.append(part.get("text", ""))
        return "\n".join(chunk for chunk in chunks if chunk)
    return str(content) if content is not None else ""


def _to_responses_content(content):
    if isinstance(content, str):
        return [{"type": "input_text", "text": content}]

    if not isinstance(content, list):
        return [{"type": "input_text", "text": str(content)}] if content is not None else []

    items = []
    for part in content:
        if not isinstance(part, dict):
            continue

        part_type = part.get("type")
        if part_type == "text":
            text = part.get("text", "")
            if text:
                items.append({"type": "input_text", "text": text})
        elif part_type == "image_url":
            image = part.get("image_url", {})
            image_url = image.get("url") if isinstance(image, dict) else image
            if image_url:
                item = {"type": "input_image", "image_url": image_url}
                if isinstance(image, dict) and image.get("detail"):
                    item["detail"] = image["detail"]
                items.append(item)
        elif part_type in {"input_text", "input_image"}:
            items.append(_strip_cache_control(part))
        elif "text" in part:
            text = str(part.get("text", ""))
            if text:
                items.append({"type": "input_text", "text": text})

    return items


def _build_responses_payload(messages, model_name, json_mode):
    instructions = []
    input_items = []

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        if role == "system":
            text = _content_to_text(content)
            if text:
                instructions.append(text)
            continue

        if role == "assistant":
            continue

        response_role = role if role in {"user", "developer"} else "user"
        response_content = _to_responses_content(content)
        if response_content:
            input_items.append({"role": response_role, "content": response_content})

    payload = {
        "model": model_name,
        "input": input_items,
        "temperature": 0.3,
        "store": False,
    }
    if instructions:
        payload["instructions"] = "\n\n".join(instructions)
    if json_mode:
        payload["text"] = {"format": {"type": "json_object"}}
    return payload


def _build_chat_payload(messages, model_name, json_mode):
    payload = {
        "model": model_name,
        "messages": _strip_cache_control(messages),
        "temperature": 0.3,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def _extract_responses_text(data):
    if isinstance(data.get("output_text"), str):
        return data["output_text"]

    chunks = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            for part in item.get("content", []):
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
        elif item.get("type") in {"output_text", "text"} and isinstance(item.get("text"), str):
            chunks.append(item["text"])

    return "".join(chunks).strip() if chunks else None


def _extract_chat_text(data):
    content = data["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
        return "".join(chunks).strip()
    return str(content)


def call_llm_with_cache(messages, new_query, api_key, api_url, model_name, json_mode=False):
    """
    调用 LLM API，支持 Responses API 与 OpenAI-compatible Chat Completions。

    Args:
        messages: 基础消息列表（包含上下文）
        new_query: 新的查询文本（将添加到消息末尾）
        api_key: API 密钥
        api_url: API 端点 URL
        model_name: 使用的模型名称
        json_mode: 是否强制 JSON 结构化输出（默认 False）

    Returns:
        LLM 响应文本（json_mode=True 时返回原始 JSON，否则返回清理后的文本）
        失败时返回 None
    """
    current_messages = copy.deepcopy(messages)

    if new_query:
        current_messages.append({"role": "user", "content": new_query})

    use_responses = config.WIRE_API == "responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(5):
        try:
            if use_responses:
                payload = _build_responses_payload(current_messages, model_name, json_mode)
            else:
                payload = _build_chat_payload(current_messages, model_name, json_mode)

            resp = requests.post(api_url, json=payload, headers=headers, timeout=600)

            if resp.status_code == 429:
                wait_time = 2 * (2 ** attempt)
                print(f"[速率限制] 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue

            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict) and data.get("error"):
                print(f"API Error: {data['error']}")
                return None

            content = _extract_responses_text(data) if use_responses else _extract_chat_text(data)
            return content if json_mode else clean_llm_output(content)

        except requests.exceptions.RequestException as e:
            print(f"API Error (attempt {attempt + 1}/5): {e}")
            if attempt < 4:
                time.sleep(2)

        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            print(f"Unexpected API response (attempt {attempt + 1}/5): {e}")
            if attempt < 4:
                time.sleep(2)

        except Exception as e:
            print(f"Unexpected Error: {e}")
            if attempt < 4:
                time.sleep(2)

    return None
