FIXED_ALIASES: dict[str, str] = {
    "text": "text",
    "embedding": "embedding",
    "audio": "audio",
    "image": "image",
    "video": "video",
}

CAPABILITIES = tuple(FIXED_ALIASES.values())
