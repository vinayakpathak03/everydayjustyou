# UI Wireframes

Low-fidelity wireframes for the core screens are published as an interactive visual reference — see **[wireframes.html artifact]** (shared alongside this doc). This file describes the intent and layout logic of each screen so the wireframes can be implemented faithfully.

Design language: near-white/near-black neutral canvas, one accent used sparingly, system font stack (SF Pro / Inter), generous 16–24px spacing rhythm, large rounded corners (16–20px) on cards, soft shadows, garment photography (background-removed) as the dominant visual element on every screen it appears. Accent palette is the **Barbie-land** direction from PRD §8.1 — lilac `#CDB4DA`, blush `#FFC8DC`, pink `#FFAFCC`, magenta `#E55E99`, orchid `#EBB9DF` — used the same way the earlier sage/camel accents were: sparingly, on badges, chips, and primary actions, never flooding a background.

## 0. Onboarding — Invite, T&C & Consent (new)
- Reached only via an invite link (token) — there is no public "Sign up" screen or link to one anywhere in the app.
- Account step: Supabase Auth email/password or Google/Apple, minimal chrome.
- **T&C + Consent screen — the one screen in this whole spec required to be un-skippable and not gestured around:** scrollable T&C text (developer's own copy — content owned outside this spec, see PRD §7.1) with the **developer photo-access toggle physically embedded partway down the same screen**, not on a separate settings page — default **ON** (pre-checked), clearly labeled, with a one-line plain-language explanation next to it. Below the T&C text, a short highlighted callout (not buried in dense paragraph text) restates the two things people are least likely to read carefully otherwise: (a) photos are sent to Google's Gemini API for analysis, and on the free tier Google may use them to improve its models; (b) please don't upload underwear/lingerie photos — use the manual entry option (screen 3a) for those instead. A single "I agree" primary button at the bottom is disabled until the user has scrolled through the text (standard iOS pattern for meaningful consent, not just a checkbox of convenience).
- Only after this screen: quick profile (sizes, style leanings, location), then batch capture (screen 3).

## 1. Home ("Today")
- Greeting + date + weather chip, top-left, minimal.
- Hero: today's top outfit suggestion as a large card (collage of items), with score badge and one-line rationale.
- Horizontal scroll: 2 more alternative outfits, smaller cards.
- Quick actions row: "Add item", "Ask Stylist", "Plan a trip".
- Bottom tab bar: Home, Wardrobe, Stylist (center, emphasized), Analytics, Profile.

## 2. Wardrobe Grid
- Stats header (PRD §6.16): item / outfit / moodboard counts, quick-jump category rail, favorites/archived filters — private by default, this is a personal-collection view, not a public profile.
- Segmented filter bar (Category chips: All, Tops, Bottoms, Dresses, Outerwear, Shoes, Bags, Accessories, Jewelry) — horizontally scrollable.
- Secondary filter sheet (tap "Filters"): color swatches, season, occasion, favorites-only, brand.
- Search bar supports natural language ("flowy summer dress") routed to semantic search.
- Masonry/grid of garment cards — clean product-shot on neutral background, no visible chrome except on tap/hold.
- Floating "+" action button (camera-first) bottom-right, thumb reach zone.

## 3. Add Item Flow
- Category picker is the first step, not the camera — this is what lets a sensitive category route to 3a instead of the camera flow below.
- Full-screen camera view by default; gallery picker as secondary option.
- After capture: instant card with a subtle shimmer/skeleton state labeled "Working on it..."
- Multi-photo: horizontal thumbnail strip under the primary photo, "+add another angle".
- Review sheet slides up from bottom (iOS-sheet style): attribute fields as tappable chips/pickers, pre-filled and highlighted if AI confidence is low (so the user knows what's worth double-checking) — never a blocking red "error," just a soft affordance to review. Acquisition type (new/pre-loved/rental/handmade/gifted) is an optional chip here, feeding §6.15's composition analytics.

## 3a. Add Item — Sensitive Category (manual entry, new)
- Reached when the category picker's selection is auto-flagged sensitive (underwear, lingerie, similar), or the user manually toggles "mark as sensitive" on any category.
- No camera-first prompt here — the screen opens straight to a plain form: description (text), quantity (stepper), category, color (optional swatch picker). A small note explains why: "Skipping AI tagging for this one — see [why]."
- Photo is explicitly optional, framed as "not required," with a one-line reminder if the user does attach one: "This photo stays local to your account — it's never sent to Google's AI, and it won't appear in outfit suggestions."
- Saved items appear in the Wardrobe grid like any other (for record-keeping/quantity tracking) but never surface in Outfit Generator results, Canvas, Dress Me, or Moodboard matching — there's no toggle to change that from the item's own detail screen, since the exclusion isn't a per-screen preference.

## 4. Item Detail
- Full-bleed hero image, swipeable through all photos for that item.
- Attribute list below, editable inline.
- "Worn 4 times · last worn 12 days ago · cost per wear $8.40" stat line.
- "Outfits featuring this item" horizontal scroll.
- "Style this item" CTA → jumps into Outfit Generator pre-anchored to this piece.

## 5. Outfit Generator / Result
- Context sheet (optional, collapsible): occasion, mood chips, aesthetic chips, color preference.
- Result: swipeable full-screen outfit cards (Tinder-like stack), each showing the flat-lay collage, score badge (1–100, colored ring), and a 1–2 line rationale beneath.
- Tap a card → detail view: itemized list of the outfit's pieces (each tappable to its own Item Detail), full rationale text, per-slot "swap" icon, "Wear this today" primary button.
- Three ways into an outfit from here on, all writing to the same `outfits` table: accept an AI suggestion (this screen), assemble by hand (screen 6, Canvas), or pin-and-shuffle (screen 7, Dress Me).

## 6. Styling Canvas (new)
- Freeform board: items dragged in from the wardrobe grid, layered and positioned by hand — resize, rotate slightly, reorder front/back, duplicate, delete, undo.
- Toolbar: undo (top-left), Save (top-right, primary).
- This is the manual counterpart to screen 5 — same outfit model underneath, `source = manual`, reopenable and re-editable via the stored layout.

## 7. Dress Me — Quick Shuffle (new)
- Item grid organized by slot, browsable in grid/list/single-column layouts (toggle row at the bottom).
- Pin icon on any item locks it in; a shuffle (dice) control re-rolls everything unlocked, constrained by the same compatibility engine as screen 5 — not random noise.
- Sits between full AI generation (5) and fully manual (6): fast, game-like, but still rule-grounded.

## 8. AI Stylist Chat
- Standard chat layout, but assistant messages can render **outfit cards inline**, not just text — the chat is a first-class outfit-suggestion surface, not just Q&A.
- Suggested prompt chips above the input on empty state: "What should I wear for dinner?", "I have a job interview", "Show me pink outfits".
- Input bar supports text + camera (e.g., "what do you think of this new piece with my closet?").

## 9. Closet Analytics
- Top stat row: total items, avg. cost-per-wear, % worn in last 30 days — big numbers, minimal chrome.
- **Wardrobe usage gauge** (§6.15): a single horizontal meter, 0–100%, with the trend delta as a small pill ("You wore 20% more").
- **Composition donut** (§6.15): segmented by acquisition type (new / pre-loved / rental / handmade / gifted / undefined), filterable by category; each segment uses a distinct accent tint rather than one flat color, so the chart itself carries information at a glance.
- Sections as horizontally-scrollable card rows: Most Worn, Rediscover These (least worn), Possible Duplicates, Missing Essentials, Seasonal Rotation.
- Tapping any card routes into the relevant action flow (outfit suggestion, shopping, archive prompt).

## 10. Packing Assistant
- Trip form (destination, dates, type) as a clean stepper.
- Result: a day-by-day header strip (day name + date badge, e.g. "Mon 03", "Tue 04"...) each with its planned outfit thumbnail beneath — the checklist is organized by day first, not a single flat list — plus overall progress ("1/10 items packed") at the top of the trip card.
- Tapping a day's thumbnail opens that day's outfit detail (same as Flow 3) to swap pieces without leaving the trip.

## 11. Shopping Assistant
- Card list, each showing the *archetype* being recommended (e.g., "Tan crossbody bag") rendered as an elegant sketch/placeholder (not a real product yet in V1) with "+15 pts to 4 of your outfits" framing and the outfits it would unlock.

## 12. Fashion Inspiration
- Grid of aesthetic mood-board tiles (Old Money, Clean Girl, Minimalist, Korean Fashion, Streetwear, Quiet Luxury), each a curated color/texture thumbnail.
- Selecting one behaves like Outfit Generator, pre-set to that aesthetic's scoring bias.

## 13. Moodboards
- Grid of board covers (named tiles: "Party", "Office", "Summer", "Bday wishes"), each a 2x2 preview of its most recent clips.
- Inside a board: masonry grid of saved clips; each clip that has a wardrobe match shows a small badge — tap to see the matched owned item(s) side by side with the inspiration image.
- "+" adds a clip via share-sheet URL, screenshot upload, or in-app camera — same capture-first pattern as adding a garment (Flow 2), reusing the same processing/review affordance.
- "Style me like this board" CTA on each board hands off into the Outfit Generator / Stylist with that board as context.

## 14. Weekly Planner
- Horizontal day strip (Sun–Sat), each day a compact column: weekday label, date, small weather glyph, and either a planned-outfit thumbnail or an empty "+ plan" state.
- Today is visually emphasized (accent-colored date badge); past days in the current week show what was actually worn (read from `wear_logs`) rather than the plan, once the day has passed.
- Tapping an empty day opens the same swipeable outfit-generation flow as Flow 3, but the "Wear this today" primary action becomes "Plan for [day]."
- A subtle inline nudge appears if a day's plan repeats an outfit worn in the last N days ("You wore this Tuesday too — swap it up?").

## 15. Settings / Profile
- Notification time picker (daily outfit push).
- Style profile (sizes, preferred colors/aesthetics, dislikes).
- Calendar connection toggle.
- Privacy & data section: developer photo-access toggle (same setting as onboarding screen 0, revocable here at any time — full T&C text stays linked/re-readable, not just the toggle), export data, delete account — surfaced clearly, not buried, given how personal this data is.
- Private-circle sharing controls, if that USP candidate (PRD §10) gets greenlit — off by default.
