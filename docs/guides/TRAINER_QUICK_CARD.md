# 🎯 AI Trainer Quick Reference Card
### Keep this open while training

---

## ⚡ Speed Training Commands

### Add Training Example (Fastest Method):
```bash
curl -X POST http://localhost:8080/api/v1/ai/train \
  -H "Content-Type: application/json" \
  -d '[{
    "input": "YOUR_QUESTION_HERE",
    "output": "YOUR_RESPONSE_HERE",
    "category": "medical|product|education"
  }]'
```

### Check Current Accuracy:
```bash
curl http://localhost:8080/api/v1/training/accuracy | jq '.accuracy'
```

### Test AI Response:
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "YOUR_TEST_QUERY", "customer_id": "test"}'
```

---

## 🎨 Training Templates

### Template 1: Medical Query
```
Input: [SYMPTOM/CONDITION]
Output: I understand you're dealing with [CONDITION]. Here are my recommendations:
• [PRODUCT_1] - $[PRICE] - [BENEFIT]
• [PRODUCT_2] - $[PRICE] - [BENEFIT]
Start with [DOSAGE]. Most customers see results in [TIME].
Would you prefer [FORMAT_1] or [FORMAT_2]?
Intent: medical_[condition]
```

### Template 2: Product Search
```
Input: [PRODUCT_REQUEST]
Output: Great choice! For [NEED], I recommend:
• [PRODUCT_NAME] - $[PRICE]/[SIZE] - [KEY_FEATURE]
• [ALTERNATIVE] - $[PRICE]/[SIZE] - [KEY_FEATURE]
[PRODUCT_NAME] is our bestseller because [REASON].
Want to see it in person or should I set one aside?
Intent: product_search
```

### Template 3: Price Objection
```
Input: That's too expensive / Anything cheaper?
Output: Absolutely, let me show you our value options:
• [BUDGET_OPTION_1] - $[LOWER_PRICE] - Still [QUALITY_POINT]
• [BUNDLE_DEAL] - Save $[SAVINGS] when you buy [QUANTITY]
• [ALTERNATIVE_FORMAT] - $[PRICE] - Same effects, different format
Which fits your budget better?
Intent: price_objection
```

### Template 4: Dosage Guidance
```
Input: How much should I take?
Output: Let's start safely:
[FORMAT]:
• Beginner: [LOW_DOSE] - Wait [TIME]
• Regular: [MEDIUM_DOSE] - Wait [TIME]
• Experienced: [HIGH_DOSE]
Golden rule: Start low, go slow. You can always take more, never less.
Using [FORMAT]? Start with [SPECIFIC_DOSE].
Intent: dosage_guidance
```

---

## 🔥 Power Phrases That Convert

### Opening Hooks:
- "Perfect timing - we just got..."
- "Based on what you're describing..."
- "I've helped dozens of customers with exactly this..."
- "Great question! Here's what works best..."

### Trust Builders:
- "Our customers report..."
- "In my experience..."
- "The science shows..."
- "Most people find..."

### Urgency Creators:
- "We've only got 3 left..."
- "This batch is particularly good..."
- "Today only..."
- "While supplies last..."

### Soft Closes:
- "Want me to set one aside?"
- "Should I add this to your order?"
- "Ready to try it?"
- "Which option sounds better?"

---

## 📊 Quality Checklist

Before applying training, each example should:
- [ ] Include specific product names
- [ ] Mention prices
- [ ] Have a follow-up question
- [ ] Match the personality tone
- [ ] Be under 150 words
- [ ] Include an alternative option
- [ ] Address the core need

---

## 🎮 Personality Shortcuts

### The Expert
```
Traits: Professional, Educational, Detailed
Phrases: "The terpene profile...", "Studies indicate...", "Pharmacologically speaking..."
```

### The Friend
```
Traits: Casual, Warm, Encouraging
Phrases: "Honestly...", "Between you and me...", "You're gonna love this..."
```

### The Guide
```
Traits: Patient, Thorough, Safety-focused
Phrases: "Let's start with...", "Step by step...", "The safe approach is..."
```

### The Enthusiast
```
Traits: Energetic, Passionate, Fun
Phrases: "Oh man!", "This stuff is fire!", "You HAVE to try..."
```

---

## 🚨 Must-Train Scenarios

Priority order - train these first:

1. **"I'm new"** - Beginner guidance
2. **"Something for sleep"** - Medical/sleep
3. **"Cheapest option"** - Budget conscious
4. **"Strongest you have"** - Potency seeker
5. **"Won't make me paranoid"** - Anxiety concern
6. **"How much?"** - Dosage question
7. **"Is this legal?"** - Compliance
8. **"I took too much"** - Safety response
9. **"Do you deliver?"** - Service info
10. **"What's the difference?"** - Education

---

## 📈 Accuracy Targets by Training Count

- 10 examples: 40% accuracy
- 25 examples: 55% accuracy
- 50 examples: 70% accuracy
- 100 examples: 80% accuracy
- 200+ examples: 85-90% accuracy

**Goal:** 50 quality examples > 200 mediocre ones

---

## 🔄 The Training Loop

1. **Test** current response
2. **Write** better response
3. **Train** with example
4. **Apply** training
5. **Verify** improvement
6. **Repeat** for each scenario

**Time per example:** 2-3 minutes
**Examples per hour:** 20-30
**Hours to expertise:** 2-3

---

## 💡 Debug Common Issues

### Problem: Generic responses
**Fix:** Add more specific product details in training

### Problem: Too salesy
**Fix:** Adjust personality empathy level higher

### Problem: Slow responses
**Fix:** Reduce Max Tokens to 100

### Problem: Forgetting context
**Fix:** Increase Context Window to 15

### Problem: Wrong products
**Fix:** Train with exact product names from inventory

---

## 🎯 Success Metrics

### You're winning when:
- Response time: <3 seconds ✅
- Includes prices: >80% of responses ✅
- Asks follow-up: >90% of responses ✅
- Specific products: >70% of responses ✅
- Handles objections: Smoothly ✅
- Maintains personality: Consistently ✅

---

## 🚀 Advanced Techniques

### Chain Training:
Link related examples:
- General → Specific → Purchase → Upsell

### Variant Training:
Same intent, different phrasings:
- "I can't sleep"
- "Insomnia issues"
- "Need something for bedtime"
- "Help me sleep"

### Context Training:
Include conversation history:
```
Previous: "I have back pain"
Input: "But I don't want to get high"
Output: "Perfect! For pain without the high, try our CBD options..."
```

---

## 📞 Emergency Contacts

### System Issues:
- API Down: Check `python api_server.py`
- UI Issues: Check `npm run dev`
- Database: Check PostgreSQL connection

### Training Issues:
- Low accuracy: Add more diverse examples
- Wrong answers: Check for conflicting training
- Slow learning: Increase training batch size

---

**Remember:** Every conversation is a training opportunity. Save the good ones, fix the bad ones.

**The AI gets smarter with every example you feed it.** 🧠

---

*Keep training. Keep testing. Keep improving.*