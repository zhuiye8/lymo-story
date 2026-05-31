from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    litellm_model: str = "gpt-4o"
    litellm_api_key: str = ""
    litellm_api_base: str | None = None

    # Storage paths
    sqlite_path: str = "data/story.db"
    checkpoint_db_path: str = "data/checkpoints.db"
    data_dir: str = "data/stories"
    chroma_path: str = "data/chroma"

    # 语义记忆 embedding。默认走 chromadb 内置 all-MiniLM（CPU，英文为主）。
    # 中文小说建议 ollama + Qwen3-Embedding（本地 GPU，中文 SOTA）：
    #   STORY_EMBED_PROVIDER=ollama  STORY_EMBED_MODEL=qwen3-embedding:4b
    embed_provider: str = "default"            # default | ollama
    embed_model: str = "qwen3-embedding:4b"    # ollama tag（embed_provider=ollama 时生效）
    ollama_base_url: str = "http://localhost:11434"

    # Generation parameters
    max_consistency_retries: int = 2
    default_chapter_word_count: int = 3000

    # Consistency thresholds (0-100 for chapter, 0.0-1.0 for scene)
    # Lower = more lenient (fewer rewrites). Raise early in a story, lower when long context degrades scores.
    chapter_consistency_threshold: int = 70        # score out of 100; below this → fail
    chapter_max_critical: int = 0                  # max critical issues allowed (0 = none)
    chapter_max_warnings: int = 3                  # max warning issues before fail
    scene_consistency_threshold: float = 0.7       # score 0-1; below this → scene retry

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_prefix": "STORY_"}
