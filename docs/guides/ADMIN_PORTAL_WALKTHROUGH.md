# 🚀 WeedGo AI Admin Portal - Complete Walkthrough Guide

## Access the Portal
Open your browser and navigate to: **http://localhost:5174/**

---

## 1. 📊 **Dashboard Overview**

When you first load the portal, you'll see the Dashboard with:

### Key Metrics (Top Row)
- **AI Accuracy**: Current model accuracy percentage
- **Examples Trained**: Total training examples in the system
- **Unique Patterns**: Number of unique cannabis terms mapped
- **Queries Today**: Number of user interactions today

### Quick Actions (Middle)
- 🧠 **Train AI**: Quick access to training hub
- 💬 **Test Query**: Jump to chat testing
- 📊 **View Reports**: Analytics dashboard
- 🚀 **Deploy Model**: Model deployment interface

### Live Feeds (Bottom)
- **Recent Activity**: Real-time system events
- **System Health**: Status of all services

---

## 2. 🎓 **Training Hub - Train Your AI Model**

Navigate to the **Unified Training Hub** tab.

### How to Upload Training Data:

1. **Click "Upload Dataset"** button
2. **Choose dataset type**:
   - **Conversation Examples**: User queries and expected responses
   - **Product Knowledge**: Cannabis product information
   - **Medical Training**: Medical conditions and recommendations

3. **Upload Format** (JSON):
```json
{
  "examples": [
    {
      "input": "I need something for sleep",
      "output": "I recommend our Indica strains like Purple Kush",
      "intent": "medical_sleep"
    }
  ]
}
```

4. **Or Create Manually**:
   - Click "Add Example"
   - Enter user query
   - Enter expected response
   - Select intent category
   - Click Save

5. **Apply Training**:
   - After adding examples, click **"Apply Training"**
   - Monitor progress in the progress bar
   - Check accuracy improvements

---

## 3. ⚙️ **AI Configuration**

### Skip Words Management
- **Purpose**: Exclude common words from product search
- **Add Skip Word**: Enter word, select category, click Add
- **Toggle Active/Inactive**: Click toggle switch
- **Categories**: conversational, question, request, polite, etc.

### Medical Intents
- **View intents**: See all medical conditions mapped
- **Add keywords**: Associate new terms with medical conditions
- **Example**: "insomnia" → sleep_issues intent

### System Parameters
- **Temperature**: Controls AI creativity (0.1-1.0)
- **Max Tokens**: Response length limit
- **Context Window**: Memory size for conversations
- **Update**: Change value and click Save

---

## 4. 🎭 **AI Personality Management**

### Create a New Personality:

1. Click **"Create New Personality"**
2. Fill in details:
   - **Name**: e.g., "Chill Buddy"
   - **Age**: e.g., "28"
   - **Traits**: Friendly, Knowledgeable, Casual
   - **Communication Style**: Casual, uses slang
   - **Humor Level**: Light/Moderate/High
   - **Sample Responses**: 
     - Greeting: "Hey there! What's good?"
     - Product Rec: "Yo, this strain is fire for what you need"

3. Click **Save Personality**
4. Click **Activate** to use this personality

---

## 5. 💬 **Live Chat Testing**

### Test Your AI:

1. Go to **Unified Chat Testing** tab
2. Select a budtender personality (top dropdown)
3. Type test queries:
   - "I need help sleeping"
   - "Show me sativa strains under $50"
   - "What's good for anxiety?"
4. View AI responses with:
   - Product recommendations
   - Confidence scores
   - Response times

### Advanced Testing:
- **Switch Personalities**: Test different AI personas
- **View History**: See past conversations
- **Export Sessions**: Download chat logs for analysis

---

## 6. 📈 **Analytics Dashboard**

Monitor performance metrics:

### Key Metrics:
- **Conversation Volume**: Daily chat trends
- **Intent Distribution**: Most common user requests
- **Popular Products**: Most requested items
- **Response Times**: System performance
- **Customer Satisfaction**: Rating distribution
- **Conversion Funnel**: From greeting to purchase

### Time Ranges:
- Today
- Last 7 days
- Last 30 days
- Custom range

---

## 7. 📚 **Cannabis Knowledge Base**

Manage domain knowledge:

### Strains Database:
- View all cannabis strains
- Add new strains with effects/terpenes
- Edit existing strain information
- Search and filter strains

### Terpene Profiles:
- Manage terpene information
- Define effects and flavors
- Associate with strains

### Medical Conditions:
- Map conditions to recommended products
- Add symptom keywords
- Define dosing guidelines

---

## 8. 👁️ **AI Soul Window**

Real-time AI monitoring:

### What You'll See:
- **Thought Stream**: AI's reasoning process
- **Context Factors**: What influences decisions
- **Decision Paths**: Alternative responses considered
- **Confidence Levels**: How certain the AI is
- **Current Intent**: What the AI thinks user wants

### Use Cases:
- Debug unexpected responses
- Understand AI decision-making
- Optimize prompts and training

---

## 9. 🔧 **Service Manager**

Monitor system health:

### Services:
- **AI Engine**: Model status and memory usage
- **Database**: Connection and query performance  
- **Cache**: Hit rates and memory usage
- **API Gateway**: Request handling

### Actions:
- View logs for each service
- Restart services if needed
- Scale services up/down
- Monitor resource usage

---

## 10. 🚀 **Model Deployment**

Deploy trained models:

### Steps:
1. Go to **Model Deployment** tab
2. View available model versions
3. Select model to deploy
4. Choose environment:
   - Development
   - Staging
   - Production
5. Click **Deploy**
6. Monitor deployment status

---

## 💡 **Pro Tips**

### Training Best Practices:
1. **Start small**: Add 10-20 examples first
2. **Test frequently**: Use chat testing after each training
3. **Balance intents**: Ensure all categories have examples
4. **Use real data**: Train with actual customer queries

### Performance Optimization:
1. **Monitor cache hit rate**: Should be >80%
2. **Watch response times**: Target <3 seconds
3. **Check error logs**: Address issues quickly
4. **Regular training**: Update weekly with new data

### Common Tasks:

**Add a new product response**:
1. Training Hub → Add Example
2. Input: "Do you have Blue Dream?"
3. Output: "Yes! Blue Dream is a popular sativa-dominant hybrid..."
4. Intent: product_inquiry
5. Apply Training

**Fix incorrect response**:
1. Find the incorrect pattern in Training Hub
2. Edit the example
3. Apply Training
4. Test in Chat

**Improve response quality**:
1. AI Configuration → System Parameters
2. Increase Temperature for more creative responses
3. Increase Max Tokens for longer responses
4. Save changes

---

## 🆘 **Troubleshooting**

### If chat responses are slow:
- Check Service Manager → AI Engine status
- Clear cache: Admin → Clear Cache
- Reduce Max Tokens in configuration

### If training isn't improving accuracy:
- Add more diverse examples
- Check for conflicting intents
- Review skip words configuration

### If services show offline:
- Check Service Manager logs
- Restart service using restart button
- Verify database connection

---

## 📞 **Need Help?**

- **Documentation**: Check README.md files
- **API Docs**: http://localhost:8080/docs
- **Logs**: Service Manager → View Logs
- **Test Suite**: Run `python test_admin_integration.py`

---

**The admin portal is your complete control center for the AI budtender. Train it, configure it, and monitor it all from one place!**