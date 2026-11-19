"""Typed loading of YAML configs so bad values fail early, not mid-experiment."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"


class Company(BaseModel):
    ticker: str
    name: str
    cik: int = Field(gt=0)
    fiscal_years: list[int] = Field(min_length=1)

    @field_validator("ticker")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.upper()


class CompaniesConfig(BaseModel):
    verified: bool = False
    companies: list[Company] = Field(min_length=1)

    @field_validator("companies")
    @classmethod
    def _unique_tickers(cls, v: list[Company]) -> list[Company]:
        tickers = [c.ticker for c in v]
        if len(tickers) != len(set(tickers)):
            raise ValueError("duplicate tickers in companies.yaml")
        return v


def load_companies(path: Path | None = None) -> CompaniesConfig:
    path = path or CONFIG_DIR / "companies.yaml"
    with open(path) as f:
        return CompaniesConfig.model_validate(yaml.safe_load(f))


class ChunkingConfig(BaseModel):
    chunk_tokens: int = Field(600, gt=50)
    max_chunk_tokens: int = Field(800, gt=50)
    chars_per_token: float = Field(4, gt=0)
    overlap_ratio: float = Field(0.12, ge=0, le=0.3)
    cross_section: bool = False
    embedding_model: str = "BAAI/bge-small-en-v1.5"


def load_chunking(path: Path | None = None) -> ChunkingConfig:
    path = path or CONFIG_DIR / "chunking.yaml"
    with open(path) as f:
        return ChunkingConfig.model_validate(yaml.safe_load(f))
