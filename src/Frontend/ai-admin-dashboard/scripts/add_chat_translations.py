#!/usr/bin/env python3
"""
Add chat widget greeting translations for all languages
"""

import json
from pathlib import Path

# Chat greeting translations for all 29 languages
CHAT_TRANSLATIONS = {
    "en": {
        "assistant": {
            "greeting": "Welcome! How can I assist you today? You can type or use voice input."
        },
        "sales": {
            "greeting": "Hi! I'm Carlos, your WeedGo sales assistant. 👋\n\nI'm here to help you discover how WeedGo can transform your cannabis retail business. Whether you're curious about pricing, features, or just getting started - I'm here to answer any questions.\n\nWhat would you like to know about WeedGo?"
        }
    },
    "es": {
        "assistant": {
            "greeting": "¡Bienvenido! ¿Cómo puedo ayudarte hoy? Puedes escribir o usar entrada de voz."
        },
        "sales": {
            "greeting": "¡Hola! Soy Carlos, tu asistente de ventas de WeedGo. 👋\n\nEstoy aquí para ayudarte a descubrir cómo WeedGo puede transformar tu negocio de cannabis. Ya sea que tengas curiosidad sobre precios, características o estés comenzando - estoy aquí para responder cualquier pregunta.\n\n¿Qué te gustaría saber sobre WeedGo?"
        }
    },
    "fr": {
        "assistant": {
            "greeting": "Bienvenue ! Comment puis-je vous aider aujourd'hui ? Vous pouvez taper ou utiliser la saisie vocale."
        },
        "sales": {
            "greeting": "Bonjour ! Je suis Carlos, votre assistant commercial WeedGo. 👋\n\nJe suis là pour vous aider à découvrir comment WeedGo peut transformer votre entreprise de cannabis. Que vous soyez curieux des prix, des fonctionnalités ou que vous débutiez - je suis là pour répondre à toutes vos questions.\n\nQu'aimeriez-vous savoir sur WeedGo ?"
        }
    },
    "zh": {
        "assistant": {
            "greeting": "欢迎！我今天能帮您什么忙？您可以打字或使用语音输入。"
        },
        "sales": {
            "greeting": "你好！我是Carlos，您的WeedGo销售助手。👋\n\n我在这里帮助您了解WeedGo如何改变您的大麻零售业务。无论您对价格、功能感到好奇，还是刚刚开始 - 我都在这里回答任何问题。\n\n您想了解WeedGo的什么？"
        }
    },
    "ar": {
        "assistant": {
            "greeting": "مرحبًا! كيف يمكنني مساعدتك اليوم؟ يمكنك الكتابة أو استخدام إدخال الصوت."
        },
        "sales": {
            "greeting": "مرحبًا! أنا Carlos، مساعد مبيعات WeedGo الخاص بك. 👋\n\nأنا هنا لمساعدتك في اكتشاف كيف يمكن لـ WeedGo تحويل أعمال تجارة التجزئة الخاصة بك. سواء كنت فضوليًا بشأن الأسعار أو الميزات أو البدء فقط - أنا هنا للإجابة على أي أسئلة.\n\nماذا تريد أن تعرف عن WeedGo؟"
        }
    },
    "hi": {
        "assistant": {
            "greeting": "स्वागत है! मैं आज आपकी कैसे मदद कर सकता हूं? आप टाइप कर सकते हैं या वॉइस इनपुट का उपयोग कर सकते हैं।"
        },
        "sales": {
            "greeting": "नमस्ते! मैं Carlos हूं, आपका WeedGo बिक्री सहायक। 👋\n\nमैं यहां आपको यह जानने में मदद करने के लिए हूं कि WeedGo आपके कैनबिस खुदरा व्यवसाय को कैसे बदल सकता है। चाहे आप मूल्य निर्धारण, सुविधाओं के बारे में उत्सुक हों या अभी शुरुआत कर रहे हों - मैं किसी भी प्रश्न का उत्तर देने के लिए यहां हूं।\n\nआप WeedGo के बारे में क्या जानना चाहेंगे?"
        }
    },
    "pa": {
        "assistant": {
            "greeting": "ਸੁਆਗਤ ਹੈ! ਮੈਂ ਅੱਜ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ? ਤੁਸੀਂ ਟਾਈਪ ਕਰ ਸਕਦੇ ਹੋ ਜਾਂ ਆਵਾਜ਼ ਇਨਪੁੱਟ ਵਰਤ ਸਕਦੇ ਹੋ।"
        },
        "sales": {
            "greeting": "ਹੈਲੋ! ਮੈਂ Carlos ਹਾਂ, ਤੁਹਾਡਾ WeedGo ਵਿਕਰੀ ਸਹਾਇਕ। 👋\n\nਮੈਂ ਇੱਥੇ ਤੁਹਾਨੂੰ ਇਹ ਪਤਾ ਲਗਾਉਣ ਵਿੱਚ ਮਦਦ ਕਰਨ ਲਈ ਹਾਂ ਕਿ WeedGo ਤੁਹਾਡੇ ਕੈਨਾਬਿਸ ਰਿਟੇਲ ਕਾਰੋਬਾਰ ਨੂੰ ਕਿਵੇਂ ਬਦਲ ਸਕਦਾ ਹੈ। ਭਾਵੇਂ ਤੁਸੀਂ ਕੀਮਤਾਂ, ਵਿਸ਼ੇਸ਼ਤਾਵਾਂ ਬਾਰੇ ਉਤਸੁਕ ਹੋ ਜਾਂ ਹੁਣੇ ਸ਼ੁਰੂਆਤ ਕਰ ਰਹੇ ਹੋ - ਮੈਂ ਕਿਸੇ ਵੀ ਸਵਾਲ ਦਾ ਜਵਾਬ ਦੇਣ ਲਈ ਇੱਥੇ ਹਾਂ।\n\nਤੁਸੀਂ WeedGo ਬਾਰੇ ਕੀ ਜਾਣਨਾ ਚਾਹੋਗੇ?"
        }
    },
    "tl": {
        "assistant": {
            "greeting": "Maligayang pagdating! Paano kita matutulungan ngayon? Maaari kang mag-type o gumamit ng voice input."
        },
        "sales": {
            "greeting": "Kamusta! Ako si Carlos, ang iyong WeedGo sales assistant. 👋\n\nNandito ako para tulungan kang matuklasan kung paano mababago ng WeedGo ang iyong cannabis retail business. Kung curious ka sa pricing, features, o nagsisimula ka pa lang - nandito ako para sagutin ang anumang tanong.\n\nAno ang gusto mong malaman tungkol sa WeedGo?"
        }
    },
    "it": {
        "assistant": {
            "greeting": "Benvenuto! Come posso aiutarti oggi? Puoi digitare o utilizzare l'input vocale."
        },
        "sales": {
            "greeting": "Ciao! Sono Carlos, il tuo assistente alle vendite WeedGo. 👋\n\nSono qui per aiutarti a scoprire come WeedGo può trasformare la tua attività al dettaglio di cannabis. Che tu sia curioso di prezzi, funzionalità o appena iniziato - sono qui per rispondere a qualsiasi domanda.\n\nCosa vorresti sapere su WeedGo?"
        }
    },
    "de": {
        "assistant": {
            "greeting": "Willkommen! Wie kann ich Ihnen heute helfen? Sie können tippen oder Spracheingabe verwenden."
        },
        "sales": {
            "greeting": "Hallo! Ich bin Carlos, Ihr WeedGo-Verkaufsassistent. 👋\n\nIch bin hier, um Ihnen zu helfen, herauszufinden, wie WeedGo Ihr Cannabis-Einzelhandelsgeschäft transformieren kann. Egal, ob Sie neugierig auf Preise, Funktionen oder den Einstieg sind - ich bin hier, um alle Fragen zu beantworten.\n\nWas möchten Sie über WeedGo erfahren?"
        }
    },
    "pt": {
        "assistant": {
            "greeting": "Bem-vindo! Como posso ajudá-lo hoje? Você pode digitar ou usar entrada de voz."
        },
        "sales": {
            "greeting": "Olá! Sou Carlos, seu assistente de vendas WeedGo. 👋\n\nEstou aqui para ajudá-lo a descobrir como o WeedGo pode transformar seu negócio de varejo de cannabis. Seja curioso sobre preços, recursos ou apenas começando - estou aqui para responder a qualquer pergunta.\n\nO que você gostaria de saber sobre o WeedGo?"
        }
    },
    "fa": {
        "assistant": {
            "greeting": "خوش آمدید! امروز چگونه می‌توانم به شما کمک کنم؟ می‌توانید تایپ کنید یا از ورودی صوتی استفاده کنید."
        },
        "sales": {
            "greeting": "سلام! من Carlos هستم، دستیار فروش WeedGo شما. 👋\n\nمن اینجا هستم تا به شما کمک کنم کشف کنید که WeedGo چگونه می‌تواند کسب‌وکار خرده‌فروشی کانابیس شما را متحول کند. خواه در مورد قیمت‌ها، ویژگی‌ها کنجکاو باشید یا فقط شروع کنید - من اینجا هستم تا به هر سوالی پاسخ دهم.\n\nچه چیزی درباره WeedGo می‌خواهید بدانید؟"
        }
    },
    "uk": {
        "assistant": {
            "greeting": "Ласкаво просимо! Як я можу допомогти вам сьогодні? Ви можете друкувати або використовувати голосовий ввід."
        },
        "sales": {
            "greeting": "Привіт! Я Carlos, ваш торговий помічник WeedGo. 👋\n\nЯ тут, щоб допомогти вам дізнатися, як WeedGo може трансформувати ваш роздрібний бізнес канабісу. Чи цікаво вам про ціни, функції чи ви тільки починаєте - я тут, щоб відповісти на будь-які запитання.\n\nЩо б ви хотіли дізнатися про WeedGo?"
        }
    },
    "pl": {
        "assistant": {
            "greeting": "Witamy! Jak mogę Ci dzisiaj pomóc? Możesz pisać lub użyć wprowadzania głosowego."
        },
        "sales": {
            "greeting": "Cześć! Jestem Carlos, Twój asystent sprzedaży WeedGo. 👋\n\nJestem tutaj, aby pomóc Ci odkryć, jak WeedGo może przekształcić Twój biznes detaliczny z konopią. Czy jesteś ciekawy cen, funkcji czy dopiero zaczynasz - jestem tutaj, aby odpowiedzieć na wszystkie pytania.\n\nCo chciałbyś wiedzieć o WeedGo?"
        }
    },
    "vi": {
        "assistant": {
            "greeting": "Chào mừng! Hôm nay tôi có thể giúp gì cho bạn? Bạn có thể gõ hoặc sử dụng đầu vào giọng nói."
        },
        "sales": {
            "greeting": "Xin chào! Tôi là Carlos, trợ lý bán hàng WeedGo của bạn. 👋\n\nTôi ở đây để giúp bạn khám phá cách WeedGo có thể biến đổi doanh nghiệp bán lẻ cần sa của bạn. Cho dù bạn tò mò về giá cả, tính năng hay chỉ mới bắt đầu - tôi ở đây để trả lời bất kỳ câu hỏi nào.\n\nBạn muốn biết gì về WeedGo?"
        }
    },
    "ko": {
        "assistant": {
            "greeting": "환영합니다! 오늘 무엇을 도와드릴까요? 입력하거나 음성 입력을 사용할 수 있습니다."
        },
        "sales": {
            "greeting": "안녕하세요! 저는 Carlos입니다, WeedGo 영업 어시스턴트입니다. 👋\n\nWeedGo가 귀하의 대마초 소매 비즈니스를 어떻게 변화시킬 수 있는지 알아보는 것을 도와드립니다. 가격, 기능 또는 시작하는 방법에 대해 궁금하신 경우 - 모든 질문에 답변해 드립니다.\n\nWeedGo에 대해 무엇을 알고 싶으신가요?"
        }
    },
    "ja": {
        "assistant": {
            "greeting": "ようこそ！今日は何かお手伝いできますか？入力するか音声入力を使用できます。"
        },
        "sales": {
            "greeting": "こんにちは！私はCarlosです、あなたのWeedGo販売アシスタントです。👋\n\nWeedGoがあなたの大麻小売ビジネスをどのように変革できるかをお手伝いします。価格、機能、または始め方について興味がある場合 - どんな質問にもお答えします。\n\nWeedGoについて何を知りたいですか？"
        }
    },
    "he": {
        "assistant": {
            "greeting": "ברוכים הבאים! איך אוכל לעזור לך היום? אתה יכול להקליד או להשתמש בקלט קולי."
        },
        "sales": {
            "greeting": "שלום! אני Carlos, עוזר המכירות של WeedGo שלך. 👋\n\nאני כאן כדי לעזור לך לגלות כיצד WeedGo יכול לשנות את עסק הקנאביס הקמעונאי שלך. בין אם אתה סקרן לגבי תמחור, תכונות או רק מתחיל - אני כאן כדי לענות על כל שאלה.\n\nמה תרצה לדעת על WeedGo?"
        }
    },
    "ur": {
        "assistant": {
            "greeting": "خوش آمدید! میں آج آپ کی کیسے مدد کر سکتا ہوں؟ آپ ٹائپ کر سکتے ہیں یا وائس ان پٹ استعمال کر سکتے ہیں۔"
        },
        "sales": {
            "greeting": "ہیلو! میں Carlos ہوں، آپ کا WeedGo سیلز اسسٹنٹ۔ 👋\n\nمیں یہاں آپ کی مدد کرنے کے لیے ہوں کہ WeedGo آپ کے بھنگ کی خوردہ کاروبار کو کیسے تبدیل کر سکتا ہے۔ چاہے آپ قیمتوں، خصوصیات کے بارے میں دلچسپی رکھتے ہوں یا ابھی شروعات کر رہے ہوں - میں کسی بھی سوال کا جواب دینے کے لیے یہاں ہوں۔\n\nآپ WeedGo کے بارے میں کیا جاننا چاہیں گے؟"
        }
    },
    "ru": {
        "assistant": {
            "greeting": "Добро пожаловать! Как я могу помочь вам сегодня? Вы можете печатать или использовать голосовой ввод."
        },
        "sales": {
            "greeting": "Привет! Я Carlos, ваш торговый помощник WeedGo. 👋\n\nЯ здесь, чтобы помочь вам узнать, как WeedGo может трансформировать ваш розничный бизнес каннабиса. Будь то цены, функции или только начало - я здесь, чтобы ответить на любые вопросы.\n\nЧто бы вы хотели узнать о WeedGo?"
        }
    },
    "ro": {
        "assistant": {
            "greeting": "Bun venit! Cum vă pot ajuta astăzi? Puteți tasta sau utiliza intrarea vocală."
        },
        "sales": {
            "greeting": "Bună! Sunt Carlos, asistentul tău de vânzări WeedGo. 👋\n\nSunt aici pentru a te ajuta să descoperi cum WeedGo poate transforma afacerea ta de retail cu canabis. Fie că ești curios despre prețuri, caracteristici sau doar începi - sunt aici pentru a răspunde la orice întrebare.\n\nCe ai dori să știi despre WeedGo?"
        }
    },
    "nl": {
        "assistant": {
            "greeting": "Welkom! Hoe kan ik u vandaag helpen? U kunt typen of spraakinvoer gebruiken."
        },
        "sales": {
            "greeting": "Hallo! Ik ben Carlos, uw WeedGo-verkoopassistent. 👋\n\nIk ben hier om u te helpen ontdekken hoe WeedGo uw cannabisdetailhandel kan transformeren. Of u nu nieuwsgierig bent naar prijzen, functies of net begint - ik ben hier om elke vraag te beantwoorden.\n\nWat wilt u weten over WeedGo?"
        }
    },
    "cr": {
        "assistant": {
            "greeting": "ᑕᓂᓯ! ᑕᓂᑯ ᑭᑭ ᐱᒥ ᐃᑖᐱᐦᑕᒥᑕᐣ ᐊᓄᐦᒋ? ᑭᑭ ᐱᒥ ᒪᓯᓇᐦᐃᑲᐣ ᐅᒪ ᐊᑎᐦᑖᐧᐠ ᐅᒪ ᐊᔨᒧᐧᐃᐣ."
        },
        "sales": {
            "greeting": "ᑕᓂᓯ! ᓂᔭ ᑲᕌᓗᔅ, ᑭ WeedGo ᐊᑎᐧᐃᐧᑭᒫᐧ ᐧᐃᒋᐦᐃᐧᐃᐧᐣ. 👋\n\nᓂᑕᔭᐧᐣ ᐅᒪ ᒋ ᐧᐃᒋᐦᐃᑕᒥᑕᐣ ᒋ ᑭᔅᑫᓕᐦᑕᒪᐣ ᑕᓂᓯ WeedGo ᑭᑭ ᐱᒥ ᐊᓐᒋᑐᒋᑲᑌ ᑭ ᒪᔅᑫᑯᓯᐎᓇ. ᑭᔅᐱᐣ ᑭ ᐱᓕᐦᑕᑲᐧᐣ ᑎᐱᑕᐃᑲᓇ, ᐃᓇᑯᓂᑫᐧᐃᓇ ᐅᒪ ᐊᓐᒋᑐᒥᑲᐧᑭᐣ - ᓂᑕᔭᐧᐣ ᐅᒪ ᒋ ᓇᑯᑌᔭᐣ ᑲᑭᓇ ᑲᑭᑫᑕᒪᐧᐠ.\n\nᑭᑫᑯᐣ ᑭ ᐧᐃᑕᒪᐧᑫ ᒋ ᑭᔅᑫᓕᐦᑕᒪᐣ ᐊᐱ WeedGo?"
        }
    },
    "yue": {
        "assistant": {
            "greeting": "歡迎！今日我可以點樣幫到你？你可以打字或者用語音輸入。"
        },
        "sales": {
            "greeting": "你好！我係Carlos，你嘅WeedGo銷售助手。👋\n\n我喺度幫你了解WeedGo點樣可以改變你嘅大麻零售業務。無論你對價錢、功能感興趣，定係啱啱開始 - 我都喺度解答任何問題。\n\n你想了解WeedGo嘅咩？"
        }
    },
    "ta": {
        "assistant": {
            "greeting": "வரவேற்கிறோம்! இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்? நீங்கள் தட்டச்சு செய்யலாம் அல்லது குரல் உள்ளீட்டைப் பயன்படுத்தலாம்."
        },
        "sales": {
            "greeting": "வணக்கம்! நான் Carlos, உங்கள் WeedGo விற்பனை உதவியாளர். 👋\n\nWeedGo உங்கள் கஞ்சா சில்லறை வணிகத்தை எவ்வாறு மாற்ற முடியும் என்பதை கண்டறிய உங்களுக்கு உதவ நான் இங்கே இருக்கிறேன். நீங்கள் விலை, அம்சங்கள் பற்றி ஆர்வமாக இருந்தாலும் அல்லது இப்போதுதான் தொடங்கினாலும் - எந்த கேள்விக்கும் பதிலளிக்க நான் இங்கே இருக்கிறேன்.\n\nWeedGo பற்றி என்ன தெரிந்து கொள்ள விரும்புகிறீர்கள்?"
        }
    },
    "gu": {
        "assistant": {
            "greeting": "સ્વાગત છે! આજે હું તમને કેવી રીતે મદદ કરી શકું? તમે ટાઈપ કરી શકો છો અથવા વૉઇસ ઇનપુટ વાપરી શકો છો."
        },
        "sales": {
            "greeting": "નમસ્તે! હું Carlos છું, તમારો WeedGo વેચાણ સહાયક. 👋\n\nWeedGo તમારા કેનાબીસ રીટેલ બિઝનેસને કેવી રીતે બદલી શકે તે શોધવામાં હું તમને મદદ કરવા અહીં છું. તમે કિંમતો, સુવિધાઓ વિશે જાણવા માગતા હો અથવા હમણાં જ શરૂઆત કરી રહ્યા હો - કોઈપણ પ્રશ્નનો જવાબ આપવા હું અહીં છું.\n\nતમે WeedGo વિશે શું જાણવા માંગો છો?"
        }
    },
    "iu": {
        "assistant": {
            "greeting": "ᑐᙵᓱᕕᑦ! ᐅᓪᓗᒥ ᖃᓄᕐᓕ ᐃᑲᔪᖅᑎᓯᒍᓐᓇᕐᒪᖔ? ᑎᑎᕋᕈᓐᓇᖅᑐᑎ ᐅᕝᕙᓘᓐᓃᑦ ᓂᐱᒋᒃᓴᐃᓂᕐᒥᒃ ᐊᑐᕈᓐᓇᖅᑐᑎ."
        },
        "sales": {
            "greeting": "ᐊᐃ! ᐅᕙᖓ Carlos-ᒪᕐᖃᐃᓐᓇᕆᐊᖃᖅᑐᖅ, ᐃᓕᓐᓂᐊᖅᑎ WeedGo. 👋\n\nᐅᕙᖓ ᑕᕝᕙᓂ ᐃᑲᔪᕐᓂᐊᖅᖢᓂ ᓇᓗᓇᐃᖅᓯᓂᕐᒧᑦ WeedGo ᖃᓄᖅ ᐊᓯᔾᔨᖅᑎᑦᑎᔪᓐᓇᕐᒪᖔᑦ ᑭᓇᔭᖃᕐᓂᕐᒧᑦ ᐱᖁᔭᖅᑐᕐᓂᕐᒧᑦ. ᐃᓱᒪᒃᓴᖅᓯᐅᕈᑎᑦ ᐊᑭᓕᖅᓱᖅᑕᐅᓂᖏᓐᓂᒃ, ᐱᐅᓯᖏᓐᓂᒃ ᐅᕝᕙᓘᓐᓃᑦ ᐱᒋᐊᕐᓂᕐᒥᒃ - ᐅᕙᖓ ᑕᕝᕙᓂ ᑭᐅᓂᐊᖅᐳᖓ ᐊᐱᖅᑯᑎᒃᓴᓄᑦ.\n\nᓱᒧᑦ WeedGo ᖃᐅᔨᒪᔪᒪᕖᑦ?"
        }
    },
    "bn": {
        "assistant": {
            "greeting": "স্বাগতম! আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি? আপনি টাইপ করতে পারেন বা ভয়েস ইনপুট ব্যবহার করতে পারেন।"
        },
        "sales": {
            "greeting": "হ্যালো! আমি Carlos, আপনার WeedGo বিক্রয় সহায়ক। 👋\n\nWeedGo কীভাবে আপনার গাঁজা খুচরা ব্যবসাকে রূপান্তরিত করতে পারে তা আবিষ্কার করতে আমি এখানে আপনাকে সাহায্য করতে এসেছি। আপনি মূল্য, বৈশিষ্ট্য সম্পর্কে কৌতূহলী হন বা শুধু শুরু করছেন - যেকোনো প্রশ্নের উত্তর দিতে আমি এখানে আছি।\n\nআপনি WeedGo সম্পর্কে কী জানতে চান?"
        }
    },
    "so": {
        "assistant": {
            "greeting": "Soo dhawoow! Sidee baan maanta kaa caawin karaa? Waxaad qori kartaa ama isticmaali kartaa codka gelinta."
        },
        "sales": {
            "greeting": "Soo dhawoow! Waxaan ahay Carlos, kaaliyaha iibka WeedGo. 👋\n\nHalkan waxaan u joogaa inaan ku caawiyo inaad ogaato sida WeedGo uu u bedeli karo ganacsigaaga tafaariiqda canabiska. Hadii aad xiiso u qabto qiimaha, muuqaalada ama uun bilaabanayso - halkan ayaan u joogaa inaan ka jawaabo su'aal kasta.\n\nMaxaad jeclaan lahayd inaad ka ogaato WeedGo?"
        }
    }
}

def add_chat_translations():
    """Add chat greeting translations to all language directories"""

    base_dir = Path(__file__).parent.parent / "src" / "i18n" / "locales"

    for lang_code, translations in CHAT_TRANSLATIONS.items():
        chat_file = base_dir / lang_code / "chat.json"

        # Create directory if it doesn't exist
        chat_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Write the chat translations
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
                f.write('\n')

            print(f"✅ Created {lang_code}/chat.json")

        except Exception as e:
            print(f"❌ Error processing {lang_code}: {e}")

    print(f"\n{'='*80}")
    print(f"Chat translation propagation complete!")
    print(f"Created chat.json for {len(CHAT_TRANSLATIONS)} languages")
    print(f"{'='*80}")

if __name__ == "__main__":
    add_chat_translations()
