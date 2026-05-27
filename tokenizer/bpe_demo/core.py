from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TokenPiece:
    token_id: int
    text: str


@dataclass(frozen=True)
class TokenizationResult:
    model: str
    source: str
    language: str
    text: str
    count: int
    pieces: list[TokenPiece] | None
    note: str = ""

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def byte_count(self) -> int:
        return len(self.text.encode("utf-8"))

    @property
    def chars_per_token(self) -> float:
        return self.char_count / self.count if self.count else 0.0

    @property
    def compression_ratio(self) -> float:
        """Characters represented by each token; higher means denser encoding."""
        return self.chars_per_token

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["char_count"] = self.char_count
        value["byte_count"] = self.byte_count
        value["chars_per_token"] = round(self.chars_per_token, 4)
        value["compression_ratio_chars_per_token"] = round(self.compression_ratio, 4)
        return value


class TokenizerAdapter(Protocol):
    name: str
    source: str

    def tokenize(self, text: str, language: str) -> TokenizationResult: ...


def sample_path(language: str) -> Path:
    suffix = {"English": "en", "中文": "zh"}[language]
    return Path(__file__).parent / "samples" / f"harbor_clock.{suffix}.txt"


def read_sample(language: str, override: Path | None = None) -> str:
    return (override or sample_path(language)).read_text(encoding="utf-8").strip()
