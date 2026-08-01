import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { TabBar } from "@/components/ui/TabBar";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchOnboardingCompleted(accessToken: string): Promise<boolean> {
  const res = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!res.ok) return false;
  const user = (await res.json()) as { onboarding_completed_at: string | null };
  return user.onboarding_completed_at !== null;
}

// Gates the authenticated app shell behind the T&C/consent screen (PRD §7.1) —
// middleware.ts only checks "does a session exist," this checks "has this
// specific user actually cleared onboarding," which needs a call to the API
// (the source of truth for onboarding_completed_at), not just the Supabase session.
export default async function MainLayout({ children }: { children: React.ReactNode }) {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/sign-in");
  }

  const completed = await fetchOnboardingCompleted(session.access_token);
  if (!completed) {
    redirect("/onboarding/consent");
  }

  return (
    <div className="min-h-screen pb-16">
      {children}
      <TabBar />
    </div>
  );
}
