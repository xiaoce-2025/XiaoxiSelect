from __future__ import annotations


class MessageClassifier:
    """Classify input text into a module category.

    Current implementation is a placeholder. You can replace this with
    keyword rules, ML model inference, or external API classification later.
    """

    def classify(self, text: str) -> str:
        content = text.strip()
        if not content:
            return "empty"

        if "天气" in content:
            return "weather"

        if "严小希" in content:
            return "yxx"

        return "demo"
