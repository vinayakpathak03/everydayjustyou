# UI Wireframes

Low-fidelity wireframes for the core screens are published as an interactive visual reference — see **[wireframes.html artifact]** (shared alongside this doc). This file describes the intent and layout logic of each screen so the wireframes can be implemented faithfully.

Design language: near-white/near-black neutral canvas, one accent used sparingly, system font stack (SF Pro / Inter), generous 16–24px spacing rhythm, large rounded corners (16–20px) on cards, soft shadows, garment photography (background-removed) as the dominant visual element on every screen it appears.

## 1. Home ("Today")
- Greeting + date + weather chip, top-left, minimal.
- Hero: today's top outfit suggestion as a large card (collage of items), with score badge and one-line rationale.
- Horizontal scroll: 2 more alternative outfits, smaller cards.
- Quick actions row: "Add item", "Ask Stylist", "Plan a trip".
- Bottom tab bar: Home, Wardrobe, Stylist (center, emphasized), Analytics, Profile.

## 2. Wardrobe Grid
- Segmented filter bar (Category chips: All, Tops, Bottoms, Dresses, Outerwear, Shoes, Bags, Accessories, Jewelry) — horizontally scrollable.
- Secondary filter sheet (tap "Filters"): color swatches, season, occasion, favorites-only, brand.
- Search bar supports natural language ("flowy summer dress") routed to semantic search.
- Masonry/grid of garment cards — clean product-shot on neutral background, no visible chrome except on tap/hold.
- Floating "+" action button (camera-first) bottom-right, thumb reach zone.

## 3. Add Item Flow
- Full-screen camera view by default; gallery picker as secondary option.
- After capture: instant card with a subtle shimmer/skeleton state labeled "Working on it..."
- Multi-photo: horizontal thumbnail strip under the primary photo, "+add another angle".
- Review sheet slides up from bottom (iOS-sheet style): attribute fields as tappable chips/pickers, pre-filled and highlighted if AI confidence is low (so the user knows what's worth double-checking) — never a blocking red "error," just a soft affordance to review.

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

## 6. AI Stylist Chat
- Standard chat layout, but assistant messages can render **outfit cards inline**, not just text — the chat is a first-class outfit-suggestion surface, not just Q&A.
- Suggested prompt chips above the input on empty state: "What should I wear for dinner?", "I have a job interview", "Show me pink outfits".
- Input bar supports text + camera (e.g., "what do you think of this new piece with my closet?").

## 7. Closet Analytics
- Top stat row: total items, avg. cost-per-wear, % worn in last 30 days — big numbers, minimal chrome.
- Sections as horizontally-scrollable card rows: Most Worn, Rediscover These (least worn), Possible Duplicates, Missing Essentials, Seasonal Rotation.
- Tapping any card routes into the relevant action flow (outfit suggestion, shopping, archive prompt).

## 8. Packing Assistant
- Trip form (destination, dates, type) as a clean stepper.
- Result: outfits grouped by day/occasion, plus a flat packing checklist beneath, each item tappable to toggle "packed."

## 9. Shopping Assistant
- Card list, each showing the *archetype* being recommended (e.g., "Tan crossbody bag") rendered as an elegant sketch/placeholder (not a real product yet in V1) with "+15 pts to 4 of your outfits" framing and the outfits it would unlock.

## 10. Fashion Inspiration
- Grid of aesthetic mood-board tiles (Old Money, Clean Girl, Minimalist, Korean Fashion, Streetwear, Quiet Luxury), each a curated color/texture thumbnail.
- Selecting one behaves like Outfit Generator, pre-set to that aesthetic's scoring bias.

## 11. Settings / Profile
- Notification time picker (daily outfit push).
- Style profile (sizes, preferred colors/aesthetics, dislikes).
- Calendar connection toggle.
- Privacy & data (export, delete account) — surfaced clearly, not buried, given how personal this data is.
