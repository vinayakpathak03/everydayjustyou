import { redirect } from "next/navigation";

// No public landing page — this app is invite-only (docs/PRD.md §1a). Anyone
// hitting "/" either already has a session (middleware lets them through, land
// on Today) or doesn't (middleware redirects to /sign-in before this even renders).
export default function RootPage() {
  redirect("/today");
}
