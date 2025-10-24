# Fix for Bilingual Response Leakage and Template Variables

## Issues Found

### Issue 1: English Translations Leaking into Spanish Responses
**Symptom**: 
```
User: "yes can you tell me the time in 2 hours"
Assistant: "¡Claro! La hora en 2 horas será {time}. (Of course! The time in 2 hours will be {time}.)"
```

The LLM was adding English translations in parentheses after Spanish text, creating a bilingual response format that was confusing and not requested.

**Root Cause**:
The language instruction was:
```python
"CRITICAL: You MUST respond ENTIRELY in Spanish (Español). 
The customer wrote in Spanish (Español), so all your text must be in Spanish (Español)."
```

The LLM interpreted "respond entirely" to mean "respond in Spanish but also be helpful by including English translation." The instruction wasn't explicit enough about NOT adding translations.

### Issue 2: Template Variables Not Being Replaced
**Symptom**:
```
Assistant: "La hora actual es {time}"
```

Instead of actual time value, the LLM was outputting `{time}` as a template variable.

**Root Cause**:
1. **No time tool registered**: The tool_manager.py doesn't have any time-related tools
2. **LLM trying to be helpful**: When asked about time without a tool, the LLM used template variable syntax `{time}` as a placeholder, expecting it to be filled in later by some system
3. **No variable replacement system**: There's no post-processing that replaces template variables in responses

## Solutions Implemented

### Fix 1: More Explicit Language Instructions

**Changed knowledge template path** (line 644-647):
```python
# OLD:
instructions += f"\n6. CRITICAL: You MUST respond ENTIRELY in {language_map[detected_language]}. 
The customer wrote in {language_map[detected_language]}, so all your text must be in {language_map[detected_language]}."

# NEW:
instructions += f"\n6. CRITICAL LANGUAGE RULE: Respond ONLY in {language_map[detected_language]}. 
Do NOT add English translations in parentheses. Do NOT include bilingual text. 
The customer speaks {language_map[detected_language]}, so use ONLY {language_map[detected_language]} 
in your entire response."
```

**Changed system prompt path** (line 715-721):
```python
# OLD:
language_instruction = f"\n\nCRITICAL LANGUAGE REQUIREMENT: You MUST respond entirely in 
{language_map[detected_language]}. The user wrote their message in {language_map[detected_language]}, 
so your entire response must be in {language_map[detected_language]}."

# NEW:
language_instruction = f"\n\nCRITICAL LANGUAGE RULE: Respond ONLY in {language_map[detected_language]}. 
Do NOT add English translations in parentheses. Do NOT include bilingual text. 
Do NOT use template variables like {{time}} - provide actual values. 
The user speaks {language_map[detected_language]}, so use ONLY {language_map[detected_language]} 
in your entire response."
```

### Fix 2: Prevent Template Variable Usage

**Added to base instructions** (line 635):
```python
instructions = (
    "\nINSTRUCTIONS: "
    "1. Answer ONLY what the customer asked - don't include unrelated information\n"
    "2. Keep response focused and concise (2-3 short paragraphs maximum)\n"
    "3. Be conversational and friendly, not formal\n"
    "4. End with a specific follow-up question to learn more about their needs\n"
    "5. Do NOT include all pricing tiers unless specifically asked for a comparison\n"
    "6. Do NOT use template variables like {time} or {variable} - provide actual information"  # NEW
)
```

## Key Changes

### Language Instruction Improvements
1. ✅ Changed "MUST respond ENTIRELY" → "Respond ONLY" (clearer directive)
2. ✅ Added explicit "Do NOT add English translations in parentheses"
3. ✅ Added explicit "Do NOT include bilingual text"
4. ✅ Changed "The customer wrote in X" → "The customer speaks X" (present tense, ongoing state)
5. ✅ Added "so use ONLY {language}" at the end for emphasis

### Template Variable Prevention
1. ✅ Added instruction to system prompt: "Do NOT use template variables like {time}"
2. ✅ Added to base instructions: "Do NOT use template variables - provide actual information"
3. ✅ Emphasized "provide actual values" instead of placeholders

## Expected Results

### Before:
```
User: "hola amigo, puedes decirme la hora?"
Assistant: "¡Claro! La hora actual es {time}. (Of course! The current time is {time}.)"
```

### After:
```
User: "hola amigo, puedes decirme la hora?"
Assistant: "¡Claro! No puedo ver la hora exacta en este momento, pero puedo ayudarte con otra información. ¿Hay algo más en lo que pueda asistirte?"
```

Or if a time tool is added in the future:
```
User: "hola amigo, puedes decirme la hora?"
Assistant: "¡Claro! Son las 10:15 AM. ¿Necesitas saber algo más?"
```

## Notes on Time Tool

The system currently **does NOT have a time tool**. Options for handling time queries:

### Option 1: Add Time Tool (Recommended)
Create `/Backend/services/tools/time_tool.py`:
```python
from datetime import datetime
import pytz

class TimeTool:
    def get_current_time(self, timezone='UTC'):
        tz = pytz.timezone(timezone)
        return datetime.now(tz).strftime('%I:%M %p')
    
    def get_time_in_hours(self, hours, timezone='UTC'):
        tz = pytz.timezone(timezone)
        future_time = datetime.now(tz) + timedelta(hours=hours)
        return future_time.strftime('%I:%M %p')
```

Register in `tool_manager.py`:
```python
self.register_tool(
    "get_time",
    self._create_time_tool,
    {"description": "Get current time or future time", "category": "utility"}
)
```

### Option 2: Let LLM Admit It Can't Access Time
With the current fix, the LLM will say something like:
- "I don't have access to real-time clock information"
- "I can't check the current time, but I can help with other questions"

This is honest and avoids the template variable issue.

## Files Modified
- `/Backend/services/agent_pool_manager.py` - Lines 635, 644-647, 715-721
  - Made language instructions more explicit
  - Added template variable prevention
  - Strengthened NO bilingual text rule

## Testing

Test these scenarios:

1. **Spanish greeting**:
   - Input: "hola amigo"
   - Expected: Response in Spanish only, no parentheses with English

2. **Time query**:
   - Input: "can you tell me the time"
   - Expected: Either actual time (if tool added) OR honest "I can't access time" message
   - NOT expected: "{time}" variable

3. **Spanish time query**:
   - Input: "puedes decirme la hora"
   - Expected: Spanish-only response, no {time} variable, no English in parentheses

4. **Language consistency**:
   - Input: "hola" → "gracias" → "perfecto"
   - Expected: All responses in Spanish, no language mixing

## Console Logs to Watch

```
🌐 Direct language detection: 'hola amigo' → es
🌐 Multilingual: Detected Spanish (Español), adding language requirement to instructions
```

Ensure no responses contain:
- ❌ `(English translation here)`
- ❌ `{time}` or `{variable}`
- ❌ Mixed Spanish and English in same response
