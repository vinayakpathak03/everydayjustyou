import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres")
os.environ.setdefault(
    "DATABASE_URL_ADMIN", "postgresql+asyncpg://postgres:postgres@localhost:54322/postgres"
)
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
