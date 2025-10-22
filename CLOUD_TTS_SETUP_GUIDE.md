# Cloud TTS Provider Setup Guide

**Purpose:** Configure free-tier cloud Text-to-Speech providers as backup for local voice synthesis

**Date:** 2025-10-20

---

## Overview

The WeedGo voice system supports multiple cloud TTS providers as fallback options when local voice cloning models (XTTS v2, StyleTTS2) are unavailable or when high-quality multi-language support is needed without voice cloning.

### Supported Cloud Providers

| Provider | Free Tier | Languages | Voices | Quality | Setup Time |
|----------|-----------|-----------|--------|---------|------------|
| **Google Cloud TTS** | 1M chars/month | 100+ | 500+ | High | 10 min |
| **Azure TTS** | 0.5M chars/month | 75+ | 400+ | High | 10 min |
| **IBM Watson TTS** | 10k chars/month | 20+ | 50+ | High | 15 min |

---

## Google Cloud Text-to-Speech Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `weedgo-tts` (or your choice)
4. Click "Create"

### Step 2: Enable Text-to-Speech API

1. In the Google Cloud Console, navigate to "APIs & Services" → "Library"
2. Search for "Cloud Text-to-Speech API"
3. Click on it and press "Enable"

### Step 3: Create Service Account

1. Navigate to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Enter:
   - **Name:** `weedgo-tts-service`
   - **Description:** "Service account for WeedGo voice synthesis"
4. Click "Create and Continue"
5. **Role:** Select "Cloud Text-to-Speech API User"
6. Click "Continue" → "Done"

### Step 4: Generate API Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create"
6. The JSON key file will download automatically
7. **Save this file securely** (e.g., `/path/to/weedgo-tts-credentials.json`)

### Step 5: Configure Environment Variable

**Local Development:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/weedgo-tts-credentials.json"
```

**Production (Docker):**
```dockerfile
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-tts.json
```

**Production (Kubernetes):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: google-tts-credentials
type: Opaque
data:
  credentials.json: <base64-encoded-json-key>
---
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: ai-engine
    env:
    - name: GOOGLE_APPLICATION_CREDENTIALS
      value: /secrets/google-tts/credentials.json
    volumeMounts:
    - name: google-tts-secret
      mountPath: /secrets/google-tts
      readOnly: true
  volumes:
  - name: google-tts-secret
    secret:
      secretName: google-tts-credentials
```

### Step 6: Test Google TTS

```python
from core.voice.google_tts_handler import GoogleTTSHandler

# Initialize handler
handler = GoogleTTSHandler()
await handler.initialize()

# Synthesize speech
result = await handler.synthesize(
    text="Welcome to WeedGo!",
    language="en-US",
    voice="en-US-Neural2-C"
)

# result.audio contains WAV bytes
```

### Popular Google TTS Voices

| Voice ID | Language | Gender | Quality |
|----------|----------|--------|---------|
| en-US-Neural2-C | English (US) | Female | Neural2 |
| en-US-Neural2-D | English (US) | Male | Neural2 |
| en-GB-Neural2-A | English (UK) | Female | Neural2 |
| es-ES-Neural2-A | Spanish (Spain) | Female | Neural2 |
| fr-FR-Neural2-A | French | Female | Neural2 |
| de-DE-Neural2-A | German | Female | Neural2 |

**Full voice list:** [Google TTS Voice Gallery](https://cloud.google.com/text-to-speech/docs/voices)

---

## Azure Cognitive Services Speech Setup

### Step 1: Create Azure Account

1. Go to [Azure Portal](https://portal.azure.com/)
2. Sign in or create a free account (requires credit card but won't charge)

### Step 2: Create Speech Service Resource

1. Click "Create a resource"
2. Search for "Speech" and select "Speech"
3. Click "Create"
4. Fill in details:
   - **Subscription:** Your subscription
   - **Resource Group:** Create new → `weedgo-resources`
   - **Region:** Choose closest to your users (e.g., `West US 2`)
   - **Name:** `weedgo-speech`
   - **Pricing tier:** `Free F0` (500k characters/month)
5. Click "Review + create" → "Create"

### Step 3: Get API Key

1. Go to the resource you just created
2. In the left menu, click "Keys and Endpoint"
3. Copy **KEY 1** and **REGION**
4. Save these securely

### Step 4: Configure Environment Variables

**Local Development:**
```bash
export AZURE_SPEECH_KEY="your-key-here"
export AZURE_SPEECH_REGION="westus2"  # Your region
```

**Production (Docker):**
```dockerfile
ENV AZURE_SPEECH_KEY=your-key-here
ENV AZURE_SPEECH_REGION=westus2
```

### Step 5: Test Azure TTS

```python
from core.voice.azure_tts_handler import AzureTTSHandler

# Initialize handler
handler = AzureTTSHandler(
    subscription_key=os.environ['AZURE_SPEECH_KEY'],
    region=os.environ['AZURE_SPEECH_REGION']
)
await handler.initialize()

# Synthesize speech
result = await handler.synthesize(
    text="Welcome to WeedGo!",
    language="en-US",
    voice="en-US-JennyNeural"
)
```

### Popular Azure TTS Voices

| Voice ID | Language | Gender | Quality |
|----------|----------|--------|---------|
| en-US-JennyNeural | English (US) | Female | Neural |
| en-US-GuyNeural | English (US) | Male | Neural |
| en-GB-SoniaNeural | English (UK) | Female | Neural |
| es-ES-ElviraNeural | Spanish (Spain) | Female | Neural |
| fr-FR-DeniseNeural | French | Female | Neural |

**Full voice list:** [Azure TTS Voice Gallery](https://speech.microsoft.com/portal/voicegallery)

---

## IBM Watson Text-to-Speech Setup

### Step 1: Create IBM Cloud Account

1. Go to [IBM Cloud](https://cloud.ibm.com/)
2. Sign up for free account (no credit card required for lite plan)

### Step 2: Create Text-to-Speech Service

1. Click "Catalog"
2. Search for "Text to Speech"
3. Click on "Text to Speech"
4. Select:
   - **Pricing Plan:** `Lite` (10k characters/month)
   - **Service name:** `weedgo-tts`
   - **Resource group:** Default
5. Click "Create"

### Step 3: Get API Credentials

1. Go to the service you just created
2. Click "Service credentials" in the left menu
3. Click "New credential"
4. Name it `weedgo-credentials`
5. Click "Add"
6. Click "View credentials"
7. Copy **apikey** and **url**
8. Save these securely

### Step 4: Configure Environment Variables

**Local Development:**
```bash
export IBM_WATSON_API_KEY="your-api-key-here"
export IBM_WATSON_URL="https://api.us-south.text-to-speech.watson.cloud.ibm.com"
```

**Production (Docker):**
```dockerfile
ENV IBM_WATSON_API_KEY=your-api-key-here
ENV IBM_WATSON_URL=https://api.us-south.text-to-speech.watson.cloud.ibm.com
```

### Step 5: Test IBM Watson TTS

```python
from core.voice.ibm_watson_handler import IBMWatsonHandler

# Initialize handler
handler = IBMWatsonHandler(
    api_key=os.environ['IBM_WATSON_API_KEY'],
    url=os.environ['IBM_WATSON_URL']
)
await handler.initialize()

# Synthesize speech
result = await handler.synthesize(
    text="Welcome to WeedGo!",
    language="en-US",
    voice="en-US_AllisonV3Voice"
)
```

### Popular IBM Watson Voices

| Voice ID | Language | Gender | Quality |
|----------|----------|--------|---------|
| en-US_AllisonV3Voice | English (US) | Female | Neural |
| en-US_MichaelV3Voice | English (US) | Male | Neural |
| en-GB_KateV3Voice | English (UK) | Female | Neural |
| es-ES_LauraV3Voice | Spanish (Spain) | Female | Neural |
| fr-FR_ReneeV3Voice | French | Female | Neural |

**Full voice list:** [IBM Watson Voice Gallery](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-voices)

---

## Cost Management

### Free Tier Limits (Monthly)

| Provider | Free Tier | Overage Cost | Reset | Monitoring |
|----------|-----------|--------------|-------|------------|
| Google TTS | 1,000,000 chars | $4.00 per 1M chars | Monthly | Cloud Console Billing |
| Azure Speech | 500,000 chars | $1.00 per 1K chars | Monthly | Azure Cost Management |
| IBM Watson | 10,000 chars | $0.02 per 1K chars | Monthly | IBM Cloud Usage Dashboard |

### Usage Estimates

**Average text lengths:**
- Short response (1 sentence): ~50 characters
- Medium response (2-3 sentences): ~150 characters
- Long response (paragraph): ~500 characters

**Monthly usage scenarios:**

| Scenario | Responses/Day | Chars/Day | Chars/Month | Fits Free Tier? |
|----------|---------------|-----------|-------------|-----------------|
| Low traffic | 100 | 15,000 | 450,000 | ✅ All providers |
| Medium traffic | 500 | 75,000 | 2,250,000 | ✅ Google only |
| High traffic | 2,000 | 300,000 | 9,000,000 | ❌ Need multiple |

### Cost Optimization Strategies

1. **Local-First Architecture** (Current Implementation)
   - Use XTTS v2/StyleTTS2/Piper for most synthesis
   - Cloud providers only as fallback
   - **Estimated savings:** 90-95%

2. **Response Caching** (Planned)
   - Cache generated audio in Redis (24h TTL)
   - Common phrases pre-generated
   - **Estimated savings:** 70-80%

3. **Multi-Provider Rotation**
   - Distribute load across Google/Azure/IBM
   - Stay within all free tiers
   - **Monthly capacity:** 1.5M+ characters free

4. **Smart Fallback Chain**
   ```
   Local (Free) → Google (1M free) → Azure (500K free) → IBM (10K free)
   ```

---

## Security Best Practices

### Credential Management

1. **Never commit credentials to git**
   ```gitignore
   # .gitignore
   **/credentials.json
   **/*-credentials.json
   .env
   ```

2. **Use environment variables**
   - Development: `.env` file (gitignored)
   - Production: Kubernetes Secrets or AWS Secrets Manager

3. **Rotate keys regularly**
   - Google: Regenerate service account keys every 90 days
   - Azure: Regenerate keys every 180 days
   - IBM: API keys don't expire but should be rotated annually

4. **Principle of least privilege**
   - Google: Only grant "Cloud Text-to-Speech API User" role
   - Azure: Only Speech Service permissions
   - IBM: Only Text to Speech access

### Firewall & IP Restrictions

**Google Cloud:**
```bash
# Restrict API key to specific IPs
gcloud services api-keys update KEY_ID \
  --allowed-ips="YOUR_PRODUCTION_IP"
```

**Azure:**
- Use Azure Private Link for VNet restriction
- Enable Azure AD authentication instead of API keys

**IBM:**
- Use IAM policies to restrict access by IP
- Enable Cloud IAM for more granular control

---

## Monitoring & Alerts

### Google Cloud Monitoring

1. Go to Cloud Console → "Monitoring" → "Metrics Explorer"
2. Add metric: `Cloud Text-to-Speech API → Character count`
3. Set alert when approaching 900,000 characters/month

### Azure Monitoring

1. Go to Speech resource → "Metrics"
2. Add metric: `TotalCalls` or `Characters`
3. Set alert at 450,000 characters/month

### IBM Cloud Monitoring

1. Go to Text to Speech service → "Usage"
2. View current month usage
3. Set email alerts in Account Settings

---

## Troubleshooting

### Google TTS

**Error:** `Could not automatically determine credentials`
```bash
# Check environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Verify file exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Test credentials manually
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
```

**Error:** `Insufficient permissions`
- Verify service account has "Cloud Text-to-Speech API User" role
- Ensure API is enabled in project

### Azure TTS

**Error:** `Unauthorized: Invalid subscription key`
```bash
# Verify key is correct
echo $AZURE_SPEECH_KEY

# Test with curl
curl -X POST "https://$AZURE_SPEECH_REGION.tts.speech.microsoft.com/cognitiveservices/v1" \
  -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY"
```

**Error:** `429 Too Many Requests`
- You've exceeded free tier limits
- Wait until next billing cycle or upgrade to paid tier

### IBM Watson

**Error:** `Unauthorized`
```bash
# Verify API key
echo $IBM_WATSON_API_KEY

# Test with curl
curl -X GET "$IBM_WATSON_URL/v1/voices" \
  -u "apikey:$IBM_WATSON_API_KEY"
```

**Error:** `Service instance not found`
- Verify URL matches your service region
- Check service is not deleted in IBM Cloud dashboard

---

## Integration with VoiceModelRouter

### Automatic Initialization

The `VoiceModelRouter` automatically detects available cloud providers based on environment variables:

```python
# VoiceModelRouter initialization
router = VoiceModelRouter(device="cpu")
await router.initialize()

# Checks for:
# - GOOGLE_APPLICATION_CREDENTIALS → Loads Google TTS
# - AZURE_SPEECH_KEY + AZURE_SPEECH_REGION → Loads Azure TTS
# - IBM_WATSON_API_KEY + IBM_WATSON_URL → Loads IBM Watson
```

### Fallback Chain Configuration

```python
from core.voice.voice_model_router import VoiceQuality

# HIGH quality uses cloud as backup
context = SynthesisContext(
    quality=VoiceQuality.HIGH  # Tries: XTTS v2 → StyleTTS2 → Google → Azure
)

result = await router.synthesize(text, context)
```

---

## Next Steps

1. **Choose a provider** (Recommendation: Google TTS for best free tier)
2. **Set up credentials** following the guide above
3. **Configure environment variables** in your deployment
4. **Test synthesis** with the voice router
5. **Monitor usage** to stay within free tier

**Priority:** Set up Google Cloud TTS first (largest free tier, best quality)

---

**Created:** 2025-10-20
**Status:** Production-ready
**Maintainer:** WeedGo Engineering Team
