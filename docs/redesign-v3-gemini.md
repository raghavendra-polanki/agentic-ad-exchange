# AAX v3 — Gemini-Powered Creative Intelligence

**Status**: Active implementation
**Parent docs**: `redesign-v2.md` (protocol architecture), `product-architecture.md` (vision)
**Purpose**: Upgrade AAX from a passive matchmaker to an intelligent creative platform using Gemini for vision analysis, agent reasoning, and branded content generation.

---

## 1. What's Changing

| Aspect | v2 (Current) | v3 (This) |
|--------|-------------|-----------|
| Agent LLM | Claude (Anthropic SDK) | **Gemini** (`google-genai` Python SDK) |
| Opportunity signal | Text description only | **Image + context** (real visual content) |
| Platform matching | Sport + reach keywords | **Visual scene analysis** → category + tier inference |
| Agent reasoning | 1 LLM call, hidden | **Multi-step streamed reasoning with thoughts** |
| Negotiation object | Price only | **Tier + placement + price + creative direction** |
| Content generation | Mock URL | **Real Gemini image generation** (2-3 branded options) |
| Content validation | Claude Vision pass/fail | **Both parties review generated images** |
| UI deal view | Static text dump | **Live streaming thoughts + image previews** |
| Image storage | None | **Local filesystem served via FastAPI** |

---

## 2. Core Concept: The Platform as Creative Director

The platform agent isn't just matching buyers and sellers — it **sees** the content, **understands** what brands would fit, **suggests** placement types at different price points, and **generates** the final branded content.

### Placement Tier Model

| Tier | Type | Description | Price Multiplier | Example |
|------|------|-------------|-----------------|---------|
| 1 | Background/Ambient | Brand visible but not focal | 1x | Court-side banner, arena signage |
| 2 | Scene Integration | Brand naturally present | 2-3x | Jersey patch, equipment branding |
| 3 | Product Interaction | Athlete actively using brand | 4-6x | Wearing shoes, drinking product, holding item |

---

## 3. Gemini Integration Architecture

### Models Used

| Purpose | Model | Why |
|---------|-------|-----|
| Vision analysis (scene understanding) | `gemini-3-flash-preview` | Latest, fast, good at structured output + thinking |
| Agent reasoning (with thoughts) | `gemini-3-flash-preview` | Streaming thoughts support, fast enough for real-time |
| Image generation (branded content) | `gemini-3-pro-image-preview` | Best quality native image editing with reference images |

### Python SDK Pattern (ported from Pixology Node.js adaptor)

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)

# Vision analysis
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        types.Part.from_text(prompt),
    ],
)

# Streaming with thoughts
for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents=[image_part, text_part],
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=8192,
        ),
    ),
):
    # chunk.candidates[0].content.parts → thought vs content

# Image generation with reference
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=[
        types.Part.from_bytes(data=original_image, mime_type="image/jpeg"),
        types.Part.from_bytes(data=brand_logo, mime_type="image/png"),
        types.Part.from_text(generation_prompt),
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
    ),
)
```

### Module Structure

```
server/src/gemini/
├── __init__.py
├── adaptor.py              # Core Gemini client wrapper
│                            #   - analyze(image_bytes, prompt) → text/JSON
│                            #   - analyze_stream(image_bytes, prompt, on_chunk) → streamed thoughts + result
│                            #   - generate_image(prompt, reference_images, aspect_ratio) → image bytes
│
├── scene_analyzer.py       # Platform Agent's vision
│                            #   - analyze_scene(image_bytes) → SceneAnalysis
│                            #   - detect_brand_zones(image_bytes) → list[BrandZone]
│                            #   - suggest_placements(image_bytes) → list[PlacementSuggestion]
│
└── content_generator.py    # Platform Agent's creative output
                             #   - generate_branded_options(original, brand_assets, tier, instructions) → list[GeneratedImage]
                             #   - validate_composition(generated, original) → CompositionCheck
```

---

## 4. Updated Deal Flow

### Step 1: Supply Agent Signals Opportunity (with image)

```
POST /api/v1/opportunities/
Content-Type: multipart/form-data

image: <binary image file>
context: {
  "content_description": "Jane Doe 1000th career point — mid-air dunk",
  "subjects": [{"athlete_name": "Jane Doe", "school": "MIT", "sport": "basketball"}],
  "audience": {"projected_reach": 150000, "trending_score": 8.5},
  "min_price": 500
}
```

### Step 2: Platform Agent Analyzes Scene (Gemini Vision, streamed)

```python
# scene_analyzer.py
async def analyze_scene(image_bytes: bytes) -> SceneAnalysis:
    """
    Sends image to Gemini Vision with structured output request.
    Streams thoughts to SSE for dashboard visibility.
    """
    prompt = """Analyze this sports image for brand sponsorship placement opportunities.

    Return JSON:
    {
      "scene_type": "athletic_action" | "celebration" | "training" | "lifestyle" | "ceremony",
      "mood": "triumph" | "intensity" | "joy" | "dedication" | "team_unity",
      "sport": "basketball" | "football" | ...,
      "athlete_visibility": {
        "face_clear": bool,
        "full_body": bool,
        "jersey_visible": bool,
        "footwear_visible": bool
      },
      "brand_zones": [
        {
          "zone_id": "footwear",
          "description": "Athlete's shoes visible mid-air",
          "tier": 3,
          "placement_type": "product_interaction",
          "feasibility": "high" | "medium" | "low",
          "natural_fit_score": 0-100
        }
      ],
      "categories": ["footwear", "sportswear", "hydration", ...],
      "pricing_guidance": {
        "tier_1_range": "$800-1200",
        "tier_2_range": "$2000-3000",
        "tier_3_range": "$4000-6000"
      },
      "creative_notes": "The upward motion and arena lighting create a heroic frame..."
    }
    """
```

### Step 3: Category-Based Matching

Instead of just sport + reach, matching now uses scene categories:
- Nike's profile says `categories: ["footwear", "sportswear"]` → matches
- Gatorade's profile says `categories: ["hydration"]` → matches (but conflict-blocked later)
- Campus Pizza says `categories: ["food"]` → no match for this scene

### Step 4: Demand Agent Evaluates (Multi-Step Reasoning, Streamed)

```python
# Each step is a focused Gemini call with thinking enabled
# Steps stream thoughts → SSE → dashboard

STEP 1: Context Gathering
"What's my budget status? Campaign goals? Recent deals?"
→ Thought: "Monthly budget: $38k remaining. Campaign: 'Just Do It March Madness'..."

STEP 2: Fit Assessment
[image + scene analysis + brand profile]
"Does this moment fit Nike's brand narrative?"
→ Thought: "Basketball dunk = peak athletic performance. Perfect 'Just Do It' material..."

STEP 3: Tier Selection
[brand zones from platform analysis]
"Which placement tier gives best ROI?"
→ Thought: "Tier 3 footwear — shoes visible mid-air, natural placement. Worth premium..."

STEP 4: Pricing Strategy
"What should I bid given tier, reach, and alternatives?"
→ Thought: "150k reach at Tier 3 = $0.03 CPM. Market rate $4-6k. Bid $4,500..."

STEP 5: Decision
→ Output: {bid: true, tier: 3, zone: "footwear", price: 4500, reasoning: "..."}
```

### Step 5: Supply Agent Evaluates (Streamed)

```python
STEP 1: Brand Vetting
"Is Nike good for my athlete's image?"
→ Thought: "Nike is premium, athlete-friendly brand. No conflicts..."

STEP 2: Creative Feasibility
[image + requested tier/zone]
"Can I produce natural Tier 3 content with this image?"
→ Thought: "Athlete's feet visible mid-air — shoe composite will look natural..."

STEP 3: Price Evaluation
"Is $4,500 fair for Tier 3?"
→ Thought: "Similar Tier 3 deals: $5-6k. Below market — counter..."

STEP 4: Decision
→ Output: {decision: "counter", counter_price: 5200, reasoning: "..."}
```

### Step 6: Negotiation (streamed back-and-forth)

Nike evaluates counter → accepts within budget → Deal agreed.

### Step 7: Platform Generates Branded Content (Gemini Image Gen)

```python
# content_generator.py
async def generate_branded_options(
    original_image: bytes,
    brand_assets: BrandAssets,  # logo, colors, guidelines
    tier: int,
    zone: str,
    instructions: str,
) -> list[GeneratedImage]:
    """Generate 2-3 branded image options."""

    prompt = f"""
    Generate a branded version of this sports image.
    
    Brand: {brand_assets.brand_name}
    Placement tier: {tier} ({zone})
    Instructions: {instructions}
    Brand colors: {brand_assets.colors}
    
    Requirements:
    - Maintain the energy and composition of the original
    - Brand placement must look natural, not photoshopped
    - Include brand logo/product in the specified zone
    - Keep athlete's face and expression unchanged
    """

    options = []
    for i in range(3):
        result = await gemini.generate_image(
            prompt=f"{prompt}\nVariation {i+1}: {'subtle' if i==0 else 'balanced' if i==1 else 'prominent'} brand presence",
            reference_images=[original_image, brand_assets.logo_bytes],
            aspect_ratio="16:9",
        )
        options.append(result)

    return options
```

### Step 8: Both Agents Review Generated Images

```
Platform → both agents: "3 branded options generated. Review and approve."
Nike agent: evaluates brand prominence, naturalness → approves Option 2
Pixology agent: evaluates athlete representation, quality → approves Option 2
Both approve same option → Deal CLOSED
```

---

## 5. Streaming Architecture (SSE Events)

### New Event Types

```typescript
// Agent thinking (streamed in chunks)
{
  event: "agent_thinking",
  data: {
    deal_id: "deal_47",
    agent_id: "agt_nike",
    agent_name: "Nike Basketball Agent",
    step: "fit_assessment",           // which reasoning step
    step_number: 2,
    total_steps: 5,
    thought: "Basketball dunk = peak...",  // chunk of thought text
    status: "thinking" | "decided"
  }
}

// Scene analysis complete
{
  event: "scene_analyzed",
  data: {
    deal_id: "deal_47",
    scene_analysis: { ... },          // full SceneAnalysis object
    brand_zones: [...],
    categories: [...],
    image_url: "/static/opportunities/opp_47.jpg"
  }
}

// Content options generated
{
  event: "content_generated",
  data: {
    deal_id: "deal_47",
    options: [
      {option_id: 1, image_url: "/static/generated/deal_47_opt1.png", style: "subtle"},
      {option_id: 2, image_url: "/static/generated/deal_47_opt2.png", style: "balanced"},
      {option_id: 3, image_url: "/static/generated/deal_47_opt3.png", style: "prominent"},
    ]
  }
}

// Agent reviews content
{
  event: "content_review",
  data: {
    deal_id: "deal_47",
    agent_id: "agt_nike",
    option_id: 2,
    decision: "approve",
    reasoning: "Brand presence is prominent but natural"
  }
}
```

---

## 6. Image Storage (Local, Phase 1)

```
server/static/
├── opportunities/          # Uploaded athlete images
│   ├── opp_001.jpg
│   └── opp_002.jpg
├── generated/              # Platform-generated branded content
│   ├── deal_001_opt1.png
│   ├── deal_001_opt2.png
│   └── deal_001_opt3.png
├── brand_assets/           # Brand logos and assets (pre-staged)
│   ├── nike_swoosh.png
│   ├── gatorade_logo.png
│   └── campus_pizza_logo.png
└── demo/                   # Pre-staged demo images
    ├── basketball_dunk.jpg
    ├── football_catch.jpg
    └── celebration.jpg
```

FastAPI serves these at `/static/{path}`.

---

## 7. Environment Variables

Add to `server/.env`:

```bash
# Gemini (all agent LLMs + vision + image gen)
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_VISION_MODEL=gemini-3-flash-preview
GEMINI_REASONING_MODEL=gemini-3-flash-preview
GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview

# Image storage
AAX_STATIC_DIR=static
```

---

## 8. Schema Changes

### New: `SceneAnalysis` (platform agent output)

```python
class BrandZone(BaseModel):
    zone_id: str                # "footwear", "jersey", "banner", etc.
    description: str
    tier: int                   # 1, 2, or 3
    placement_type: str         # "background", "scene_integration", "product_interaction"
    feasibility: str            # "high", "medium", "low"
    natural_fit_score: int      # 0-100

class SceneAnalysis(BaseModel):
    scene_type: str             # "athletic_action", "celebration", etc.
    mood: str
    sport: str
    athlete_visibility: dict
    brand_zones: list[BrandZone]
    categories: list[str]       # ["footwear", "hydration", ...]
    pricing_guidance: dict
    creative_notes: str

class PlacementOption(BaseModel):
    tier: int
    zone: BrandZone
    suggested_price_range: tuple[float, float]
```

### Updated: `OpportunitySignal`

```python
class OpportunitySignal(BaseModel):
    content_description: str
    image_id: str | None = None         # Reference to uploaded image
    subjects: list[SubjectInfo]
    audience: AudienceInfo
    available_formats: list[ContentFormat]
    min_price: float
    sport: str | None = None
    # NEW — populated by platform agent after scene analysis
    scene_analysis: SceneAnalysis | None = None
    placement_options: list[PlacementOption] | None = None
```

### Updated: `Proposal`

```python
class Proposal(BaseModel):
    deal_terms: DealTerms
    reasoning: str
    scores: dict | None = None
    # NEW
    selected_tier: int | None = None
    selected_zone: str | None = None    # Which brand zone they want
```

### New: `ContentOption`

```python
class ContentOption(BaseModel):
    option_id: int
    image_url: str
    style: str          # "subtle", "balanced", "prominent"
    description: str

class ContentReview(BaseModel):
    option_id: int
    decision: str       # "approve" | "reject" | "request_revision"
    reasoning: str
```

---

## 9. Agent Persona Redesign (Multi-Step Reasoning)

Each agent gets a rich system prompt that drives multi-step reasoning:

### Nike Demand Agent — System Prompt

```
You are Nike's autonomous sponsorship agent for college athletics.

## Your Identity
- Brand: Nike — "Just Do It"
- Tone: Bold, empowering, aspirational
- Budget: $5,000/deal, $50,000/month
- Campaign: March Madness 2026 — "Every Game is an Opportunity"
- Competitors: Adidas, Under Armour, New Balance (NEVER co-sponsor)

## Your Strategy
- Prioritize Tier 3 (product interaction) for basketball moments
- Prefer milestone/achievement moments over routine plays
- Bid aggressively on high-reach (>100k) basketball content
- Be selective on football — only championship/rivalry moments
- Walk away if Tier 3 pricing exceeds $6,000 (diminishing returns)

## Your Evaluation Framework
When evaluating an opportunity, think through:
1. BRAND FIT: Does this moment tell a "Just Do It" story?
2. AUDIENCE: Is the reach and demographic worth the spend?
3. TIER VALUE: Which placement tier maximizes brand impact?
4. PRICE: What's fair market value for this tier + reach combo?
5. TIMING: Is this moment still fresh? Will it be stale by delivery?

## Your Negotiation Style
- Open strong but leave room for counter
- Accept counters within 20% of your bid
- Never chase — if rejected, move on. More moments are coming.
- Prefer exclusivity (no other brands on same content)
```

### Pixology Supply Agent — System Prompt

```
You are Pixology's content creation agent — premium graphics for college athletes.

## Your Identity
- Service: Gameday graphics, social posts, highlight reels
- Quality: Broadcast-grade, NCAA-compliant
- Turnaround: 45 minutes for standard, 2 hours for premium composite
- Athletes: You protect their image and reputation above all

## Your Strategy
- Minimum price: $500 (below this, not worth the production effort)
- Tier 3 commands premium — compositing is expensive and time-sensitive
- Prefer repeat brand partners (Nike, Gatorade) — they know the drill
- Reject brands that could harm athlete's NIL value
- Counter aggressively on Tier 3 — brands need YOU more than you need them

## Your Evaluation Framework
When evaluating a proposal:
1. PRICE: Is it fair for the tier and production effort required?
2. BRAND SAFETY: Will this brand association help or hurt the athlete?
3. CREATIVE FEASIBILITY: Can I produce natural-looking content at this tier?
4. USAGE RIGHTS: How long do they want to use it? Shorter = better for you
5. TIMELINE: Can I deliver before the moment goes stale?

## Your Negotiation Style
- Never accept first offer on Tier 3 (always counter up)
- Accept first offer on Tier 1 if above minimum (low effort)
- Counter with specific reasoning (not just "I want more")
- Include creative feedback ("I can do Tier 3 but suggest X angle")
```

---

## 10. Dashboard UI Changes

### Deal Detail Page — Two-Column Thinking View

```
┌─────────────────────────────────────────────────────────────────┐
│  Deal #47 — MIT Basketball Dunk                                  │
│  Image: [thumbnail of athlete photo]                             │
│  Scene: athletic_action | Mood: triumph | Sport: basketball     │
│  Zones: footwear (T3), banner (T1), jersey (T2)                 │
├───────────────────────────────┬─────────────────────────────────┤
│  🔵 Nike Basketball Agent     │  🟠 Pixology Content Agent       │
│  ───────────────────────────  │  ─────────────────────────────── │
│                               │                                   │
│  ⟳ Step 2/5: Fit Assessment  │  ⏳ Awaiting proposal...          │
│                               │                                   │
│  💭 "Basketball dunk — peak   │                                   │
│      'Just Do It' moment.     │                                   │
│      The upward motion and    │                                   │
│      arena energy perfectly   │                                   │
│      capture athletic         │                                   │
│      aspiration..."           │                                   │
│                               │                                   │
│  [thinking animation ···]     │                                   │
│                               │                                   │
├───────────────────────────────┴─────────────────────────────────┤
│  🤖 Platform Agent — Scene Analysis                              │
│  ┌────────┐ ┌────────┐ ┌────────┐                               │
│  │Zone: T1│ │Zone: T2│ │Zone: T3│                               │
│  │Banner  │ │Jersey  │ │Shoes   │                               │
│  │$800-1.2k│ │$2-3k  │ │$4-6k   │                               │
│  └────────┘ └────────┘ └────────┘                               │
├─────────────────────────────────────────────────────────────────┤
│  Generated Options (after deal agreed)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                           │
│  │ Option 1│ │ Option 2│ │ Option 3│                           │
│  │ Subtle  │ │Balanced │ │Prominent│                           │
│  │         │ │  ✓ ✓   │ │         │                           │
│  │         │ │Nike Pix │ │         │                           │
│  └─────────┘ └─────────┘ └─────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Implementation Phases

### Phase A: Gemini Adaptor + Scene Analysis (foundation)
- `server/src/gemini/adaptor.py` — Python Gemini client
- `server/src/gemini/scene_analyzer.py` — Image analysis
- Image upload endpoint + local storage
- Update opportunity signal flow to include image
- SSE event: `scene_analyzed`

### Phase B: Streamed Agent Reasoning
- Replace single-call Claude evaluation with multi-step Gemini reasoning
- Each step streams thoughts via SSE (`agent_thinking` events)
- Rich system prompts with brand personas
- Dashboard thinking UI component

### Phase C: Image Generation + Review
- `server/src/gemini/content_generator.py`
- Generate 2-3 branded options after deal agreement
- Image review endpoint (both agents approve/reject)
- Dashboard image gallery component

### Phase D: Polish + Demo
- 3-5 pre-staged demo scenarios with curated images
- Timing optimizations
- End-to-end demo script
- Error handling and fallbacks

---

## 12. Demo Scenarios (Pre-Staged)

### Scenario 1: "The Milestone Dunk"
- Image: Basketball player mid-air dunk (MIT arena)
- Categories: footwear, sportswear
- Expected winner: Nike (Tier 3 footwear)
- Demonstrates: Full negotiation + image generation

### Scenario 2: "Victory Celebration"
- Image: Team celebrating, locker room
- Categories: hydration, casual wear, food
- Expected: Gatorade bids but gets CONFLICT BLOCKED
- Demonstrates: Conflict engine + alternative winner

### Scenario 3: "Training Grind"
- Image: Athlete in weight room
- Categories: supplements, sportswear, wearables
- Expected: Nike (Tier 2) + Campus Pizza passes (wrong category)
- Demonstrates: Category filtering, tier selection

---

## 13. Dependencies

Add to `pyproject.toml`:
```toml
"google-genai>=1.0",       # Gemini Python SDK
"pillow>=11.0",            # Image processing
"aiofiles>=24.1",          # Async file I/O for image storage
```

Remove (no longer needed for agents):
```toml
# Keep anthropic for now (might use for fallback) but agents switch to Gemini
```
