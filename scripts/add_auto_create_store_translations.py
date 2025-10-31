#!/usr/bin/env python3
"""Add auto-create store checkbox translations to all languages"""

import json
import os

# Auto-create store checkbox translations for all 28 languages
AUTO_CREATE_STORE_TRANSLATIONS = {
    "en": {
        "autoCreateStoreLabel": "Create {storeName} as my first store",
        "autoCreateStoreHelp": "This store will be automatically created when you complete signup. You can uncheck this to add stores manually later."
    },
    "zh": {
        "autoCreateStoreLabel": "创建 {storeName} 作为我的第一家店铺",
        "autoCreateStoreHelp": "完成注册时将自动创建此店铺。您可以取消选中以便稍后手动添加店铺。"
    },
    "fr": {
        "autoCreateStoreLabel": "Créer {storeName} comme mon premier magasin",
        "autoCreateStoreHelp": "Ce magasin sera automatiquement créé lors de votre inscription. Vous pouvez décocher pour ajouter des magasins manuellement plus tard."
    },
    "es": {
        "autoCreateStoreLabel": "Crear {storeName} como mi primera tienda",
        "autoCreateStoreHelp": "Esta tienda se creará automáticamente al completar el registro. Puede desmarcar para agregar tiendas manualmente más tarde."
    },
    "ar": {
        "autoCreateStoreLabel": "إنشاء {storeName} كمتجري الأول",
        "autoCreateStoreHelp": "سيتم إنشاء هذا المتجر تلقائيًا عند إكمال التسجيل. يمكنك إلغاء التحديد لإضافة المتاجر يدويًا لاحقًا."
    },
    "de": {
        "autoCreateStoreLabel": "{storeName} als mein erstes Geschäft erstellen",
        "autoCreateStoreHelp": "Dieses Geschäft wird automatisch bei Abschluss der Registrierung erstellt. Sie können dies abwählen, um Geschäfte später manuell hinzuzufügen."
    },
    "it": {
        "autoCreateStoreLabel": "Crea {storeName} come mio primo negozio",
        "autoCreateStoreHelp": "Questo negozio verrà creato automaticamente al completamento della registrazione. Puoi deselezionare per aggiungere negozi manualmente in seguito."
    },
    "pt": {
        "autoCreateStoreLabel": "Criar {storeName} como minha primeira loja",
        "autoCreateStoreHelp": "Esta loja será criada automaticamente ao concluir o cadastro. Você pode desmarcar para adicionar lojas manualmente depois."
    },
    "nl": {
        "autoCreateStoreLabel": "{storeName} als mijn eerste winkel maken",
        "autoCreateStoreHelp": "Deze winkel wordt automatisch aangemaakt bij het voltooien van de registratie. U kunt dit uitvinken om later handmatig winkels toe te voegen."
    },
    "pl": {
        "autoCreateStoreLabel": "Utwórz {storeName} jako mój pierwszy sklep",
        "autoCreateStoreHelp": "Ten sklep zostanie automatycznie utworzony po zakończeniu rejestracji. Możesz odznaczyć, aby dodać sklepy ręcznie później."
    },
    "ro": {
        "autoCreateStoreLabel": "Creează {storeName} ca primul meu magazin",
        "autoCreateStoreHelp": "Acest magazin va fi creat automat la finalizarea înregistrării. Puteți debifa pentru a adăuga magazine manual mai târziu."
    },
    "ru": {
        "autoCreateStoreLabel": "Создать {storeName} как мой первый магазин",
        "autoCreateStoreHelp": "Этот магазин будет создан автоматически при завершении регистрации. Вы можете снять флажок, чтобы добавить магазины вручную позже."
    },
    "uk": {
        "autoCreateStoreLabel": "Створити {storeName} як мій перший магазин",
        "autoCreateStoreHelp": "Цей магазин буде створено автоматично після завершення реєстрації. Ви можете зняти прапорець, щоб додати магазини вручну пізніше."
    },
    "ja": {
        "autoCreateStoreLabel": "{storeName} を最初の店舗として作成",
        "autoCreateStoreHelp": "この店舗は登録完了時に自動的に作成されます。チェックを外すと、後で手動で店舗を追加できます。"
    },
    "ko": {
        "autoCreateStoreLabel": "{storeName}를 첫 번째 매장으로 생성",
        "autoCreateStoreHelp": "이 매장은 가입 완료 시 자동으로 생성됩니다. 체크를 해제하여 나중에 수동으로 매장을 추가할 수 있습니다."
    },
    "vi": {
        "autoCreateStoreLabel": "Tạo {storeName} làm cửa hàng đầu tiên của tôi",
        "autoCreateStoreHelp": "Cửa hàng này sẽ được tạo tự động khi hoàn tất đăng ký. Bạn có thể bỏ chọn để thêm cửa hàng thủ công sau."
    },
    "yue": {
        "autoCreateStoreLabel": "創建 {storeName} 作為我嘅第一間鋪頭",
        "autoCreateStoreHelp": "完成註冊時會自動創建呢間鋪頭。你可以取消選擇以便稍後手動添加鋪頭。"
    },
    "hi": {
        "autoCreateStoreLabel": "{storeName} को मेरे पहले स्टोर के रूप में बनाएं",
        "autoCreateStoreHelp": "साइनअप पूरा होने पर यह स्टोर स्वचालित रूप से बनाया जाएगा। आप बाद में मैन्युअल रूप से स्टोर जोड़ने के लिए अनचेक कर सकते हैं।"
    },
    "bn": {
        "autoCreateStoreLabel": "{storeName} আমার প্রথম স্টোর হিসাবে তৈরি করুন",
        "autoCreateStoreHelp": "সাইনআপ সম্পূর্ণ হলে এই স্টোরটি স্বয়ংক্রিয়ভাবে তৈরি হবে। পরে ম্যানুয়ালি স্টোর যুক্ত করতে আপনি আনচেক করতে পারেন।"
    },
    "gu": {
        "autoCreateStoreLabel": "{storeName} ને મારા પ્રથમ સ્ટોર તરીકે બનાવો",
        "autoCreateStoreHelp": "સાઇનઅપ પૂર્ણ થાય ત્યારે આ સ્ટોર આપમેળે બનાવવામાં આવશે. તમે પછીથી મેન્યુઅલી સ્ટોર્સ ઉમેરવા માટે અનચેક કરી શકો છો।"
    },
    "pa": {
        "autoCreateStoreLabel": "{storeName} ਨੂੰ ਮੇਰੇ ਪਹਿਲੇ ਸਟੋਰ ਵਜੋਂ ਬਣਾਓ",
        "autoCreateStoreHelp": "ਸਾਈਨਅੱਪ ਪੂਰਾ ਹੋਣ 'ਤੇ ਇਹ ਸਟੋਰ ਆਪਣੇ ਆਪ ਬਣਾਇਆ ਜਾਵੇਗਾ। ਤੁਸੀਂ ਬਾਅਦ ਵਿੱਚ ਮੈਨੁਅਲੀ ਸਟੋਰ ਜੋੜਨ ਲਈ ਅਨਚੈੱਕ ਕਰ ਸਕਦੇ ਹੋ।"
    },
    "ta": {
        "autoCreateStoreLabel": "{storeName} ஐ எனது முதல் ஸ்டோராக உருவாக்கு",
        "autoCreateStoreHelp": "பதிவு முடிக்கும்போது இந்த ஸ்டோர் தானாக உருவாக்கப்படும். பின்னர் கைமுறையாக ஸ்டோர்களைச் சேர்க்க நீங்கள் தேர்வை நீக்கலாம்."
    },
    "ur": {
        "autoCreateStoreLabel": "{storeName} کو میرے پہلے اسٹور کے طور پر بنائیں",
        "autoCreateStoreHelp": "سائن اپ مکمل ہونے پر یہ اسٹور خودکار طور پر بنایا جائے گا۔ آپ بعد میں دستی طور پر اسٹور شامل کرنے کے لیے ان چیک کر سکتے ہیں۔"
    },
    "fa": {
        "autoCreateStoreLabel": "ایجاد {storeName} به عنوان اولین فروشگاه من",
        "autoCreateStoreHelp": "این فروشگاه به طور خودکار هنگام تکمیل ثبت نام ایجاد می‌شود. می‌توانید تیک را بردارید تا فروشگاه‌ها را بعداً به صورت دستی اضافه کنید."
    },
    "he": {
        "autoCreateStoreLabel": "צור את {storeName} כחנות הראשונה שלי",
        "autoCreateStoreHelp": "חנות זו תיווצר אוטומטית בסיום ההרשמה. אתה יכול לבטל את הסימון כדי להוסיף חנויות ידנית מאוחר יותר."
    },
    "so": {
        "autoCreateStoreLabel": "Samee {storeName} dukaankayga ugu horreeya",
        "autoCreateStoreHelp": "Dukaankan si otomaatig ah ayaa loo samayn doonaa markaad dhammaystirto isdiiwaangelinta. Waxaad ka saari kartaa calaamadda si aad u darto dukaammo gacanta markii dambe."
    },
    "tl": {
        "autoCreateStoreLabel": "Gawing {storeName} ang aking unang tindahan",
        "autoCreateStoreHelp": "Awtomatikong gagawin ang tindahang ito kapag nakumpleto ang signup. Maaari mong i-uncheck upang magdagdag ng mga tindahan nang manu-mano mamaya."
    },
    "cr": {
        "autoCreateStoreLabel": "osîhtaw {storeName} nitam ni atâwêwikamik",
        "autoCreateStoreHelp": "oma atâwêwikamik ta-osîhtâw mêkwâc kikway ispayiw. kika pakitinên êkwa kiskinwahamaw atâwêwikamikwa îskwêyâc."
    },
    "iu": {
        "autoCreateStoreLabel": "ᓴᖅᑭᑎᑦᑎᓗᒍ {storeName} ᓯᕗᓪᓕᖅᐹᖅ ᓂᐅᕕᕐᕕᒃ",
        "autoCreateStoreHelp": "ᐅᓇ ᓂᐅᕕᕐᕕᖅ ᓴᖅᑭᑎᑕᐅᓂᐊᖅᑐᖅ ᐊᐅᑐᒪᑎᒃᑯᑦ. ᐊᓂᒍᐃᔪᓐᓇᖅᑐᑎᑦ ᐃᓚᒋᐊᕐᓗᒋᑦ ᓂᐅᕕᕐᕕᑦ ᐊᒡᒍᑐᖅᑎᑦᑎᓗᑎᑦ ᐃᓱᓕᕐᓗᒍ."
    }
}

def update_ontario_section(lang_code, translations):
    """Add auto-create store translations to tenant.ontario section"""
    file_path = f"src/Frontend/ai-admin-dashboard/src/i18n/locales/{lang_code}/signup.json"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'tenant' in data and 'ontario' in data['tenant']:
            # Add new keys to ontario section
            data['tenant']['ontario'].update(translations)
            
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
    print("ADDING AUTO-CREATE STORE CHECKBOX TRANSLATIONS")
    print("=" * 80)
    
    completed = 0
    for lang_code, translations in AUTO_CREATE_STORE_TRANSLATIONS.items():
        if update_ontario_section(lang_code, translations):
            completed += 1
    
    print("=" * 80)
    print(f"✅ COMPLETE! Updated {completed}/{len(AUTO_CREATE_STORE_TRANSLATIONS)} languages")
    print(f"   Added 2 translation keys per language (56 total)")
    print("=" * 80)

if __name__ == "__main__":
    main()
