from dataclasses import dataclass


@dataclass(frozen=True)
class ModelClassification:
    capability: str
    family: str
    default_priority: int


def classify_model(model_name: str) -> ModelClassification:
    normalized = model_name.lower()
    capability = _classify_capability(normalized)
    family = _classify_family(normalized)
    priority = _default_priority(normalized, capability)
    return ModelClassification(capability=capability, family=family, default_priority=priority)


def _classify_capability(model: str) -> str:
    if any(token in model for token in ("embedding", "embed", "bge", "gte-", "m3e")):
        return "embedding"
    if any(token in model for token in ("whisper", "tts", "speech", "transcribe", "audio", "asr")):
        return "audio"
    if any(token in model for token in ("sora", "video", "veo", "kling", "wan", "hailuo", "runway")):
        return "video"
    if any(token in model for token in ("dall-e", "gpt-image", "imagen", "flux", "midjourney", "stable-diffusion", "sdxl")):
        return "image"
    return "text"


def _classify_family(model: str) -> str:
    family_tokens = (
        "gpt",
        "claude",
        "gemini",
        "deepseek",
        "qwen",
        "llama",
        "mistral",
        "glm",
        "ernie",
        "yi",
        "grok",
        "o1",
        "o3",
        "o4",
    )
    for token in family_tokens:
        if token in model:
            return token
    return "unknown"


def _default_priority(model: str, capability: str) -> int:
    capability_base = {
        "text": 1000,
        "embedding": 2000,
        "audio": 3000,
        "image": 4000,
        "video": 5000,
    }[capability]

    score = capability_base
    strength_patterns = (
        ("gpt-5", -500),
        ("claude-4", -450),
        ("opus", -420),
        ("gemini-2.5-pro", -400),
        ("o3", -380),
        ("o4", -360),
        ("gpt-4.1", -340),
        ("sonnet", -330),
        ("gpt-4o", -300),
        ("deepseek-r1", -280),
        ("qwen-max", -260),
        ("pro", -180),
        ("turbo", -120),
        ("mini", 150),
        ("flash", 180),
        ("lite", 220),
        ("8b", 260),
        ("7b", 280),
    )
    for token, delta in strength_patterns:
        if token in model:
            score += delta
    return max(score, 1)
