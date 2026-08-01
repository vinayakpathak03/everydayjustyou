"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { postChatMessage } from "@/lib/api";
import { Chip } from "@/components/ui/Chip";

type OutfitCard = {
  id: string;
  score: number;
  rationale: string | null;
  items: { slot: string; garment_id: string; image_url: string | null }[];
};
type ChatBubble = {
  role: "user" | "assistant";
  content: string;
  outfitCards?: OutfitCard[];
};

const SUGGESTED_PROMPTS = [
  "What should I wear for dinner?",
  "I have a job interview",
  "Show me pink outfits",
  "I wore this yesterday",
];

export default function StylistPage() {
  const [messages, setMessages] = useState<ChatBubble[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const conversationIdRef = useRef<string | null>(null);

  async function send(text: string) {
    if (!text.trim() || sending) return;
    setSending(true);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);

    try {
      await postChatMessage(
        { conversation_id: conversationIdRef.current, message: text },
        (evt) => {
          if (evt.event === "conversation") {
            conversationIdRef.current = evt.data.conversation_id;
          } else if (evt.event === "token") {
            setMessages((prev) => {
              const next = [...prev];
              next[next.length - 1] = {
                ...next[next.length - 1],
                content: next[next.length - 1].content + evt.data.text,
              };
              return next;
            });
          } else if (evt.event === "outfit_cards") {
            setMessages((prev) => {
              const next = [...prev];
              next[next.length - 1] = {
                ...next[next.length - 1],
                outfitCards: evt.data.outfits as OutfitCard[],
              };
              return next;
            });
          }
        }
      );
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: "Couldn't reach the Stylist just now — try again in a moment.",
        };
        return next;
      });
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col px-6 pt-8">
      <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Stylist</p>
      <h1 className="mb-4 font-display text-2xl">Ask Muse</h1>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto pb-4">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_PROMPTS.map((p) => (
              <Chip key={p} onClick={() => send(p)}>
                {p}
              </Chip>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
              m.role === "user"
                ? "self-end bg-accent-soft text-ink"
                : "self-start border border-line bg-bg-elevated text-ink"
            }`}
          >
            <p className="whitespace-pre-wrap">{m.content || (sending && i === messages.length - 1 ? "..." : "")}</p>
            {m.outfitCards?.map((card) => (
              <Link
                key={card.id}
                href={`/outfits/${card.id}`}
                className="mt-2 flex items-center gap-2 rounded-lg border border-line bg-bg p-2"
              >
                <div className="flex h-14 w-14 flex-none items-center justify-center rounded-md bg-secondary-soft">
                  {card.items.find((it) => it.image_url) ? (
                    // eslint-disable-next-line @next/next/no-img-element -- signed Supabase Storage URL
                    <img
                      src={card.items.find((it) => it.image_url)!.image_url!}
                      alt=""
                      className="h-full w-full rounded-md object-contain"
                    />
                  ) : (
                    <span className="font-mono text-[10px] text-ink-faint">{card.items.length}</span>
                  )}
                </div>
                <div>
                  <p className="font-mono text-xs text-ink-faint">Score {card.score}</p>
                  <p className="text-xs text-ink-soft">Tap to view outfit</p>
                </div>
              </Link>
            ))}
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="sticky bottom-16 flex gap-2 border-t border-line bg-bg py-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the Stylist..."
          className="flex-1 rounded-full border border-line bg-bg-elevated px-4 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-full bg-ink px-4 py-2 text-sm text-bg-elevated disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </main>
  );
}
