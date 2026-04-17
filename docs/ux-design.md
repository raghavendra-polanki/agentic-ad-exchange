# AAX Dashboard — UX Design Document

## Design Philosophy

AAX is a **content marketplace** where the traded asset is visual media — branded graphics, social posts, highlight reels. The UI must put content front and center. Every screen should feel like a place where creative work happens, not a place where numbers scroll by.

**We are NOT**: Bloomberg Terminal, Robinhood, a stock ticker dashboard.
**We ARE**: Canva's Brand Hub meets Instagram Creator Studio meets a real-time marketplace. Professional, visual, warm.

---

## Visual Language — Aligned with Pixology's FlareLab Design System

AAX is a Pixology product. The dashboard must feel like it belongs in the same family as Pixology's FlareLab — a brand manager using FlareLab should feel at home when they open the AAX Exchange.

### Color System (matching FlareLab)
```
Background (from Pixology):
  --bg-primary:    #1a1a1f       Dark charcoal (Pixology's base)
  --bg-surface:    #222228       Card/panel surface
  --bg-elevated:   #2a2a32       Elevated elements, hover states
  --bg-sidebar:    #141418       Left sidebar background

Text:
  --text-primary:  #f0f0f5       White text on dark (Pixology standard)
  --text-secondary:#a0a0b0       Labels, metadata
  --text-muted:    #6b6b78       Timestamps, tertiary info

Accent Colors (from Pixology FlareLab):
  --orange:        #f97316       PRIMARY — Pixology's signature orange. Buttons, CTAs,
                                 active states, progress indicators, selected items.
  --orange-muted:  #f97316/20%   Orange at 20% opacity for subtle backgrounds
  --purple:        #8b5cf6       SECONDARY — Pixology brand mark. Used for platform 
                                 identity elements, agent branding
  --green:         #22c55e       Success — completed deals, cleared conflicts, 
                                 checkmarks (matching FlareLab's green ✓ badges)
  --red:           #ef4444       Error — blocked conflicts, validation failures, 
                                 "Needs Regeneration" states
  --amber:         #f59e0b       Price, monetary values, warnings

Status-specific (matching FlareLab's stage badges):
  --stage-active:  #f97316       Orange background, white text (current step)
  --stage-done:    #22c55e       Green check icon (completed step)
  --stage-error:   #ef4444       Red warning icon (needs attention)
  --stage-pending: #6b6b78       Gray (not yet started)
```

### Typography
```
Headings:   Inter (600/700 weight)     — Clean, modern (matching FlareLab)
Body:       Inter (400)                 — Highly readable
Data/IDs:   JetBrains Mono (400)       — Deal IDs, prices, scores only
Section:    11px uppercase, letter-spacing 1.5px, --text-muted
            (matching FlareLab's "FLARELAB", "TOOLS", "SETTINGS" section headers)
```

### Layout Pattern (from Pixology)
- **Left sidebar navigation** — persistent, collapsible. Grouped sections with section headers.
  Matches FlareLab's sidebar (Home, Projects, Asset Library → Tools → Settings → Admin)
- **Main content area** — wide, card-based, visual-first
- **No top nav bar** — navigation lives in the sidebar. Top area is for page title + actions only.

### Component Patterns
- **Content cards**: Large image/video preview (70%+ of card height, matching FlareLab's project cards), metadata below. Orange border on selected/active cards.
- **Stage/pipeline indicators**: Horizontal steps with icons — green ✓ for done, orange for active, red △ for needs attention, gray ○ for pending. Directly from FlareLab's 6-stage workflow sidebar.
- **Agent avatars**: Colored circle with org initial. Supply=orange (Pixology family), Demand=purple.
- **Buttons**: Orange background, white text, rounded. Matches FlareLab's "Continue to Select Players →" CTA style.
- **Tags/badges**: Small rounded pills. "Game" badge in orange on content cards (from FlareLab). "SOON" badge in gray for upcoming features.
- **Conversation bubbles**: Chat-style for negotiation — supply messages left-aligned (orange accent), demand messages right-aligned (purple accent).

---

## Global Layout Pattern (All Screens)

Every screen follows FlareLab's layout: **persistent left sidebar + main content area**.

```
┌──────────────┬──────────────────────────────────────────────────┐
│              │                                                  │
│  [AAX Logo]  │   Page Title                        [+ Action]  │
│  Exchange    │                                                  │
│              │   ┌──────────────────────────────────────────┐   │
│  ┌─Org ▼───┐│   │                                          │   │
│  │ Nike    ││   │          Main Content Area               │   │
│  └─────────┘│   │          (varies per screen)              │   │
│              │   │                                          │   │
│  EXCHANGE    │   └──────────────────────────────────────────┘   │
│  ◉ Dashboard │                                                  │
│  ◻ Opps     │                                                  │
│  ◻ Deals    │                                                  │
│              │                                                  │
│  AGENTS      │                                                  │
│  ◻ Directory │                                                  │
│  ◻ Managed   │                                                  │
│              │                                                  │
│  SETTINGS    │                                                  │
│  ◻ Org       │                                                  │
│  ◻ Brand Kit │                                                  │
│  ◻ Guardrails│                                                  │
│              │                                                  │
│  ADMIN       │                                                  │
│  ◻ Onboard   │                                                  │
│  ◻ Protocol  │                                                  │
│              │                                                  │
│  ─────────── │                                                  │
│  ◻ Help      │                                                  │
│  ◻ Logout    │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
```

The greeting "Good morning, Raghavendra" at top (matching FlareLab). Orange CTA button top-right.

The wireframes below show only the **main content area** for each screen. The sidebar is always present.

---

## Screen 1: Dashboard Home ("The Exchange Floor")

The landing page. Shows real-time exchange activity with content as the visual hero.
Left sidebar nav (persistent, matching FlareLab's layout). Main content area fills the rest.

```
┌──────────────┬──────────────────────────────────────────────────────────────┐
│              │                                                              │
│  [AAX Logo]  │  Good morning, Raghavendra              [+ New Opportunity]  │
│  Exchange    │                                                              │
│              │  RECENT DEALS                                    View All ▼  │
│  ┌─Nike, Inc.┐│
│                                                                             │
│  ┌─ STATS BAR (horizontal, compact) ─────────────────────────────────────┐ │
│  │                                                                        │ │
│  │   🟢 12 Active Deals    ✓ 8 Completed    ⚡ 4.2m Avg Time    6 Agents │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ LIVE ACTIVITY FEED (2/3 width) ──────────┐  ┌─ AGENTS (1/3) ───────┐ │
│  │                                             │  │                      │ │
│  │  ● JUST NOW                                 │  │  ┌─ Online ────────┐ │ │
│  │  ┌──────────────────────────────────────┐   │  │  │                  │ │ │
│  │  │  ┌─────────┐                         │   │  │  │  [P] Pixology   │ │ │
│  │  │  │ 🖼️      │  Nike ↔ Pixology       │   │  │  │      Supply     │ │ │
│  │  │  │ content │  "Jane Doe 1000 pts"    │   │  │  │                  │ │ │
│  │  │  │ preview │                         │   │  │  │  [N] Nike       │ │ │
│  │  │  │         │  ██████████░░  AGREED   │   │  │  │      Demand     │ │ │
│  │  │  └─────────┘  $2,500 · gameday_graphic│  │  │  │                  │ │ │
│  │  │               2 rounds · 4m 12s       │   │  │  │  [G] Gatorade  │ │ │
│  │  └──────────────────────────────────────┘   │  │  │      Demand     │ │ │
│  │                                             │  │  │                  │ │ │
│  │  ● 3 MIN AGO                                │  │  │  [C] Campus Pz  │ │ │
│  │  ┌──────────────────────────────────────┐   │  │  │      Demand     │ │ │
│  │  │  ┌─────────┐                         │   │  │  │                  │ │ │
│  │  │  │ 🖼️      │  Gatorade ↔ Pixology   │   │  │  └──────────────────┘ │ │
│  │  │  │         │  "Jane Doe 1000 pts"    │   │  │                      │ │
│  │  │  │         │                         │   │  │  ┌─ Activity ─────┐  │ │
│  │  │  │         │  ⛔ BLOCKED             │   │  │  │                 │  │ │
│  │  │  └─────────┘  Conflict: BodyArmor    │   │  │  │ Nike bid $2.5k │  │ │
│  │  │               NIL deal               │   │  │  │ Gatorade blocked│ │ │
│  │  └──────────────────────────────────────┘   │  │  │ Deal agreed     │  │ │
│  │                                             │  │  │ Content sent    │  │ │
│  │  ● 5 MIN AGO                                │  │  │                 │  │ │
│  │  ┌──────────────────────────────────────┐   │  │  └─────────────────┘  │ │
│  │  │  ┌─────────┐                         │   │  │                      │ │
│  │  │  │ 🖼️      │  Campus Pizza ↔ Pix    │   │  └──────────────────────┘ │
│  │  │  │         │  $200 · social_post     │   │                          │
│  │  │  │         │  ── OUTBID              │   │                          │
│  │  │  └─────────┘                         │   │                          │
│  │  └──────────────────────────────────────┘   │                          │
│  │                                             │                          │
│  └─────────────────────────────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key design choices (aligned with FlareLab):**
- Deal cards styled like FlareLab's project cards — **large content thumbnail** (70% of card) with metadata overlay
- Orange border on active/selected deals (matching FlareLab's selected theme border)
- Cards show "Game" or "Deal" orange badge in top-left corner (matching FlareLab's badge style)
- Stage indicator on each card (like FlareLab's "Stage 4/7") showing deal progress
- Blocked/conflict deals: red accent border, conflict explanation below thumbnail
- Agent panel on right: colored circle avatars with initials (orange for supply, purple for demand)
- Stats bar is compact horizontal row — glanceable, not prominent
- "RECENT DEALS" section header in 11px uppercase muted text (matching FlareLab's "RECENT PROJECTS")

---

## Screen 2: Organization Onboarding

Split into two clear paths. Clean, focused, form-oriented.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  (Left sidebar nav always present — see Global Layout Pattern)             │
│                                                                             │
│                    Welcome to AAX Exchange                                   │
│                    Set up your organization to start trading                 │
│                                                                             │
│  ┌─ STEP 1: CREATE ORGANIZATION ─────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │   Organization Name     [ Nike, Inc.                    ]              │ │
│  │   Domain                [ nike.com                      ]              │ │
│  │                                                                        │ │
│  │   Monthly Budget        [ $50,000          ]                           │ │
│  │   Per-Deal Maximum      [ $5,000           ]                           │ │
│  │                                                                        │ │
│  │   Competitor Exclusions [ Adidas, Under Armour, Puma    ]   + Add      │ │
│  │                                                                        │ │
│  │   Auto-Approve Below    [ $1,000           ]                           │ │
│  │                                                                        │ │
│  │                                          [ Create Organization → ]     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ─── After org creation, two paths appear: ───                              │
│                                                                             │
│  ┌─ PATH A: Managed Agent ──────────┐  ┌─ PATH B: Self-Hosted Agent ────┐ │
│  │                                   │  │                                 │ │
│  │  Let AAX run an agent for you.    │  │  Connect your own AI agent.     │ │
│  │  Configure its personality and    │  │  Give it our protocol URL and   │ │
│  │  brand guidelines — we handle     │  │  your org key. It will read     │ │
│  │  the rest.                        │  │  the instructions and register  │ │
│  │                                   │  │  itself.                        │ │
│  │  ┌──────────────────────────┐     │  │                                 │ │
│  │  │ Agent Type  [Demand ▼]   │     │  │  Protocol URL:                  │ │
│  │  │                          │     │  │  ┌────────────────────────────┐ │ │
│  │  │ Persona                  │     │  │  │ https://aax.example.com/   │ │ │
│  │  │ [Aggressive bidder,     ]│     │  │  │ protocol.md           [📋] │ │ │
│  │  │ [premium sports brand   ]│     │  │  └────────────────────────────┘ │ │
│  │  │                          │     │  │                                 │ │
│  │  │ Tagline                  │     │  │  Org API Key:                   │ │
│  │  │ [ Just Do It            ]│     │  │  ┌────────────────────────────┐ │ │
│  │  │                          │     │  │  │ aax_org_a8f2c...     [📋] │ │ │
│  │  │ Target Demographics      │     │  │  └────────────────────────────┘ │ │
│  │  │ [ 18-34, athletics     ]│     │  │                                 │ │
│  │  │                          │     │  │  Tell your agent:               │ │
│  │  │ Preferred Formats        │     │  │  "Join the AAX exchange.        │ │
│  │  │ ☑ Gameday Graphics      │     │  │   Read [protocol URL].          │ │
│  │  │ ☑ Highlight Reels       │     │  │   Use org key [key]."           │ │
│  │  │ ☐ Social Posts          │     │  │                                 │ │
│  │  │                          │     │  │                                 │ │
│  │  │ Strategy                 │     │  │                                 │ │
│  │  │ ○ Aggressive             │     │  │                                 │ │
│  │  │ ● Selective              │     │  │                                 │ │
│  │  │ ○ Conservative           │     │  │                                 │ │
│  │  └──────────────────────────┘     │  │                                 │ │
│  │                                   │  │                                 │ │
│  │  [ Launch Agent → ]               │  │                                 │ │
│  │                                   │  │                                 │ │
│  └───────────────────────────────────┘  └─────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key design choices:**
- Two paths are presented side by side as equal options — not a primary/secondary hierarchy
- Path A is a rich form with personality configuration — this IS the agent
- Path B is minimal — just copy two values. The complexity is on the agent side, not the platform.
- Copy buttons (📋) next to protocol URL and org key for easy clipboard copy
- The "tell your agent" instruction is written as natural language the human can paste into their agent

---

## Screen 3: Opportunity Feed ("The Marketplace")

Where supply agents list content opportunities. Visual-first — large content previews, like a Pinterest board.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  (Left sidebar nav always present — see Global Layout Pattern)             │
│                                                                             │
│  Opportunities               Filter: [All Sports ▼] [All Formats ▼]  🔍    │
│  3 active opportunities                                                     │
│                                                                             │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐   │
│  │                      │ │                      │ │                      │  │
│  │  ┌──────────────┐   │ │  ┌──────────────┐   │ │  ┌──────────────┐   │  │
│  │  │              │   │ │  │              │   │ │  │              │   │  │
│  │  │  [Hero image │   │ │  │  [Hero image │   │ │  │  [Hero image │   │  │
│  │  │   of the     │   │ │  │   of the     │   │ │  │   of the     │   │  │
│  │  │   moment -   │   │ │  │   moment -   │   │ │  │   moment -   │   │  │
│  │  │   athlete    │   │ │  │   team       │   │ │  │   game       │   │  │
│  │  │   photo]     │   │ │  │   photo]     │   │ │  │   highlight] │   │  │
│  │  │              │   │ │  │              │   │ │  │              │   │  │
│  │  └──────────────┘   │ │  └──────────────┘   │ │  └──────────────┘   │  │
│  │                      │ │                      │ │                      │  │
│  │  Jane Doe Scores     │ │  MIT Wins Conference │ │  Rivalry Game        │  │
│  │  1000th Career Point │ │  Championship        │ │  Comeback Win        │  │
│  │                      │ │                      │ │                      │  │
│  │  🏀 Basketball · MIT │ │  🏀 Basketball · MIT │ │  🏈 Football · MIT  │  │
│  │                      │ │                      │ │                      │  │
│  │  📊 150k reach       │ │  📊 85k reach        │ │  📊 200k reach      │  │
│  │  💰 Min $500         │ │  💰 Min $300         │ │  💰 Min $800        │  │
│  │  📸 Graphic, Social  │ │  📸 Social           │ │  📸 Graphic, Video  │  │
│  │                      │ │                      │ │                      │  │
│  │  ┌────────────────┐  │ │  ┌────────────────┐  │ │  ┌────────────────┐ │  │
│  │  │ Pixology       │  │ │  │ Pixology       │  │ │  │ Pixology       │ │  │
│  │  │ 3 agents       │  │ │  │ 2 agents       │  │ │  │ 4 agents       │ │  │
│  │  │ matched        │  │ │  │ matched        │  │ │  │ matched        │ │  │
│  │  └────────────────┘  │ │  └────────────────┘  │ │  └────────────────┘ │  │
│  │                      │ │                      │ │                      │  │
│  │  ⏱ Expires in 1h 42m│ │  ⏱ Expires in 45m   │ │  ⏱ Expires in 2h   │  │
│  │                      │ │                      │ │                      │  │
│  └──────────────────────┘ └──────────────────────┘ └──────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key design choices:**
- **Pinterest-style card grid** — large image previews dominate each card
- The moment's athlete/team photo is the hero (we can use placeholder images, or content supplied by the supply agent)
- Cards show: sport icon, school, projected reach, minimum price, available formats
- Match count tells you how many agents are interested (social proof)
- Expiry countdown creates urgency — matches the "speed of culture" thesis
- Clicking a card goes to the opportunity detail / deal negotiation view

---

## Screen 4: Deal Detail / Negotiation View

The centerpiece. Shows the negotiation as a **conversation** between two agents, with content preview and deal terms.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  (Left sidebar nav always present — see Global Layout Pattern)             │
│                                                                             │
│  ← Back to Dashboard                                                        │
│                                                                             │
│  ┌─ DEAL HEADER ─────────────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  ┌────────────────────────┐   Jane Doe Scores 1000th Career Point     │ │
│  │  │                        │                                            │ │
│  │  │   [Large content       │   [P] Pixology  ←→  [N] Nike             │ │
│  │  │    preview image -     │                                            │ │
│  │  │    the actual          │   🏀 MIT Basketball · 150k reach           │ │
│  │  │    generated graphic   │   Status: ██████████████░░  AGREED         │ │
│  │  │    or opportunity      │   $2,500 · Gameday Graphic · IG, Twitter   │ │
│  │  │    hero image]         │   2 rounds · 4 min 12 sec                  │ │
│  │  │                        │                                            │ │
│  │  └────────────────────────┘                                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ NEGOTIATION (2/3 width) ─────────────┐  ┌─ DEAL TERMS (1/3) ───────┐ │
│  │                                        │  │                           │ │
│  │  ┌─ MATCHING ────────────────────────┐ │  │  Current Terms            │ │
│  │  │  Nike       87/100  ✓ Cleared     │ │  │                           │ │
│  │  │  Gatorade   72/100  ✗ Blocked     │ │  │  Price      $2,500       │ │
│  │  │  Campus Pz  45/100  ✓ Cleared     │ │  │  Format     Gameday      │ │
│  │  └───────────────────────────────────┘ │  │  Platforms  IG, Twitter   │ │
│  │                                        │  │  Rights     14 days       │ │
│  │  ┌─ CONVERSATION ────────────────────┐ │  │  Exclusivity 48 hours    │ │
│  │  │                                    │ │  │                           │ │
│  │  │        ┌──────────────────────┐    │ │  │  ─────────────────────── │ │
│  │  │        │ Nike (Demand)        │    │ │  │                           │ │
│  │  │        │                      │    │ │  │  Original Terms           │ │
│  │  │        │ "D1 basketball       │    │ │  │  Price      $2,500       │ │
│  │  │        │  milestone, 150k     │    │ │  │  Rights     7 days       │ │
│  │  │        │  reach. Strong       │    │ │  │  Exclusivity 24 hours    │ │
│  │  │        │  'Just Do It'        │    │ │  │                           │ │
│  │  │        │  narrative angle."   │    │ │  │  Changes                  │ │
│  │  │        │                      │    │ │  │  Rights   7d → 14d  ↑    │ │
│  │  │        │  BID $2,500          │    │ │  │  Exclus.  24h → 48h ↑   │ │
│  │  │        │  Score: 82/100       │    │ │  │                           │ │
│  │  │        └──────────────────────┘    │ │  └───────────────────────────┘ │
│  │  │                                    │ │                                │
│  │  │  ┌──────────────────────┐          │ │  ┌─ CONFLICT LOG ──────────┐  │
│  │  │  │ Pixology (Supply)    │          │ │  │                          │  │
│  │  │  │                      │          │ │  │  ✓ Nike                  │  │
│  │  │  │ "Nike at $2,500 —    │          │ │  │    Pre-screen: cleared   │  │
│  │  │  │  above minimum.      │          │ │  │    Final: cleared        │  │
│  │  │  │  Premium brand, good │          │ │  │                          │  │
│  │  │  │  for portfolio. But  │          │ │  │  ✗ Gatorade              │  │
│  │  │  │  requesting longer   │          │ │  │    Pre-screen: cleared   │  │
│  │  │  │  usage rights."      │          │ │  │    Final: BLOCKED        │  │
│  │  │  │                      │          │ │  │    → Jane Doe has        │  │
│  │  │  │  COUNTER             │          │ │  │      BodyArmor NIL deal. │  │
│  │  │  │  14-day rights       │          │ │  │      BodyArmor competes  │  │
│  │  │  │  48h exclusivity     │          │ │  │      with Gatorade.      │  │
│  │  │  └──────────────────────┘          │ │  │                          │  │
│  │  │                                    │ │  │  ✓ Campus Pizza          │  │
│  │  │        ┌──────────────────────┐    │ │  │    Cleared (outbid)      │  │
│  │  │        │ Nike (Demand)        │    │ │  │                          │  │
│  │  │        │                      │    │ │  └──────────────────────────┘  │
│  │  │        │ "14-day rights       │    │ │                                │
│  │  │        │  reasonable for this │    │ │                                │
│  │  │        │  milestone content.  │    │ │                                │
│  │  │        │  ACCEPT."            │    │ │                                │
│  │  │        └──────────────────────┘    │ │                                │
│  │  │                                    │ │                                │
│  │  │  ✅ DEAL AGREED · 9:49 PM          │ │                                │
│  │  │                                    │ │                                │
│  │  └────────────────────────────────────┘ │                                │
│  │                                        │                                │
│  └────────────────────────────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key design choices:**
- **Content preview is large** at the top — the hero image/graphic is always visible
- **Conversation layout** like a chat interface — Nike's messages right-aligned (violet), Pixology's left-aligned (teal)
- Each message bubble shows: the agent's reasoning (quoted from LLM output), their decision (BID/COUNTER/ACCEPT), and their score
- **Deal terms sidebar** shows current vs original with change indicators (↑ ↓)
- **Conflict log** on right shows the full audit of who was screened, who was blocked, and why — with the conflict chain explained in plain language
- **Matching section** at top of conversation shows all agents' relevance scores and conflict status

---

## Screen 5: Content & Fulfillment View

Shown within the deal detail after deal agreement. Focuses on the generated content and validation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─ FULFILLMENT PIPELINE ────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  ● Brief ──── ● Content ──── ● Validate ──── ● Approve ──── ○ Deliver │ │
│  │  Generated    Generating     ← Current                                 │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ CONTENT PREVIEW (large, center) ─────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  ┌────────────────────────────────────────────────────────────────┐    │ │
│  │  │                                                                │    │ │
│  │  │                                                                │    │ │
│  │  │              [Full-size preview of the generated               │    │ │
│  │  │               branded graphic / social post /                  │    │ │
│  │  │               highlight reel thumbnail]                        │    │ │
│  │  │                                                                │    │ │
│  │  │              This is THE content being traded.                 │    │ │
│  │  │              It should be BIG and beautiful.                   │    │ │
│  │  │                                                                │    │ │
│  │  │                                                                │    │ │
│  │  └────────────────────────────────────────────────────────────────┘    │ │
│  │                                                                        │ │
│  │  Gameday Graphic · 1080x1080 · Instagram, Twitter                      │ │
│  │  Generated by Pixology · 9:50 PM                                       │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ VALIDATION RESULTS ──────────────────┐  ┌─ CREATIVE BRIEF ──────────┐ │
│  │                                        │  │                            │ │
│  │  Overall: 94/100  ✅ PASSED            │  │  Athlete: Jane Doe         │ │
│  │                                        │  │  School: MIT               │ │
│  │  ✅ Brand logo present (top-right)     │  │  Sport: Basketball         │ │
│  │  ✅ Color palette matches guidelines   │  │  Moment: 1000th point      │ │
│  │  ✅ "Just Do It" messaging correct     │  │                            │ │
│  │  ✅ FTC disclosure "#ad" present       │  │  Brand: Nike               │ │
│  │  ✅ NCAA compliance disclosure         │  │  Logo: nike_swoosh_white   │ │
│  │                                        │  │  Message: "Just Do It —    │ │
│  │  Validated by Claude Vision            │  │   1000 points"             │ │
│  │  9:52 PM                               │  │  Colors: #000, #FFF        │ │
│  │                                        │  │  Disclosures: #ad, #NIL    │ │
│  └────────────────────────────────────────┘  └────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key design choices:**
- **Content preview dominates the page** — large, centered, full-width. This is the product.
- Pipeline stepper shows fulfillment progress with clear current state indicator
- Validation results are a checklist — green checks for pass, red X for fail. Simple, scannable.
- Creative brief shown alongside as reference — what was asked for vs what was delivered
- If validation fails, this screen would show revision instructions prominently, with before/after content previews

---

## Screen 6: Agent Profile / Directory

Shows detailed view of a registered agent. Useful for the human observer to understand agent behavior.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─ AGENT HEADER ────────────────────────────────────────────────────────┐ │
│  │                                                                        │ │
│  │  [N]  Nike Demand Agent                              🟢 Online         │ │
│  │       Nike, Inc. · Demand · Aggressive                                 │ │
│  │       "Empowering, competitive, aspirational"                          │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─ STATS ──────────┐  ┌─ STANDING QUERIES ────────────────────────────┐  │
│  │                   │  │                                               │  │
│  │  Opps received: 8 │  │  🏀 Basketball · reach > 50k · any conf.    │  │
│  │  Bids submitted: 3│  │  🏈 Football · SEC, Big Ten · reach > 100k  │  │
│  │  Deals closed: 1  │  │  🏆 Any sport · milestone · reach > 200k    │  │
│  │  Conflicts: 0     │  │                                               │  │
│  │  Spent: $2,500    │  └───────────────────────────────────────────────┘  │
│  │  of $50k monthly  │                                                     │
│  │  ━━░░░░░░ 5%      │  ┌─ GUARDRAILS ─────────────────────────────────┐  │
│  │                   │  │  Auto-approve below: $1,000                   │  │
│  └───────────────────┘  │  Per-deal max: $5,000                         │  │
│                          │  Competitors: Adidas, Under Armour, Puma      │  │
│                          └──────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ RECENT ACTIVITY ────────────────────────────────────────────────────┐  │
│  │                                                                       │  │
│  │  ┌─────────┐  "Jane Doe 1000 pts" → BID $2,500 → DEAL AGREED        │  │
│  │  │ 🖼️      │  Score: 82/100 · "Strong milestone narrative..."        │  │
│  │  └─────────┘  4 min ago                                               │  │
│  │                                                                       │  │
│  │  ┌─────────┐  "Conference semifinal highlight" → PASSED              │  │
│  │  │ 🖼️      │  Score: 34/100 · "Reach 22k below my 50k minimum."     │  │
│  │  └─────────┘  28 min ago                                              │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key design choices:**
- Agent avatar is prominent with color coding by role (violet for demand, teal for supply)
- Recent activity shows **content thumbnails** — even in the activity log, the visual asset is visible
- Each activity shows the agent's LLM reasoning — the observer can see WHY the agent decided what it decided
- Guardrails and standing queries are visible — the observer can see the agent's configuration
- Budget utilization bar shows spend against monthly ceiling

---

## Navigation Structure — Left Sidebar (Pixology Pattern)

```
┌──────────────────────┐
│  [AAX Logo] Exchange  │
│  ┌─ Org Selector ▼ ─┐│
│  │  Nike, Inc.       ││
│  └───────────────────┘│
│                        │
│  EXCHANGE              │
│  ◉ Dashboard     /     │
│  ◻ Opportunities /opps │
│  ◻ Deals         /deals│
│                        │
│  AGENTS                │
│  ◻ Agent Directory     │
│  ◻ Managed Agents      │
│                        │
│  SETTINGS              │
│  ◻ Organization        │
│  ◻ Brand Kit           │
│  ◻ Guardrails          │
│                        │
│  ADMIN                 │
│  ◻ Onboarding   /onboard│
│  ◻ Protocol URL        │
│  ◻ Usage & Billing     │
│                        │
│  ───────────────────   │
│  ◻ Help                │
│  ◻ Logout              │
└────────────────────────┘
```

This mirrors FlareLab's sidebar structure: grouped sections (FLARELAB → TOOLS → SETTINGS → ADMIN → PLATFORM), with the org selector at top.

---

## Responsive Considerations

- **Desktop (>1200px)**: Full layout as shown — sidebar panels, multi-column grids
- **Tablet (768-1200px)**: Single column, cards stack vertically, sidebar collapses to tabs
- **Mobile**: Not a priority for class demo. Dashboard is primarily desktop.

---

## Summary: Content-First Principles

1. **Every screen shows visual content** — thumbnails on deal cards, hero images on opportunities, full-size preview on fulfillment
2. **Conversations, not state badges** — the negotiation is shown as agent chat, not just "status: negotiating"
3. **Reasoning is visible** — every agent decision shows the LLM's quoted reasoning
4. **Warm creative palette** — dark but warm, teal/violet/amber accents, clean sans-serif typography
5. **Cards are visual** — images take 50-60% of card space, metadata is secondary
6. **Conflict stories are told** — not just "blocked" but the full chain: "Jane Doe → BodyArmor → competes with Gatorade"
