"""
配置模块 - 从项目 .env 和环境变量中加载配置
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(dotenv_path=None):
        """轻量级 .env 回退实现，避免运行时必须安装 python-dotenv。"""
        path = Path(dotenv_path) if dotenv_path is not None else Path.cwd() / ".env"
        if not path.exists():
            return False

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return True


# 加载项目根目录的 .env。这样即使从其他目录执行 main.py，也能读到配置。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv()


def _env(*names, default=""):
    """按顺序读取环境变量，支持小写 .env 字段和常见大写别名。"""
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _normalize_wire_api(value):
    normalized = value.strip().replace("-", "_").lower()
    if normalized in {"response", "responses_api"}:
        return "responses"
    if normalized in {"chat", "chat_completions", "chat/completions"}:
        return "chat_completions"
    return normalized or "responses"


def _build_api_url(base_url, wire_api):
    base = base_url.rstrip("/")
    if base.endswith("/responses") or base.endswith("/chat/completions"):
        return base
    if wire_api == "responses":
        return f"{base}/responses"
    return f"{base}/chat/completions"


# ============================================================================
# LLM API 配置
# ============================================================================

MODEL_PROVIDER = _env("model_provider", "MODEL_PROVIDER", default="OpenAI")
MODEL_NAME_TEXT = _env("model", "MODEL", "OPENAI_MODEL", default="gpt-5.5")
MODEL_NAME_IMAGE = _env("model_image", "MODEL_NAME_IMAGE", default=MODEL_NAME_TEXT)
API_BASE_URL = _env(
    "base_url",
    "BASE_URL",
    "OPENAI_BASE_URL",
    default="https://api.openai.com/v1",
)
WIRE_API = _normalize_wire_api(
    _env("wire_api", "WIRE_API", "OPENAI_WIRE_API", default="responses")
)
API_URL = _env("api_url", "API_URL", "OPENAI_API_URL") or _build_api_url(
    API_BASE_URL,
    WIRE_API,
)
API_KEY = _env("OPENAI_API_KEY", "openai_api_key")
MODEL_REASONING_EFFORT = _env("MODEL_REASONING_EFFORT", default="medium")

if not API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Please set it in the project .env file "
        "or in your shell environment."
    )

# ============================================================================
# 系统提示词
# ============================================================================

UNIFIED_SYSTEM_PROMPT = (
    "你是一个专业的计算机科学与人工智能论文分析专家。"
    "请根据提供的论文内容和图表进行深入分析。"
)

# ============================================================================
# MinerU PDF 解析服务配置
# ============================================================================

MINERU_API_TOKEN = _env("MINERU_API_TOKEN")

if not MINERU_API_TOKEN:
    print("[警告] MINERU_API_TOKEN 未配置，PDF 解析功能将不可用")

MINERU_BASE_URL = "https://mineru.net/api/v4"
MINERU_MODEL_VERSION = "pipeline"  # 可选: "pipeline" 或 "vlm"
