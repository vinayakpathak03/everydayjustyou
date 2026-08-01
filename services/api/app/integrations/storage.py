from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings

GARMENTS_BUCKET = "garment-images"


class StorageClient:
    """Wraps Supabase Storage. Uses the service-role key deliberately here — the
    bucket itself is private with per-user path-scoped Storage RLS policies (see
    docs/architecture/database-schema.md §10), and every path this client writes
    to is prefixed with the *already-authenticated* caller's own user_id (set by
    the router, not by this client), so the app-level authorization already
    happened before any of these calls run. This mirrors how get_admin_db is used
    elsewhere: a narrow, deliberate use of elevated access, not a default.
    """

    def __init__(self, client: Client, bucket: str = GARMENTS_BUCKET) -> None:
        self._client = client
        self._bucket = bucket

    def upload(self, path: str, content: bytes, content_type: str) -> str:
        self._client.storage.from_(self._bucket).upload(
            path, content, {"content-type": content_type, "upsert": "true"}
        )
        return path

    def download(self, path: str) -> bytes:
        return self._client.storage.from_(self._bucket).download(path)

    def signed_url(self, path: str, expires_in: int = 3600) -> str:
        result = self._client.storage.from_(self._bucket).create_signed_url(path, expires_in)
        return result["signedURL"]


@lru_cache
def get_storage_client() -> StorageClient:
    settings = get_settings()
    supabase_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return StorageClient(supabase_client)
