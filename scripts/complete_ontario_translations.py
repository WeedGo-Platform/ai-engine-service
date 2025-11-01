#!/usr/bin/env python3
"""Complete Ontario licensing translations for remaining 7 languages"""

import json
import os

# Ontario section translations for all 7 remaining languages
ONTARIO_TRANSLATIONS = {
    "ar": {  # Arabic (RTL)
        "title": "ترخيص القنب في أونتاريو",
        "description": "مطلوب لتجار تجزئة القنب في أونتاريو. CROL هو ترخيص التشغيل على مستوى المستأجر، CRSA هو تصريح التجزئة على مستوى المتجر.",
        "crolLabel": "رقم CROL (ترخيص تشغيل تجارة القنب بالتجزئة) *",
        "crolPlaceholder": "أدخل رقم CROL الخاص بـ OCS",
        "crolHelpText": "رقم ترخيص التشغيل من OCS على مستوى المستأجر",
        "crsaTitle": "التحقق من CRSA (تصريح متجر بيع القنب بالتجزئة)",
        "domainVerifiedSuccess": "✓ تم التحقق من النطاق - نطاق بريدك الإلكتروني يتطابق مع موقع CRSA. سيتم إنشاء متجرك الأول تلقائيًا من هذا الترخيص.",
        "licenseLabel": "رقم ترخيص بيع القنب بالتجزئة في أونتاريو",
        "licensePlaceholder": "مثال: LCBO-1234",
        "validating": "جارٍ التحقق...",
        "validate": "تحقق",
        "licenseHelpText": "أدخل رقم ترخيص بيع القنب بالتجزئة في أونتاريو من AGCO",
        "validatedSuccess": "✓ تم التحقق من الترخيص بنجاح",
        "storeNameLabel": "اسم المتجر:",
        "municipalityLabel": "البلدية:",
        "addressLabel": "العنوان:",
        "websiteLabel": "الموقع الإلكتروني:",
        "validationFailed": "فشل التحقق",
        "searchIntro": "لا تعرف رقم ترخيصك؟ ابحث عن متجرك:",
        "searchPlaceholder": "ابحث باسم المتجر أو العنوان",
        "searching": "جارٍ البحث...",
        "noResults": "لم يتم العثور على نتائج",
        "selectStore": "حدد متجرك من القائمة أدناه:",
        "needHelp": "تحتاج مساعدة؟",
        "helpDetails": "يمكنك العثور على أرقام ترخيصك في:",
        "helpCrol": "• رقم CROL: بوابة OCS B2B الخاصة بك (مطلوب لإنشاء المستأجر)",
        "helpCrsa": "• رقم CRSA: قاعدة بيانات ترخيص AGCO العامة (اختياري - للتحقق التلقائي من المتجر)",
        "helpNote": "ملاحظة: يمكنك تخطي التحقق من CRSA وإضافة المتاجر يدويًا لاحقًا."
    },
    "cr": {  # Cree
        "title": "Ontario ê-pê-oyôhkêmakan askîhkâna",
        "description": "nitawihtamihk Ontario askîhkâna atâwêwikamikohk. CROL kîsi-oyôhkêmakan, CRSA kîsi-atâwêwin-oyôhkêmakan.",
        "crolLabel": "CROL ayamihâwin (Cannabis Retail Operating License) *",
        "crolPlaceholder": "kîkway ki OCS CROL ayamihâwin",
        "crolHelpText": "ki OCS oyôhkêmakan ayamihâwin",
        "crsaTitle": "CRSA kwayaskîtamowin (Cannabis Retail Store Authorization)",
        "domainVerifiedSuccess": "✓ Domain kwayaskîtamohk - ki email domain tahto CRSA website. kikway atâwêwikamik ta-osîhtâw mêkwâc oma oyôhkêmakan.",
        "licenseLabel": "Ontario Cannabis atâwêwin oyôhkêmakan ayamihâwin",
        "licensePlaceholder": "ayamân: LCBO-1234",
        "validating": "kwayaskîtamohk...",
        "validate": "kwayaskîtamowin",
        "licenseHelpText": "kîkway ki Ontario cannabis atâwêwin oyôhkêmakan AGCO ohci",
        "validatedSuccess": "✓ oyôhkêmakan kwayaskîtamohk mwêhci",
        "storeNameLabel": "atâwêwikamik isiyîhkâsowin:",
        "municipalityLabel": "otênaw:",
        "addressLabel": "tânite:",
        "websiteLabel": "website:",
        "validationFailed": "kwayaskîtamowin namôya mwêhci",
        "searchIntro": "namôya kikiskêyihtên ki oyôhkêmakan ayamihâwin? nâtam ki atâwêwikamik:",
        "searchPlaceholder": "nâtam isiyîhkâsowin ahpô tânite",
        "searching": "nâtamohk...",
        "noResults": "namôya kîkway miskam",
        "selectStore": "wâpahtam ki atâwêwikamik oma ohci:",
        "needHelp": "nitawihtên wîcihiwewin?",
        "helpDetails": "kimiska ki oyôhkêmakan ayamihâwina ôma:",
        "helpCrol": "• CROL: ki OCS B2B portal (nitawihtamihk)",
        "helpCrsa": "• CRSA: AGCO oyôhkêmakan database awâsime (namôya nitawihtamihk)",
        "helpNote": "kiskisiwin: kika pakitinên CRSA êkwa kiskinwahamaw atâwêwikamikwa îskwêyâc."
    },
    "fa": {  # Persian (RTL)
        "title": "مجوز شاهدانه انتاریو",
        "description": "برای خرده‌فروشان شاهدانه در انتاریو الزامی است. CROL مجوز عملیاتی در سطح مستاجر شماست، CRSA مجوز خرده‌فروشی در سطح فروشگاه است.",
        "crolLabel": "شماره CROL (مجوز عملیاتی خرده‌فروشی شاهدانه) *",
        "crolPlaceholder": "شماره CROL خود از OCS را وارد کنید",
        "crolHelpText": "شماره مجوز عملیاتی OCS در سطح مستاجر شما",
        "crsaTitle": "اعتبارسنجی CRSA (مجوز فروشگاه خرده‌فروشی شاهدانه)",
        "domainVerifiedSuccess": "✓ دامنه تأیید شد - دامنه ایمیل شما با وب‌سایت CRSA مطابقت دارد. اولین فروشگاه شما به‌طور خودکار از این مجوز ایجاد خواهد شد.",
        "licenseLabel": "شماره مجوز خرده‌فروشی شاهدانه انتاریو",
        "licensePlaceholder": "مثال: LCBO-1234",
        "validating": "در حال اعتبارسنجی...",
        "validate": "اعتبارسنجی",
        "licenseHelpText": "شماره مجوز خرده‌فروشی شاهدانه انتاریو خود را از AGCO وارد کنید",
        "validatedSuccess": "✓ مجوز با موفقیت تأیید شد",
        "storeNameLabel": "نام فروشگاه:",
        "municipalityLabel": "شهرداری:",
        "addressLabel": "آدرس:",
        "websiteLabel": "وب‌سایت:",
        "validationFailed": "اعتبارسنجی ناموفق بود",
        "searchIntro": "شماره مجوز خود را نمی‌دانید؟ فروشگاه خود را جستجو کنید:",
        "searchPlaceholder": "جستجو بر اساس نام فروشگاه یا آدرس",
        "searching": "در حال جستجو...",
        "noResults": "نتیجه‌ای یافت نشد",
        "selectStore": "فروشگاه خود را از لیست زیر انتخاب کنید:",
        "needHelp": "به کمک نیاز دارید؟",
        "helpDetails": "می‌توانید شماره‌های مجوز خود را در اینجا پیدا کنید:",
        "helpCrol": "• شماره CROL: پورتال B2B شما در OCS (برای ایجاد مستاجر الزامی است)",
        "helpCrsa": "• شماره CRSA: پایگاه داده عمومی مجوز AGCO (اختیاری - برای تأیید خودکار فروشگاه)",
        "helpNote": "نکته: می‌توانید اعتبارسنجی CRSA را رد کنید و فروشگاه‌ها را بعداً به‌صورت دستی اضافه کنید."
    },
    "he": {  # Hebrew (RTL)
        "title": "רישוי קנאביס באונטריו",
        "description": "נדרש לקמעונאי קנאביס באונטריו. CROL הוא רישיון התפעול שלך ברמת הדייר, CRSA הוא אישור הקמעונאות ברמת החנות.",
        "crolLabel": "מספר CROL (רישיון תפעול קמעונאות קנאביס) *",
        "crolPlaceholder": "הזן את מספר ה-CROL שלך מ-OCS",
        "crolHelpText": "מספר רישיון התפעול שלך מ-OCS ברמת הדייר",
        "crsaTitle": "אימות CRSA (אישור חנות קמעונאות קנאביס)",
        "domainVerifiedSuccess": "✓ הדומיין אומת - דומיין האימייל שלך תואם לאתר CRSA. החנות הראשונה שלך תיווצר אוטומטית מרישיון זה.",
        "licenseLabel": "מספר רישיון קמעונאות קנאביס באונטריו",
        "licensePlaceholder": "לדוגמה: LCBO-1234",
        "validating": "מאמת...",
        "validate": "אמת",
        "licenseHelpText": "הזן את מספר רישיון קמעונאות הקנאביס שלך באונטריו מ-AGCO",
        "validatedSuccess": "✓ הרישיון אומת בהצלחה",
        "storeNameLabel": "שם החנות:",
        "municipalityLabel": "עירייה:",
        "addressLabel": "כתובת:",
        "websiteLabel": "אתר אינטרנט:",
        "validationFailed": "האימות נכשל",
        "searchIntro": "לא יודע את מספר הרישיון שלך? חפש את החנות שלך:",
        "searchPlaceholder": "חפש לפי שם חנות או כתובת",
        "searching": "מחפש...",
        "noResults": "לא נמצאו תוצאות",
        "selectStore": "בחר את החנות שלך מהרשימה למטה:",
        "needHelp": "צריך עזרה?",
        "helpDetails": "אתה יכול למצוא את מספרי הרישיון שלך ב:",
        "helpCrol": "• מספר CROL: פורטל ה-B2B שלך ב-OCS (נדרש ליצירת דייר)",
        "helpCrsa": "• מספר CRSA: מסד הנתונים הציבורי של רישיונות AGCO (אופציונלי - לאימות אוטומטי של חנות)",
        "helpNote": "הערה: אתה יכול לדלג על אימות CRSA ולהוסיף חנויות ידנית מאוחר יותר."
    },
    "iu": {  # Inuktitut
        "title": "Ontario ᐊᖅᑭᓯᒪᔪᑦ ᐱᔪᓐᓇᐅᑎᑦ",
        "description": "ᐱᔭᕆᐊᖃᖅᑐᖅ Ontario-ᒥ ᓂᐅᕕᕐᕕᖃᖅᑎᑦ. CROL ᐃᒡᓗᑎᑦ ᐱᔪᓐᓇᐅᑎᖓ, CRSA ᓂᐅᕕᕐᕕᐅᑉ ᐱᔪᓐᓇᐅᑎᖓ.",
        "crolLabel": "CROL ᓈᓴᐅᑎ (Cannabis Retail Operating License) *",
        "crolPlaceholder": "ᐃᓕᔅᓯ OCS CROL ᓈᓴᐅᑎ",
        "crolHelpText": "ᐃᓕᔅᓯ OCS ᐃᒡᓗᑎᑦ ᐱᔪᓐᓇᐅᑎ ᓈᓴᐅᑎ",
        "crsaTitle": "CRSA ᖃᐅᔨᓴᖅᑕᐅᓂᖓ (Cannabis Retail Store Authorization)",
        "domainVerifiedSuccess": "✓ Domain ᖃᐅᔨᓴᖅᑕᐅᓯᒪᔪᖅ - ᐃᓕᔅᓯ email domain ᐊᔾᔨᐅᔪᖅ CRSA website-ᒧᑦ. ᓯᕗᓪᓕᖅᐹᖅ ᓂᐅᕕᕐᕕᑦ ᓴᖅᑭᑎᑕᐅᓂᐊᖅᑐᖅ ᐊᐅᑐᒪᑎᒃᑯᑦ ᐅᑯᓇᖓᑦ ᐱᔪᓐᓇᐅᑎᖅ.",
        "licenseLabel": "Ontario Cannabis ᓂᐅᕕᕐᕕᐅᑉ ᐱᔪᓐᓇᐅᑎ ᓈᓴᐅᑎ",
        "licensePlaceholder": "ᐆᑦᑑᑎ: LCBO-1234",
        "validating": "ᖃᐅᔨᓴᖅᑕᐅᔪᖅ...",
        "validate": "ᖃᐅᔨᓴᕐᓗᒍ",
        "licenseHelpText": "ᐃᓕᔅᓯ Ontario cannabis ᓂᐅᕕᕐᕕᐅᑉ ᐱᔪᓐᓇᐅᑎ ᓈᓴᐅᑎ AGCO-ᒥᑦ",
        "validatedSuccess": "✓ ᐱᔪᓐᓇᐅᑎ ᖃᐅᔨᓴᖅᑕᐅᓯᒪᔪᖅ ᐱᐅᓯᒋᐊᖅᑎᑕᐅᓪᓗᓂ",
        "storeNameLabel": "ᓂᐅᕕᕐᕕᐅᑉ ᐊᑎᖓ:",
        "municipalityLabel": "ᓄᓇᓕᖅ:",
        "addressLabel": "ᐊᑐᐃᓐᓇᐅᑎᓕᒃ:",
        "websiteLabel": "ᐅᕙᓂ:",
        "validationFailed": "ᖃᐅᔨᓴᕐᓂᖅ ᐊᑲᐅᙱᓚᐅᖅᑐᖅ",
        "searchIntro": "ᖃᐅᔨᒪᙱᑦᑐᑎᑦ ᐃᓕᔅᓯ ᐱᔪᓐᓇᐅᑎ ᓈᓴᐅᑎ? ᕿᓂᕐᓗᒍ ᐃᓕᔅᓯ ᓂᐅᕕᕐᕕᖅ:",
        "searchPlaceholder": "ᕿᓂᕐᓗᒍ ᓂᐅᕕᕐᕕᐅᑉ ᐊᑎᖓ ᐅᕙᓗ ᐊᑐᐃᓐᓇᐅᑎᓕᒃ",
        "searching": "ᕿᓂᖅᑕᐅᔪᖅ...",
        "noResults": "ᐊᑕᐅᓯᕐᓗ ᓇᓂᔭᐅᓚᐅᙱᑦᑐᖅ",
        "selectStore": "ᓂᕈᐊᕐᓗᒍ ᐃᓕᔅᓯ ᓂᐅᕕᕐᕕᖅ ᐅᑯᓇᖓᑦ:",
        "needHelp": "ᐃᑲᔪᖅᑕᐅᔭᕆᐊᖃᖅᐱᑎᑦ?",
        "helpDetails": "ᓇᓂᔭᐅᔪᓐᓇᖅᑐᑦ ᐃᓕᔅᓯ ᐱᔪᓐᓇᐅᑎ ᓈᓴᐅᑎᑦ:",
        "helpCrol": "• CROL: ᐃᓕᔅᓯ OCS B2B portal (ᐱᔭᕆᐊᖃᖅᑐᖅ)",
        "helpCrsa": "• CRSA: AGCO ᐃᓄᐃᑦ ᖃᐅᔨᒪᔾᔪᑎᖏᑦ (ᐱᔭᕆᐊᖃᙱᑦᑐᖅ)",
        "helpNote": "ᖃᐅᔨᒪᔭᐅᔪᖅ: ᐊᓂᒍᐃᔪᓐᓇᖅᑐᑎᑦ CRSA ᖃᐅᔨᓴᕐᓂᖅ ᐊᒻᒪ ᐃᓚᒋᐊᕐᓗᒋᑦ ᓂᐅᕕᕐᕕᑦ ᐊᒡᒍᑐᖅᑎᑦᑎᓗᑎᑦ ᐃᓱᓕᕐᓗᒍ."
    },
    "so": {  # Somali
        "title": "Shatiga Cannabis ee Ontario",
        "description": "Loo baahan yahay iibiyeyaasha cannabis ee Ontario. CROL waa shatiga hawlgalkaaga ee heerka qanjadhada, CRSA waa ogolaanshaha tafaariiqda ee heerka dukaanka.",
        "crolLabel": "Nambarada CROL (Cannabis Retail Operating License) *",
        "crolPlaceholder": "Geli nambaradaada CROL ee OCS",
        "crolHelpText": "Nambarada shatiga hawlgalkaaga ee OCS heerka qanjadhada",
        "crsaTitle": "Xaqiijinta CRSA (Cannabis Retail Store Authorization)",
        "domainVerifiedSuccess": "✓ Domain la Xaqiijiyey - domain-ka email-kaagu wuxuu u dhigma website-ka CRSA. Dukaankaaga ugu horreeya ayaa si otomaatig ah loogu samayn doonaa shatigan.",
        "licenseLabel": "Nambarada Shatiga Tafaariiqda Cannabis ee Ontario",
        "licensePlaceholder": "tusaale: LCBO-1234",
        "validating": "Xaqiijinaya...",
        "validate": "Xaqiiji",
        "licenseHelpText": "Geli nambarada shatiga tafaariiqda cannabis ee Ontario ee AGCO",
        "validatedSuccess": "✓ Shatiga si Guul leh ayaa loo Xaqiijiyey",
        "storeNameLabel": "Magaca Dukaanka:",
        "municipalityLabel": "Degmada:",
        "addressLabel": "Cinwaanka:",
        "websiteLabel": "Website-ka:",
        "validationFailed": "Xaqiijinta Way Fashilantay",
        "searchIntro": "Ma ogtahay nambaradaada shatiga? Raadi dukaankaaga:",
        "searchPlaceholder": "Ku raadi magaca dukaanka ama cinwaanka",
        "searching": "Raadinta...",
        "noResults": "Wax natiijo ah lama helin",
        "selectStore": "Dooro dukaankaaga liiska hoose:",
        "needHelp": "Ma u baahan tahay caawimaad?",
        "helpDetails": "Waxaad ka heli kartaa nambaradahaaga shatiga:",
        "helpCrol": "• Nambarada CROL: Portal-kaaga OCS B2B (loo baahan yahay in la abuuro qanjadhada)",
        "helpCrsa": "• Nambarada CRSA: Kaydka dadweynaha ee shatiga AGCO (ikhtiyaar ah - xaqiijinta otomaatigga ah ee dukaanka)",
        "helpNote": "Fiiro gaar ah: Waxaad ka booddhi kartaa xaqiijinta CRSA oo dukaammada si gacanta ah u dari kartaa markii dambe."
    },
    "tl": {  # Tagalog
        "title": "Lisensya ng Cannabis sa Ontario",
        "description": "Kinakailangan para sa mga retailer ng cannabis sa Ontario. Ang CROL ay ang iyong operating license sa antas ng tenant, ang CRSA ay ang iyong retail authorization sa antas ng tindahan.",
        "crolLabel": "Numero ng CROL (Cannabis Retail Operating License) *",
        "crolPlaceholder": "Ilagay ang iyong OCS CROL numero",
        "crolHelpText": "Ang iyong OCS operating license number sa antas ng tenant",
        "crsaTitle": "Pagpapatunay ng CRSA (Cannabis Retail Store Authorization)",
        "domainVerifiedSuccess": "✓ Na-verify ang Domain - Ang domain ng iyong email ay tumutugma sa website ng CRSA. Ang iyong unang tindahan ay awtomatikong lilikhahin mula sa lisensyang ito.",
        "licenseLabel": "Numero ng Lisensya ng Cannabis Retail sa Ontario",
        "licensePlaceholder": "halimbawa: LCBO-1234",
        "validating": "Nag-veverify...",
        "validate": "I-validate",
        "licenseHelpText": "Ilagay ang iyong numero ng lisensya ng cannabis retail sa Ontario mula sa AGCO",
        "validatedSuccess": "✓ Matagumpay na Na-validate ang Lisensya",
        "storeNameLabel": "Pangalan ng Tindahan:",
        "municipalityLabel": "Munisipalidad:",
        "addressLabel": "Address:",
        "websiteLabel": "Website:",
        "validationFailed": "Nabigo ang Pagpapatunay",
        "searchIntro": "Hindi alam ang iyong numero ng lisensya? Maghanap ng iyong tindahan:",
        "searchPlaceholder": "Maghanap sa pamamagitan ng pangalan ng tindahan o address",
        "searching": "Naghahanap...",
        "noResults": "Walang nahanap na resulta",
        "selectStore": "Piliin ang iyong tindahan mula sa listahan sa ibaba:",
        "needHelp": "Kailangan ng tulong?",
        "helpDetails": "Maaari mong mahanap ang iyong mga numero ng lisensya sa:",
        "helpCrol": "• Numero ng CROL: Ang iyong OCS B2B portal (kinakailangan para lumikha ng tenant)",
        "helpCrsa": "• Numero ng CRSA: Pampublikong database ng lisensya ng AGCO (opsyonal - para sa awtomatikong pagpapatunay ng tindahan)",
        "helpNote": "Paalala: Maaari mong laktawan ang pagpapatunay ng CRSA at magdagdag ng mga tindahan nang manu-mano mamaya."
    }
}

def update_ontario_section(lang_code, translations):
    """Update Ontario section in signup.json for a language"""
    file_path = f"src/Frontend/ai-admin-dashboard/src/i18n/locales/{lang_code}/signup.json"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update Ontario section
        if 'tenant' in data and 'ontario' in data['tenant']:
            data['tenant']['ontario'] = translations
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Updated {lang_code}")
            return True
        else:
            print(f"✗ Missing ontario section in {lang_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error updating {lang_code}: {e}")
        return False

def main():
    print("=" * 80)
    print("COMPLETING ONTARIO TRANSLATIONS FOR 7 LANGUAGES")
    print("=" * 80)
    
    completed = 0
    for lang_code, translations in ONTARIO_TRANSLATIONS.items():
        if update_ontario_section(lang_code, translations):
            completed += 1
    
    print("=" * 80)
    print(f"✅ COMPLETE! Updated {completed}/{len(ONTARIO_TRANSLATIONS)} languages")
    print(f"   Total translations added: {completed * 28}")
    print("=" * 80)

if __name__ == "__main__":
    main()
