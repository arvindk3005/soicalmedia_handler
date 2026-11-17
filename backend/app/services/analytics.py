from collections import Counter
from dataclasses import asdict, dataclass
import re

POSITIVE = {"great", "love", "excited", "win", "growth", "thanks", "launch", "learned"}
NEGATIVE = {"hate", "bad", "failed", "blocked", "issue", "problem", "delay"}
STOP = {"this", "that", "with", "from", "have", "your", "about", "will", "just", "into"}

@dataclass
class Analysis:
    sentiment: str; score: int; summary: str; hashtags: list[str]; recommendation: str; suggested_hook: str; provider: str

def analyze_demo(content: str, platform: str) -> dict:
    words = re.findall(r"[a-zA-Z]{3,}", content.lower())
    score = sum(w in POSITIVE for w in words) - sum(w in NEGATIVE for w in words)
    sentiment = "positive" if score > 0 else "negative" if score < 0 else "neutral"
    topics = [word for word, _ in Counter(w for w in words if w not in STOP).most_common(3)] or ["insights"]
    tags = ["#" + topic.title().replace(" ", "") for topic in topics]
    recommendation = "Add a specific outcome or metric to make the value concrete." if not re.search(r"\d", content) else "Keep the metric near the opening and finish with one focused question."
    hook = f"What I learned about {topics[0]} this week" if platform == "linkedin" else f"A practical {topics[0]} lesson"
    return asdict(Analysis(sentiment, score, f"The post reads as {sentiment} and centers on {', '.join(topics)}.", tags, recommendation, hook, "demo"))
