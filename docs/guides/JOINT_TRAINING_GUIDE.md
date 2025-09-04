# 🎯 Joint Recognition Training Guide

## Teaching the AI: "Joint" = 1g Pre-Roll

### Overview
This guide provides step-by-step instructions for training the AI to understand that when customers ask for a "joint", they're looking for 1g pre-rolls. The AI will learn to:
- Recognize "joint" and related slang terms
- Return only 1g pre-rolls (not other sizes)
- Provide plant type breakdown (Indica, Sativa, Hybrid)
- Offer smart quick actions for sales conversion

---

## 📊 Current System State

### Database Structure
```sql
-- Products table contains pre-rolls with these key fields:
sub_category: 'Pre-Rolls'
size: '1x1g' or '1g'  -- These are joints!
plant_type: 'Indica Dominant', 'Sativa Dominant', 'Hybrid', 'Blend'
```

### Current Inventory (as of training):
- **Total 1g joints:** 160 products
- **Indica Dominant:** 72 products ($3.25-$11.08)
- **Sativa Dominant:** 48 products ($3.25-$10.12)
- **Hybrid:** 37 products ($3.65-$10.87)
- **Blend:** 3 products ($3.76-$7.59)

---

## 🚀 Step-by-Step Training Instructions

### Step 1: Prepare the Training Script

1. **Save the training script** as `train_joint_recognition_v2.py`
2. **Ensure API is running** at `http://localhost:8080`
3. **Verify database connection** (port 5434, database: ai_engine)

### Step 2: Run the Training Script

```bash
python train_joint_recognition_v2.py
```

**Expected Output:**
```
🚀 Joint Recognition Training Module V2
============================================================
Teaching AI: 'joint' = 1g pre-roll
============================================================

📊 Fetching current joint inventory stats...

📈 Current Inventory:
   Total 1g joints: 160
   • Indica Dominant: 72 products ($3.25-$11.08)
   • Sativa Dominant: 48 products ($3.25-$10.12)
   • Hybrid: 37 products ($3.65-$10.87)
   • Blend: 3 products ($3.76-$7.59)

📚 Adding training examples to database...
============================================================
✅ Added: give me a joint...
✅ Added: I want a joint...
[... 25 more examples ...]

📊 Training Summary:
   ✅ Successful: 27
   ❌ Failed: 0
   📈 Success Rate: 100.0%
```

### Step 3: Test in Chat Interface

1. **Open the chat interface:**
   ```bash
   open http://localhost:5174/
   ```

2. **Test these queries:**

   **Basic Joint Request:**
   ```
   User: "give me a joint"
   
   Expected AI Response:
   "I have 160 pre-rolled joints (1g) available:
   
   • Indica Dominant: 72 options | Sativa Dominant: 48 options | 
     Hybrid: 37 options | Blend: 3 options
   • Price range: $3.25 - $11.08
   
   What type are you looking for?"
   
   Quick Actions:
   [Show indica joints] [Show sativa joints] [Filter by price] [High THC options]
   ```

   **Plant Type Specific:**
   ```
   User: "show me indica joints"
   
   Expected AI Response:
   "I have 72 Indica Dominant pre-rolled joints (1g) available:
   
   • Price range: $3.25 - $11.08
   • Average price: $6.45
   
   Would you like to:
   - See specific brands
   - Filter by THC content
   - View customer favorites
   - Check current deals"
   ```

   **Price-Based Query:**
   ```
   User: "what's your cheapest joint"
   
   Expected AI Response:
   "Our most affordable joints start at $3.25. These are quality 
   1g pre-rolls at great prices. Interested in seeing what's available?"
   ```

   **Slang Recognition:**
   ```
   User: "got any j's"
   
   Expected AI Response:
   [Same as basic joint request - AI understands slang]
   ```

### Step 4: Verify in Decision Tree Visualizer

1. **Navigate to:** http://localhost:5174/unified-training
2. **Click on** "AI Decision Tree Visualizer"
3. **Enter query:** "give me a joint"
4. **Click** "Analyze"

**Expected Visualization:**
- **Intent Detection:** product_inquiry (100% confidence)
- **Entities Extracted:** 
  - product_type: "joint"
  - sub_category: "Pre-Rolls"
  - size: "1g"
- **Product Search:** Triggered with correct criteria
- **Response Generation:** Includes count, plant types, price range

---

## 📋 Training Examples Added

### Categories of Training:

1. **Basic Queries (10 examples)**
   - "give me a joint"
   - "I want a joint"
   - "show me joints"
   - etc.

2. **Plant Type Specific (9 examples)**
   - "give me an indica joint"
   - "show me sativa joints"
   - "I want hybrid pre-rolls"

3. **Price-Based (3 examples)**
   - "show me cheap joints"
   - "what's your cheapest joint"
   - "show me premium joints"

4. **Slang Variations (5 examples)**
   - "got any j's" → joints
   - "need a doobie" → joints
   - "looking for a fatty" → joints
   - "got any pre-rolls" → joints

---

## ✅ Success Criteria

The training is successful when:

1. **Query Recognition:** AI correctly identifies "joint" queries as product inquiries
2. **Product Filtering:** Returns ONLY 1g pre-rolls (size='1x1g' or '1g')
3. **Plant Type Grouping:** Shows breakdown by Indica/Sativa/Hybrid
4. **Price Information:** Includes price ranges in response
5. **Quick Actions:** Generates relevant follow-up options
6. **Slang Understanding:** Recognizes common slang terms

---

## 🔧 Troubleshooting

### Issue: Training fails with 500 errors
**Solution:** 
- Check API is running: `curl http://localhost:8080/health`
- Verify database connection
- Restart API server if needed

### Issue: AI not returning correct products
**Solution:**
- Verify training was successful (27/27 examples added)
- Apply training: `curl -X POST http://localhost:8080/api/v1/training/apply`
- Clear AI cache if needed

### Issue: No quick actions appearing
**Solution:**
- Check that metadata includes quick_actions array
- Verify frontend is parsing response correctly
- Check browser console for errors

---

## 📊 Expected Results

After successful training:

1. **Accuracy:** 95%+ for joint recognition
2. **Response Time:** < 2 seconds
3. **Product Match:** 100% returning 1g pre-rolls only
4. **Plant Type Accuracy:** Correct counts for each type
5. **Price Range:** Accurate min/max from database

---

## 🎯 Next Steps

1. **Monitor Performance:**
   - Track conversion rates on joint queries
   - Monitor which quick actions users click
   - Analyze follow-up questions

2. **Continuous Improvement:**
   - Add more slang variations as discovered
   - Refine response templates based on sales data
   - Add seasonal/promotional responses

3. **Expand Training:**
   - Train for multi-packs (3x0.5g, 5x0.5g)
   - Add brand-specific training
   - Include THC preference handling

---

## 📝 Notes

- Training data is saved to `joint_training_v2_[timestamp].json`
- All examples are stored in the `training_examples` table
- The AI uses these examples to improve its understanding over time
- Quick actions should drive sales by offering relevant filters

---

## 🚦 Verification Checklist

- [ ] Training script runs without errors
- [ ] 27 examples successfully added to database
- [ ] "give me a joint" returns 1g pre-rolls
- [ ] Plant type breakdown is accurate
- [ ] Price range matches database
- [ ] Quick actions appear in chat
- [ ] Decision tree visualizer shows correct intent
- [ ] Slang terms are recognized
- [ ] Response includes sales-oriented language

---

*Last Updated: August 26, 2024*
*Training Version: V2*
*Author: AI Training Module*