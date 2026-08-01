import { createClient } from "@/lib/supabase/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(`API error ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

/** Thin fetch wrapper that attaches the current Supabase session's JWT as a
 * Bearer token — this is the token app/main.py's get_current_user verifies and
 * the one Postgres RLS ultimately keys off of. See docs/architecture/api-architecture.md. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  const res = await fetch(`${API_BASE_URL}/api/v1${path}`, { ...init, headers });

  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** multipart/form-data upload — separate from apiFetch because that helper
 * unconditionally sets Content-Type: application/json, which would break a
 * FormData body (the browser needs to set its own multipart boundary). */
export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers = new Headers();
  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  const res = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export type GarmentStatusEvent = { image_id: string; garment_id: string; status: string };

/** Consumes GET /garments/events via fetch+ReadableStream rather than the native
 * EventSource API — EventSource can't send an Authorization header, and query-
 * param tokens would leak into server logs/proxies. Returns an abort function. */
export function subscribeToGarmentEvents(onEvent: (e: GarmentStatusEvent) => void): () => void {
  const controller = new AbortController();

  (async () => {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) return;

    let res: Response;
    try {
      res = await fetch(`${API_BASE_URL}/api/v1/garments/events`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        signal: controller.signal,
      });
    } catch {
      return; // aborted before the connection opened
    }
    const reader = res.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const dataLine = frame.split("\n").find((line) => line.startsWith("data: "));
        if (!dataLine) continue;
        try {
          onEvent(JSON.parse(dataLine.slice("data: ".length)) as GarmentStatusEvent);
        } catch {
          // malformed frame — skip rather than crash the stream reader
        }
      }
    }
  })();

  return () => controller.abort();
}

export type ChatStreamEvent =
  | { event: "conversation"; data: { conversation_id: string } }
  | { event: "token"; data: { text: string } }
  | { event: "outfit_cards"; data: { outfits: unknown[] } }
  | { event: "done"; data: Record<string, never> };

/** POSTs a chat turn and consumes the SSE reply — same fetch+ReadableStream
 * approach as subscribeToGarmentEvents, for the same reason (Authorization
 * header). One-shot rather than a subscription: a chat turn has a clear end
 * (the `done` event), unlike the open-ended garment-processing stream. */
export async function postChatMessage(
  body: { conversation_id: string | null; message: string },
  onEvent: (e: ChatStreamEvent) => void
): Promise<void> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) throw new ApiError(401, null);

  const res = await fetch(`${API_BASE_URL}/api/v1/stylist/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) throw new ApiError(res.status, null);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const lines = frame.split("\n");
      const eventLine = lines.find((l) => l.startsWith("event: "));
      const dataLine = lines.find((l) => l.startsWith("data: "));
      if (!eventLine || !dataLine) continue;
      const eventName = eventLine.slice("event: ".length).trim();
      try {
        const data = JSON.parse(dataLine.slice("data: ".length));
        onEvent({ event: eventName, data } as ChatStreamEvent);
      } catch {
        // malformed frame — skip
      }
    }
  }
}
