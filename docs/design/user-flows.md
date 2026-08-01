# User Flows

## 1. Onboarding

```mermaid
flowchart TD
    A["Sign up (email or Google/Apple)"] --> B["Welcome + brand moment<br/>('Your closet, digitized')"]
    B --> C["Quick profile: sizes, style leanings,<br/>location for weather"]
    C --> D["Batch capture mode:<br/>'Let's add your first 10 items'"]
    D --> E{"Photo per item"}
    E --> F["AI processes in background<br/>(user keeps shooting more items)"]
    F --> G["Review queue: confirm/correct<br/>AI-tagged attributes"]
    G --> H["Home ('Today') screen<br/>with first outfit suggestion"]
```

Design intent: get to a *usable* wardrobe (10–20 items) inside the first session without making the user wait on each photo — capture is decoupled from processing.

## 2. Add a Garment (core loop, used constantly)

```mermaid
flowchart TD
    A["Tap '+' (camera-first)"] --> B["Capture or select photo(s)"]
    B --> C["Upload — instant optimistic card<br/>('Processing...')"]
    C --> D["Background removal + AI tagging<br/>(async, 5-15s)"]
    D --> E["Card flips to 'Ready for review'"]
    E --> F["Attribute review sheet:<br/>category, color, pattern, season, occasion<br/>(all pre-filled, all editable)"]
    F --> G{"User edits anything?"}
    G -->|Yes| H["Save corrections"]
    G -->|No| I["Confirm as-is"]
    H --> J["Item live in Wardrobe"]
    I --> J
```

## 3. Outfit Generation (manual, from Wardrobe or Home)

```mermaid
flowchart TD
    A["Tap 'Style me' on Home,<br/>or 'Generate outfit' in Wardrobe"] --> B["Optional context sheet:<br/>occasion / mood / aesthetic / color"]
    B --> C["Engine generates 3 ranked outfits"]
    C --> D["Swipeable outfit cards<br/>(score badge + 1-line rationale)"]
    D --> E{"User action"}
    E -->|Tap card| F["Full outfit detail:<br/>items, full rationale, alternatives"]
    E -->|Swipe like| G["Saved to favorites"]
    E -->|Swipe skip| H["Next suggestion"]
    F --> I["'Swap' a slot → re-scored instantly"]
    F --> J["'Wear this today' → logs wear_log entries"]
```

## 4. AI Stylist Chat

```mermaid
flowchart TD
    A["Open Stylist tab or<br/>tap mic/chat bubble from Home"] --> B["Free-text or suggested prompt chip<br/>('I have a job interview')"]
    B --> C["Assistant resolves intent →<br/>calls tools (search/generate/weather/calendar)"]
    C --> D["Streamed reply + rich outfit cards inline"]
    D --> E{"Follow-up"}
    E -->|"'Something more casual'"| C
    E -->|"Tap a suggested outfit"| F["Outfit detail (same as flow 3)"]
    E -->|"'I wore this yesterday'"| G["Logs wear, deprioritizes<br/>in future suggestions"]
```

## 5. Daily Outfit Notification

```mermaid
flowchart TD
    A["Scheduled job runs at user's<br/>configured time each morning"] --> B["Pulls weather + calendar for today"]
    B --> C["Generates 3 outfits via Outfit Engine"]
    C --> D["Push notification:<br/>'3 looks ready for today ☀️ 72°'"]
    D --> E["Tap → Home screen pre-loaded<br/>with today's 3 options"]
    E --> F["Pick one → 'Wear this today'"]
```

## 6. Packing Assistant

```mermaid
flowchart TD
    A["Packing tab → 'New trip'"] --> B["Destination, dates, trip type"]
    B --> C["Fetch forecast (or seasonal average)"]
    C --> D["Engine composes N complete outfits<br/>+ versatile extras from owned items"]
    D --> E["Packing checklist grouped by outfit,<br/>with 'why this covers your trip'"]
    E --> F{"User adjusts"}
    F -->|Remove item| D
    F -->|Add item manually| D
    F -->|Check off while packing| G["Trip-ready state"]
```

## 7. Closet Analytics → Action

```mermaid
flowchart TD
    A["Analytics tab"] --> B["Most/least worn, cost-per-wear,<br/>duplicates, missing essentials"]
    B --> C{"User taps an insight"}
    C -->|"'12 items unworn 90+ days'"| D["Rediscovery outfit suggestions<br/>built around those items"]
    C -->|"'Missing: white sneakers'"| E["Routed to Shopping Assistant"]
    C -->|"'2 near-duplicate black tees'"| F["Prompt to archive one"]
```

## 8. Shopping Assistant

```mermaid
flowchart TD
    A["Shopping tab (or from Analytics gap)"] --> B["Gap-fill / outfit-completion<br/>recommendations (archetype-based)"]
    B --> C["Each rec shows: which outfits it unlocks,<br/>score uplift, why it fits existing wardrobe"]
    C --> D{"User action"}
    D -->|Dismiss| E["Removed from list"]
    D -->|Mark purchased| F["Prompts to add as new garment<br/>once it arrives (loops to Flow 2)"]
```

## 9. Fashion Inspiration

```mermaid
flowchart TD
    A["Inspiration tab"] --> B["Grid of aesthetic presets<br/>(Old Money, Clean Girl, Quiet Luxury...)"]
    B --> C["Select one (or describe a custom vibe)"]
    C --> D["Engine generates outfits from<br/>owned items, scored against that aesthetic"]
    D --> E["Same outfit-detail flow as Flow 3"]
```
