# Missing Translation Keys - Action Required

## Summary
The console showed errors for two missing translation keys. These need to be added to all language files.

## Keys to Add

### 1. Navigation Back Button
**Location:** `tenant.navigation.back`  
**Parent object:** `navigation` (already exists)

Add after `createAccount`:
```json
"back": "<translation>"
```

### 2. City Placeholder
**Location:** `tenant.contactInfo.cityPlaceholder`  
**Parent object:** `contactInfo` (already exists)

Add after `city`:
```json
"cityPlaceholder": "<translation for 'e.g., Toronto'>",
```

## Completed Languages
✅ English (en) - "Back" / "e.g., Toronto"
✅ French (fr) - "Retour" / "par ex., Toronto"
✅ Spanish (es) - "Atrás" / "ej., Toronto"
✅ Chinese (zh) - "返回" / "例如,多伦多"
✅ Hindi (hi) - "वापस" / "उदा., टोरंटो"
✅ Arabic (ar) - "عودة" / (needs cityPlaceholder)
✅ Punjabi (pa) - "ਵਾਪਸ" / (needs cityPlaceholder)
✅ Urdu (ur) - "واپس" / (needs cityPlaceholder)
✅ German (de) - "Zurück" / (needs cityPlaceholder)

## Remaining Languages (Need Both Keys)

| Code | Language | navigation.back | contactInfo.cityPlaceholder |
|------|----------|-----------------|------------------------------|
| pt | Portuguese | "Voltar" | "ex., Toronto" |
| bn | Bengali | "ফিরে যান" | "উদা., টরন্টো" |
| cr | Cree | "kîwêhtahk" | "nîsta, Toronto" |
| fa | Farsi | "بازگشت" | "مثلاً، تورنتو" |
| gu | Gujarati | "પાછા" | "દા.ત., ટોરોન્ટો" |
| he | Hebrew | "חזרה" | "לדוגמה, טורונטו" |
| it | Italian | "Indietro" | "es., Toronto" |
| iu | Inuktitut | "ᐅᑎᕐᓂᖅ" | "ᓲᕐᓗ, ᑐᕉᓐᑐ" |
| ja | Japanese | "戻る" | "例：トロント" |
| ko | Korean | "뒤로" | "예: 토론토" |
| nl | Dutch | "Terug" | "bijv., Toronto" |
| pl | Polish | "Wstecz" | "np., Toronto" |
| ro | Romanian | "Înapoi" | "de ex., Toronto" |
| ru | Russian | "Назад" | "напр., Торонто" |
| so | Somali | "Dib u noqo" | "tusaale, Toronto" |
| ta | Tamil | "மீண்டும்" | "உதா., டொராண்டோ" |
| tl | Tagalog | "Bumalik" | "hal., Toronto" |
| uk | Ukrainian | "Назад" | "напр., Торонто" |
| vi | Vietnamese | "Quay lại" | "ví dụ, Toronto" |
| yue | Cantonese | "返回" | "例如，多倫多" |

## Partial Completions (Need cityPlaceholder Only)

| Code | Language | contactInfo.cityPlaceholder |
|------|----------|-----------------------------|
| ar | Arabic | "على سبيل المثال، تورنتو" |
| pa | Punjabi | "ਉਦਾ., ਟੋਰਾਂਟੋ" |
| ur | Urdu | "مثلاً، ٹورنٹو" |
| de | German | "z.B., Toronto" |

## How to Apply

For each language file in `src/Frontend/ai-admin-dashboard/src/i18n/locales/{lang}/signup.json`:

1. **Add navigation.back:**
   ```json
   "navigation": {
     "previous": "...",
     "next": "...",
     "createAccount": "...",
     "back": "<translation from table above>"  // ← ADD THIS
   },
   ```

2. **Add contactInfo.cityPlaceholder:**
   ```json
   "contactInfo": {
     ...
     "city": "...",
     "cityPlaceholder": "<translation from table above>",  // ← ADD THIS
     "province": "...",
     ...
   }
   ```

## Quick Command to Add (Example for Portuguese)

```bash
# Replace in pt/signup.json navigation section
# Find: "createAccount": "Criar conta"
# After: Add: "back": "Voltar"

# Replace in pt/signup.json contactInfo section
# Find: "city": "Cidade",
# After: Add: "cityPlaceholder": "ex., Toronto",
```
