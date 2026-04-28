from app.services.model_classifier import classify_model


def test_classifies_text_model() -> None:
    result = classify_model("gpt-4o")
    assert result.capability == "text"
    assert result.family == "gpt"


def test_classifies_embedding_model() -> None:
    result = classify_model("text-embedding-3-large")
    assert result.capability == "embedding"


def test_classifies_audio_model() -> None:
    result = classify_model("whisper-1")
    assert result.capability == "audio"


def test_classifies_image_model() -> None:
    result = classify_model("gpt-image-1")
    assert result.capability == "image"


def test_classifies_video_model() -> None:
    result = classify_model("sora-1")
    assert result.capability == "video"


def test_stronger_model_gets_lower_priority() -> None:
    assert classify_model("gpt-5").default_priority < classify_model("gpt-4o-mini").default_priority
