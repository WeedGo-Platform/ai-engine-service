# AI Personality Management - UI/UX Mockup

## Feature Overview

Allow tenant admins to manage their AI budtender personalities based on subscription tier limits.

### Subscription Tier Limits

| Tier | Default Personalities | Custom Personalities | Total Available |
|------|----------------------|---------------------|----------------|
| **Free** | 3 (marcel, shante, zac) | 0 | 3 |
| **Small Business** | 3 | +2 custom | 5 |
| **Professional** | 3 | +3 custom | 6 |
| **Enterprise** | 3 | +5 custom | 8 |

### Access Control

- ✅ **Super Admin**: Full access (view all, edit all, create unlimited)
- ✅ **Tenant Admin**: Limited access (view own, edit own, create within tier limits)
- ❌ **Store Manager / Staff**: No access

---

## UI Layout

### 1. New Tab in AI Configuration Page

**Location**: `/dashboard/ai` → New "Personalities" tab

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 AI Engine Management                                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┬──────────────┬───────────┬──────────────┐     │
│  │ Models  │ Configuration│ Inference │ Personalities│ ← NEW │
│  └─────────┴──────────────┴───────────┴──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Main Personalities Tab View

### Header Section

```
┌────────────────────────────────────────────────────────────────────┐
│  👤 Budtender Personalities                                        │
│                                                                    │
│  Configure your AI budtender personalities. Each personality has  │
│  unique traits, communication styles, and responses.              │
│                                                                    │
│  📊 Your Plan: Small Business (2 of 2 custom slots used)         │
│  🆙 Upgrade to Professional for 3 more personalities              │
│                                                                    │
│  ┌──────────────────────────────────────┐                        │
│  │ [+] Create New Personality           │ ← Disabled if at limit │
│  └──────────────────────────────────────┘                        │
└────────────────────────────────────────────────────────────────────┘
```

### Personalities Grid View

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  Default Personalities (Provided by WeedGo)                       │
│  ─────────────────────────────────────────────────────────────── │
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐│
│  │ 🔥 Marcel        │  │ 💜 Shanté        │  │ 😎 Zac           ││
│  │                  │  │                  │  │                  ││
│  │ Energetic &      │  │ Knowledgeable &  │  │ Chill & Laid-back││
│  │ Enthusiastic     │  │ Sophisticated    │  │                  ││
│  │                  │  │                  │  │                  ││
│  │ Age: 25, Male    │  │ Age: 30, Female  │  │ Age: 28, Male    ││
│  │ Humor: High      │  │ Humor: Medium    │  │ Humor: Low       ││
│  │ Sales: Consult.  │  │ Sales: Educational│ │ Sales: Relaxed   ││
│  │                  │  │                  │  │                  ││
│  │ ☑️ Active        │  │ ☐ Inactive       │  │ ☑️ Active        ││
│  │                  │  │                  │  │                  ││
│  │ [👁 View]        │  │ [👁 View]        │  │ [👁 View]        ││
│  │ [Toggle Active]  │  │ [Toggle Active]  │  │ [Toggle Active]  ││
│  └──────────────────┘  └──────────────────┘  └──────────────────┘│
│                                                                    │
│  Custom Personalities (Created by Your Team)                      │
│  ─────────────────────────────────────────────────────────────── │
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │ 🌿 Jade          │  │ ⚡ Alex           │                      │
│  │                  │  │                  │                      │
│  │ Medical-focused  │  │ Fast & Efficient │                      │
│  │ Expert           │  │ Transaction-based│                      │
│  │                  │  │                  │                      │
│  │ Age: 35, Female  │  │ Age: 24, Non-bin │                      │
│  │ Humor: Low       │  │ Humor: Medium    │                      │
│  │ Sales: Medical   │  │ Sales: Quick     │                      │
│  │                  │  │                  │                      │
│  │ ☑️ Active        │  │ ☐ Inactive       │                      │
│  │                  │  │                  │                      │
│  │ [✏️ Edit]        │  │ [✏️ Edit]        │                      │
│  │ [🗑️ Delete]     │  │ [🗑️ Delete]     │                      │
│  └──────────────────┘  └──────────────────┘                      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  [+] Add Another Personality                              │   │
│  │      (0 of 2 remaining slots)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. View Default Personality Modal (Read-Only)

**Trigger**: Click "View" on marcel, shanté, or zac

```
┌────────────────────────────────────────────────────────────────────┐
│  🔥 Marcel - Default Personality                          [✕ Close]│
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ℹ️  Default personalities are provided by WeedGo and cannot be   │
│     edited. You can activate/deactivate them for your stores.     │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Basic Information                                          │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  Name:        Marcel                                        │  │
│  │  Emoji:       🔥                                            │  │
│  │  Role:        Budtender                                     │  │
│  │  Description: Your energetic cannabis guide who brings      │  │
│  │               enthusiasm to every interaction               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Personality Traits                                         │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  Age:                  25                                   │  │
│  │  Gender:               Male                                 │  │
│  │  Communication Style:  Energetic and enthusiastic           │  │
│  │  Knowledge Level:      Expert                               │  │
│  │  Humor Style:          Witty and playful                    │  │
│  │  Humor Level:          High                                 │  │
│  │  Empathy Level:        Medium                               │  │
│  │  Response Length:      Medium                               │  │
│  │  Jargon Level:         Moderate                             │  │
│  │  Sales Approach:       Consultative                         │  │
│  │  Formality:            Casual                               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Sample Conversation Style                                  │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  Opening Phrases:                                           │  │
│  │  • "Yo! Welcome! What's bringing you in today?"            │  │
│  │  • "Hey hey! Ready to find something amazing?"             │  │
│  │  • "What's up! Looking for some fire today?"               │  │
│  │                                                             │  │
│  │  Product Transitions:                                       │  │
│  │  • "Oh man, I've got the perfect thing for you!"          │  │
│  │  • "Dude, you're gonna love this..."                       │  │
│  │                                                             │  │
│  │  Closing Phrases:                                           │  │
│  │  • "Awesome choice! You're gonna love it!"                 │  │
│  │  • "Hit me up if you need anything else!"                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  [📋 Copy as Template]  [✕ Close]                          │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Read-only view of default personality configuration
- "Copy as Template" button to create a custom personality based on this one
- Cannot edit default personalities directly

---

## 4. Create/Edit Custom Personality Form

**Trigger**: Click "+Create New Personality" or "Edit" on custom personality

```
┌────────────────────────────────────────────────────────────────────┐
│  ✏️ Create New Personality                                [✕ Close]│
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  🎭 Basic Information                                       │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  Personality Name *                                         │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Jade                                                 │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  Emoji (optional)                                           │  │
│  │  ┌──────┐                                                  │  │
│  │  │ 🌿   │ [Choose Emoji]                                  │  │
│  │  └──────┘                                                  │  │
│  │                                                             │  │
│  │  Description *                                              │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Medical-focused cannabis expert who specializes in  │  │  │
│  │  │ helping patients find therapeutic products...        │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  🎭 Personality Traits                                      │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  Age *            Gender *                                  │  │
│  │  ┌──────────┐    ┌──────────────────────┐                 │  │
│  │  │ 35       │    │ Female        [▼]    │                 │  │
│  │  └──────────┘    └──────────────────────┘                 │  │
│  │                   Options: Male, Female, Non-binary, Other │  │
│  │                                                             │  │
│  │  Communication Style *                                      │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Professional and empathetic        [▼]              │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  Presets: Energetic, Professional, Casual, Medical,       │  │
│  │           Friendly, Educational                            │  │
│  │                                                             │  │
│  │  Knowledge Level *      Sales Approach *                   │  │
│  │  ┌─────────────────┐   ┌─────────────────┐               │  │
│  │  │ Expert    [▼]   │   │ Medical   [▼]   │               │  │
│  │  └─────────────────┘   └─────────────────┘               │  │
│  │                                                             │  │
│  │  ─────────────────────────────────────────────────────── │  │
│  │                                                             │  │
│  │  Humor Level              ●────────○────────○  Medium      │  │
│  │                           Low    Medium    High             │  │
│  │                                                             │  │
│  │  Empathy Level            ○────────○────────●  High        │  │
│  │                           Low    Medium    High             │  │
│  │                                                             │  │
│  │  Formality                ●────────○────────○  Professional│  │
│  │                           Casual  Friendly Professional    │  │
│  │                                                             │  │
│  │  Response Length          ○────────●────────○  Medium      │  │
│  │                           Short  Medium    Long             │  │
│  │                                                             │  │
│  │  Jargon Level             ○────────●────────○  Moderate    │  │
│  │                           Low   Moderate   High             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  💬 Conversation Style                                      │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  Greeting Phrases (3-5 examples) *                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 1. Hello, how can I help you today?                 │  │  │
│  │  │ 2. Welcome! Are you looking for something specific?│  │  │
│  │  │ 3. Hi there! I'm here to help you find the right   │  │  │
│  │  │    products...                                       │  │  │
│  │  │ [+ Add Another]                                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  Product Transitions (3-5 examples)                        │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 1. Let me show you something that might help...     │  │  │
│  │  │ 2. Based on your needs, I recommend...              │  │  │
│  │  │ [+ Add Another]                                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  Closing Phrases (3-5 examples)                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ 1. Feel free to reach out if you have questions...  │  │  │
│  │  │ 2. Thank you for choosing us today!                 │  │  │
│  │  │ [+ Add Another]                                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  🎤 Advanced Settings (Optional)                            │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  Custom System Prompt                                       │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ You are Jade, a medical cannabis expert. Your goal │  │  │
│  │  │ is to help patients find therapeutic relief through│  │  │
│  │  │ cannabis products. Always prioritize patient needs  │  │  │
│  │  │ and medical considerations...                        │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  ⚠️  Advanced: Only modify if you know what you're doing   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  💡 AI Preview                                              │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  [Test Personality] ← Opens chat to test before saving     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                             │  │
│  │  ☐ Set as active immediately                               │  │
│  │                                                             │  │
│  │  [Cancel]  [Save Personality]                              │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 5. Tier Limit Warning Modal

**Trigger**: Click "+Create New Personality" when at tier limit

```
┌────────────────────────────────────────────────────────┐
│  ⚠️  Personality Limit Reached                [✕ Close]│
├────────────────────────────────────────────────────────┤
│                                                        │
│  You've reached the maximum number of personalities   │
│  for your Small Business plan.                        │
│                                                        │
│  Current Usage: 2 of 2 custom personalities           │
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │  Upgrade to Professional for:                    ││
│  │  • 3 additional custom personalities             ││
│  │  • Advanced AI features                          ││
│  │  • Priority support                              ││
│  │                                                   ││
│  │  Or: Enterprise for up to 5 custom personalities ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │  💡 You can still edit or replace existing       ││
│  │     personalities within your limit              ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  [View Plans]  [Maybe Later]                          │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 6. Delete Confirmation Modal

**Trigger**: Click "Delete" on custom personality

```
┌────────────────────────────────────────────────────────┐
│  🗑️  Delete Personality?                      [✕ Close]│
├────────────────────────────────────────────────────────┤
│                                                        │
│  Are you sure you want to delete "Jade"?              │
│                                                        │
│  ⚠️  This action cannot be undone.                     │
│                                                        │
│  ┌──────────────────────────────────────────────────┐│
│  │  📊 Impact:                                      ││
│  │  • 3 active conversations will be reassigned     ││
│  │    to default personality (Marcel)               ││
│  │  • Conversation history will be preserved        ││
│  │  • This frees up 1 personality slot              ││
│  └──────────────────────────────────────────────────┘│
│                                                        │
│  [Cancel]  [Delete Permanently]                       │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 7. Mobile Responsive View

```
┌──────────────────────────────┐
│ 👤 Personalities             │
│                              │
│ Your Plan: Small Business    │
│ 2 of 2 custom slots used     │
│                              │
│ [+] Create New (Disabled)    │
│                              │
│ ─── Default ───              │
│                              │
│ ┌──────────────────────────┐│
│ │ 🔥 Marcel                ││
│ │ Energetic & Enthusiastic ││
│ │ ☑️ Active                ││
│ │ [View Details ▼]         ││
│ └──────────────────────────┘│
│                              │
│ ┌──────────────────────────┐│
│ │ 💜 Shanté                ││
│ │ Knowledgeable & Sophist. ││
│ │ ☐ Inactive               ││
│ │ [View Details ▼]         ││
│ └──────────────────────────┘│
│                              │
│ ─── Custom ───               │
│                              │
│ ┌──────────────────────────┐│
│ │ 🌿 Jade                  ││
│ │ Medical-focused Expert   ││
│ │ ☑️ Active                ││
│ │ [Edit] [Delete]          ││
│ └──────────────────────────┘│
│                              │
└──────────────────────────────┘
```

---

## 8. Success/Error States

### Success Toast
```
┌───────────────────────────────────────────┐
│ ✅ Success!                               │
│ Personality "Jade" created successfully   │
│ [Dismiss]                                 │
└───────────────────────────────────────────┘
```

### Error Toast
```
┌───────────────────────────────────────────┐
│ ❌ Error                                  │
│ Failed to save personality: Name already  │
│ exists. Please choose a different name.   │
│ [Dismiss]                                 │
└───────────────────────────────────────────┘
```

### Loading State
```
┌──────────────────┐
│ 🔄 Saving...     │
└──────────────────┘
```

---

## Feature Specifications

### Validation Rules

1. **Personality Name**:
   - Required, 3-50 characters
   - Alphanumeric + spaces allowed
   - Must be unique within tenant
   - Cannot use reserved names (marcel, shante, zac)

2. **Description**:
   - Required, 20-500 characters
   - Plain text only

3. **Greeting/Product/Closing Phrases**:
   - Minimum 3, maximum 5 phrases each
   - Each phrase: 10-200 characters
   - At least one required in each category

4. **System Prompt**:
   - Optional, max 2000 characters
   - Only visible to admins
   - Auto-generated if left empty

### Personality Activation Logic

1. **Default personalities**: Can be activated/deactivated by tenant
2. **Custom personalities**: Automatically active when created (unless unchecked)
3. **At least 1 personality must be active** at all times
4. **Active personality** can be selected in chat sessions/cart sessions

### Data Storage

**ai_personalities table fields:**
```sql
- id (uuid)
- tenant_id (uuid) ← Links to tenant
- store_id (uuid) ← Optional: Null for tenant-level
- name (varchar) ← Display name
- personality_name (varchar) ← Internal ID (auto-generated from name)
- personality_type (varchar) ← 'default' or 'custom'
- is_default (boolean) ← True for marcel/shante/zac
- is_active (boolean) ← Can be toggled
- traits (jsonb) ← All personality traits
- response_style (jsonb) ← Conversation phrases
- system_prompt (text) ← Custom system prompt
- greeting_message (text) ← Legacy, can deprecate
- voice_config (jsonb) ← For future voice features
- avatar_url (varchar) ← Future: Profile picture
- created_at, updated_at
```

**tenants.settings (JSONB) addition:**
```json
{
  "ai_personalities": {
    "active_default_ids": ["marcel", "zac"],
    "custom_count": 2,
    "primary_personality_id": "uuid-of-jade"
  }
}
```

### API Endpoints Needed

```
GET    /api/admin/ai-personalities          List all (filtered by tenant)
POST   /api/admin/ai-personalities          Create new custom personality
GET    /api/admin/ai-personalities/:id      Get single personality
PUT    /api/admin/ai-personalities/:id      Update custom personality
DELETE /api/admin/ai-personalities/:id      Delete custom personality
PATCH  /api/admin/ai-personalities/:id/toggle  Toggle active status

GET    /api/admin/ai-personalities/default   List 3 default personalities
GET    /api/admin/ai-personalities/limits    Get tier limits for current tenant
```

### Access Control Logic

**Super Admin**:
- Can see all personalities across all tenants
- Can edit any personality (default or custom)
- No tier limits
- Can force-activate/deactivate

**Tenant Admin**:
- Can only see/edit personalities for their tenant
- Cannot edit default personalities (can only view/toggle)
- Subject to tier limits
- Can CRUD custom personalities within limits

---

## User Flows

### Flow 1: Free Tier User Selects Default Personality

1. Navigate to AI Configuration → Personalities
2. See 3 default personalities (marcel, shante, zac)
3. Click "View" on Shanté → View read-only details
4. Click "Toggle Active" to activate Shanté
5. Success toast: "Shanté is now active"
6. See upgrade prompt: "Want to create custom personalities? Upgrade to Small Business"

### Flow 2: Small Business Tier Creates Custom Personality

1. Navigate to AI Configuration → Personalities
2. See "2 of 2 custom slots used" badge
3. Click "+Create New Personality" (available)
4. Fill out form with Jade's details
5. Use sliders for humor/empathy/formality levels
6. Add 3 greeting phrases
7. Click "Test Personality" → Opens preview chat
8. Test a few messages, satisfied with responses
9. Click "Save Personality"
10. Success: "Personality 'Jade' created successfully"
11. Jade appears in custom personalities grid
12. Badge now shows "2 of 2 custom slots used"

### Flow 3: Professional Tier User Hits Limit

1. User has 3 custom personalities (at Professional limit)
2. Clicks "+Create New Personality"
3. Modal appears: "Personality Limit Reached"
4. Options: "Upgrade to Enterprise" or "Maybe Later"
5. User clicks "View Plans"
6. Redirected to billing page with Enterprise highlighted

### Flow 4: Tenant Admin Deletes Unused Personality

1. Navigate to custom personalities section
2. Find "Alex" personality (inactive, 0 conversations)
3. Click "Delete"
4. Confirmation modal: "Are you sure?"
5. Shows impact: "0 conversations will be affected"
6. Click "Delete Permanently"
7. Success: "Personality deleted. You now have 1 available slot"
8. Badge updates to "1 of 2 custom slots used"

---

## Technical Implementation Notes

### Database Seeding

Seed 3 default personalities on initial migration:
```sql
INSERT INTO ai_personalities (
  id, tenant_id, name, personality_name, personality_type,
  is_default, is_active, traits, response_style, system_prompt
)
VALUES
  (uuid, NULL, 'Marcel', 'marcel', 'default', true, true, {...}, {...}, '...'),
  (uuid, NULL, 'Shanté', 'shante', 'default', true, true, {...}, {...}, '...'),
  (uuid, NULL, 'Zac', 'zac', 'default', true, true, {...}, {...}, '...');
```

### Tier Limit Enforcement

Middleware check on personality creation:
```python
def check_personality_limit(tenant_id):
    tenant = get_tenant(tenant_id)
    tier = tenant.subscription_tier

    limits = {
        'free': 0,
        'small_business': 2,
        'professional': 3,
        'enterprise': 5
    }

    custom_count = count_custom_personalities(tenant_id)

    if custom_count >= limits.get(tier, 0):
        raise HTTPException(403, "Personality limit reached for tier")
```

### Default Personality Handling

- Default personalities have `is_default=true` and `tenant_id=NULL`
- When tenant activates a default, create a tenant-specific reference in `tenants.settings`
- Do NOT duplicate default personalities per tenant
- Just track which defaults are active in tenant settings

---

## Open Questions for Approval

1. **Should store managers see this tab?** (Currently: No, only super admin & tenant admin)
2. **Should each store have different personalities?** (Currently: Tenant-level only)
3. **Should there be a "primary" personality** that's used by default in new conversations?
4. **Test Personality feature**: Should it be a mini chat interface or just show sample phrases?
5. **Copy as Template**: Should copying a default personality count against the custom limit?
6. **Avatar/Profile Picture**: Should we include avatar upload in V1, or save for later?
7. **Voice Config**: Should we expose voice settings (pitch, speed) in V1?

---

## Design System Consistency

### Colors (Dark Mode)
- Background: `bg-gray-800`
- Cards: `bg-gray-900/50`
- Borders: `border-gray-700`
- Text: `text-gray-300` (body), `text-white` (headers)
- Primary Action: `bg-indigo-600 hover:bg-indigo-700`
- Danger Action: `bg-red-600 hover:bg-red-700`
- Success: `bg-green-600`
- Warning: `bg-yellow-600`

### Typography
- Headers: `text-2xl font-bold`
- Subheaders: `text-lg font-semibold`
- Body: `text-sm`
- Labels: `text-sm font-medium`

### Spacing
- Card padding: `p-6`
- Form spacing: `space-y-4`
- Grid gap: `gap-4`

### Icons (Lucide React)
- User2 (personality)
- Plus (create)
- Pencil (edit)
- Trash2 (delete)
- Eye (view)
- Check (active)
- X (inactive)
- AlertCircle (warning)
- Info (info)

---

## Next Steps After Approval

1. ✅ **Get user approval on mockup**
2. Create database migration for default personalities
3. Build backend API endpoints
4. Implement frontend Personalities tab component
5. Add access control middleware
6. Add tier limit enforcement
7. Write unit tests
8. Manual QA testing
9. Deploy to production

---

**Status**: 📋 **AWAITING APPROVAL** - Do not proceed with implementation until user reviews and approves this mockup.
