#!/usr/bin/env python3
"""
Add navigation and role translations to all 28 languages
"""

import json
import os
from pathlib import Path

# Navigation translations for all 28 languages
TRANSLATIONS = {
    "en": {
        "navigation": {
            "dashboard": "Dashboard",
            "apps": "Apps",
            "organization": "Organization",
            "tenants": "Tenants",
            "products": "Products",
            "inventory": "Inventory",
            "accessories": "Accessories",
            "orders": "Orders",
            "customers": "Customers",
            "purchaseOrders": "Purchase Orders",
            "promotions": "Promotions",
            "recommendations": "Recommendations",
            "communications": "Communications",
            "deliveries": "Deliveries",
            "aiConfiguration": "AI Configuration",
            "provincialCatalog": "Provincial Catalog",
            "database": "Database",
            "systemLogs": "System Logs"
        },
        "roles": {
            "superAdmin": "Super Admin",
            "tenantAdmin": "Tenant Admin",
            "storeManager": "Store Manager",
            "staff": "Staff",
            "user": "User"
        }
    },
    "es": {
        "navigation": {
            "dashboard": "Panel de Control",
            "apps": "Aplicaciones",
            "organization": "Organización",
            "tenants": "Inquilinos",
            "products": "Productos",
            "inventory": "Inventario",
            "accessories": "Accesorios",
            "orders": "Pedidos",
            "customers": "Clientes",
            "purchaseOrders": "Órdenes de Compra",
            "promotions": "Promociones",
            "recommendations": "Recomendaciones",
            "communications": "Comunicaciones",
            "deliveries": "Entregas",
            "aiConfiguration": "Configuración de IA",
            "provincialCatalog": "Catálogo Provincial",
            "database": "Base de Datos",
            "systemLogs": "Registros del Sistema"
        },
        "roles": {
            "superAdmin": "Super Administrador",
            "tenantAdmin": "Administrador de Inquilino",
            "storeManager": "Gerente de Tienda",
            "staff": "Personal",
            "user": "Usuario"
        }
    },
    "fr": {
        "navigation": {
            "dashboard": "Tableau de Bord",
            "apps": "Applications",
            "organization": "Organisation",
            "tenants": "Locataires",
            "products": "Produits",
            "inventory": "Inventaire",
            "accessories": "Accessoires",
            "orders": "Commandes",
            "customers": "Clients",
            "purchaseOrders": "Bons de Commande",
            "promotions": "Promotions",
            "recommendations": "Recommandations",
            "communications": "Communications",
            "deliveries": "Livraisons",
            "aiConfiguration": "Configuration IA",
            "provincialCatalog": "Catalogue Provincial",
            "database": "Base de Données",
            "systemLogs": "Journaux Système"
        },
        "roles": {
            "superAdmin": "Super Administrateur",
            "tenantAdmin": "Administrateur Locataire",
            "storeManager": "Gestionnaire de Magasin",
            "staff": "Personnel",
            "user": "Utilisateur"
        }
    },
    "zh": {
        "navigation": {
            "dashboard": "仪表板",
            "apps": "应用程序",
            "organization": "组织",
            "tenants": "租户",
            "products": "产品",
            "inventory": "库存",
            "accessories": "配件",
            "orders": "订单",
            "customers": "客户",
            "purchaseOrders": "采购订单",
            "promotions": "促销",
            "recommendations": "推荐",
            "communications": "通讯",
            "deliveries": "配送",
            "aiConfiguration": "AI配置",
            "provincialCatalog": "省级目录",
            "database": "数据库",
            "systemLogs": "系统日志"
        },
        "roles": {
            "superAdmin": "超级管理员",
            "tenantAdmin": "租户管理员",
            "storeManager": "门店经理",
            "staff": "员工",
            "user": "用户"
        }
    },
    "ar": {
        "navigation": {
            "dashboard": "لوحة التحكم",
            "apps": "التطبيقات",
            "organization": "المنظمة",
            "tenants": "المستأجرون",
            "products": "المنتجات",
            "inventory": "المخزون",
            "accessories": "الملحقات",
            "orders": "الطلبات",
            "customers": "العملاء",
            "purchaseOrders": "طلبات الشراء",
            "promotions": "العروض الترويجية",
            "recommendations": "التوصيات",
            "communications": "الاتصالات",
            "deliveries": "التسليمات",
            "aiConfiguration": "تكوين الذكاء الاصطناعي",
            "provincialCatalog": "الكتالوج الإقليمي",
            "database": "قاعدة البيانات",
            "systemLogs": "سجلات النظام"
        },
        "roles": {
            "superAdmin": "مسؤول متقدم",
            "tenantAdmin": "مسؤول المستأجر",
            "storeManager": "مدير المتجر",
            "staff": "الموظفين",
            "user": "مستخدم"
        }
    },
    "hi": {
        "navigation": {
            "dashboard": "डैशबोर्ड",
            "apps": "ऐप्स",
            "organization": "संगठन",
            "tenants": "किरायेदार",
            "products": "उत्पाद",
            "inventory": "इन्वेंटरी",
            "accessories": "एक्सेसरीज़",
            "orders": "ऑर्डर",
            "customers": "ग्राहक",
            "purchaseOrders": "क्रय आदेश",
            "promotions": "प्रचार",
            "recommendations": "सिफारिशें",
            "communications": "संचार",
            "deliveries": "डिलीवरी",
            "aiConfiguration": "AI कॉन्फ़िगरेशन",
            "provincialCatalog": "प्रांतीय कैटलॉग",
            "database": "डेटाबेस",
            "systemLogs": "सिस्टम लॉग्स"
        },
        "roles": {
            "superAdmin": "सुपर एडमिन",
            "tenantAdmin": "किरायेदार एडमिन",
            "storeManager": "स्टोर मैनेजर",
            "staff": "कर्मचारी",
            "user": "उपयोगकर्ता"
        }
    },
    "pa": {
        "navigation": {
            "dashboard": "ਡੈਸ਼ਬੋਰਡ",
            "apps": "ਐਪਸ",
            "organization": "ਸੰਗਠਨ",
            "tenants": "ਕਿਰਾਏਦਾਰ",
            "products": "ਉਤਪਾਦ",
            "inventory": "ਇਨਵੈਂਟਰੀ",
            "accessories": "ਐਕਸੈਸਰੀਜ਼",
            "orders": "ਆਰਡਰ",
            "customers": "ਗਾਹਕ",
            "purchaseOrders": "ਖਰੀਦ ਆਰਡਰ",
            "promotions": "ਪ੍ਰਮੋਸ਼ਨ",
            "recommendations": "ਸਿਫਾਰਸ਼ਾਂ",
            "communications": "ਸੰਚਾਰ",
            "deliveries": "ਡਿਲੀਵਰੀ",
            "aiConfiguration": "AI ਸੰਰਚਨਾ",
            "provincialCatalog": "ਸੂਬਾਈ ਕੈਟਲਾਗ",
            "database": "ਡੇਟਾਬੇਸ",
            "systemLogs": "ਸਿਸਟਮ ਲੌਗਸ"
        },
        "roles": {
            "superAdmin": "ਸੁਪਰ ਐਡਮਿਨ",
            "tenantAdmin": "ਕਿਰਾਏਦਾਰ ਐਡਮਿਨ",
            "storeManager": "ਸਟੋਰ ਮੈਨੇਜਰ",
            "staff": "ਸਟਾਫ",
            "user": "ਯੂਜ਼ਰ"
        }
    },
    "tl": {
        "navigation": {
            "dashboard": "Dashboard",
            "apps": "Mga App",
            "organization": "Organisasyon",
            "tenants": "Mga Umuupa",
            "products": "Mga Produkto",
            "inventory": "Imbentaryo",
            "accessories": "Mga Aksesorya",
            "orders": "Mga Order",
            "customers": "Mga Kostumer",
            "purchaseOrders": "Mga Purchase Order",
            "promotions": "Mga Promosyon",
            "recommendations": "Mga Rekomendasyon",
            "communications": "Komunikasyon",
            "deliveries": "Mga Paghahatid",
            "aiConfiguration": "Pagsasaayos ng AI",
            "provincialCatalog": "Catalog ng Probinsya",
            "database": "Database",
            "systemLogs": "Mga System Log"
        },
        "roles": {
            "superAdmin": "Super Admin",
            "tenantAdmin": "Tenant Admin",
            "storeManager": "Store Manager",
            "staff": "Staff",
            "user": "User"
        }
    },
    # Add more languages as needed (continuing with remaining 20 languages)
    "it": {"navigation": {"dashboard": "Cruscotto", "apps": "App", "organization": "Organizzazione", "tenants": "Inquilini", "products": "Prodotti", "inventory": "Inventario", "accessories": "Accessori", "orders": "Ordini", "customers": "Clienti", "purchaseOrders": "Ordini di Acquisto", "promotions": "Promozioni", "recommendations": "Raccomandazioni", "communications": "Comunicazioni", "deliveries": "Consegne", "aiConfiguration": "Configurazione IA", "provincialCatalog": "Catalogo Provinciale", "database": "Database", "systemLogs": "Log di Sistema"}, "roles": {"superAdmin": "Super Amministratore", "tenantAdmin": "Amministratore Inquilino", "storeManager": "Responsabile Negozio", "staff": "Personale", "user": "Utente"}},
    "de": {"navigation": {"dashboard": "Dashboard", "apps": "Apps", "organization": "Organisation", "tenants": "Mieter", "products": "Produkte", "inventory": "Inventar", "accessories": "Zubehör", "orders": "Bestellungen", "customers": "Kunden", "purchaseOrders": "Bestellungen", "promotions": "Werbeaktionen", "recommendations": "Empfehlungen", "communications": "Kommunikation", "deliveries": "Lieferungen", "aiConfiguration": "KI-Konfiguration", "provincialCatalog": "Provinzkatalog", "database": "Datenbank", "systemLogs": "Systemprotokolle"}, "roles": {"superAdmin": "Super-Administrator", "tenantAdmin": "Mieter-Administrator", "storeManager": "Filialleiter", "staff": "Personal", "user": "Benutzer"}},
    "pt": {"navigation": {"dashboard": "Painel", "apps": "Aplicativos", "organization": "Organização", "tenants": "Inquilinos", "products": "Produtos", "inventory": "Inventário", "accessories": "Acessórios", "orders": "Pedidos", "customers": "Clientes", "purchaseOrders": "Ordens de Compra", "promotions": "Promoções", "recommendations": "Recomendações", "communications": "Comunicações", "deliveries": "Entregas", "aiConfiguration": "Configuração de IA", "provincialCatalog": "Catálogo Provincial", "database": "Banco de Dados", "systemLogs": "Logs do Sistema"}, "roles": {"superAdmin": "Super Administrador", "tenantAdmin": "Administrador de Inquilino", "storeManager": "Gerente de Loja", "staff": "Equipe", "user": "Usuário"}},
    "fa": {"navigation": {"dashboard": "داشبورد", "apps": "برنامه‌ها", "organization": "سازمان", "tenants": "مستأجران", "products": "محصولات", "inventory": "موجودی", "accessories": "لوازم جانبی", "orders": "سفارشات", "customers": "مشتریان", "purchaseOrders": "سفارشات خرید", "promotions": "تبلیغات", "recommendations": "توصیه‌ها", "communications": "ارتباطات", "deliveries": "تحویل‌ها", "aiConfiguration": "پیکربندی هوش مصنوعی", "provincialCatalog": "کاتالوگ استانی", "database": "پایگاه داده", "systemLogs": "گزارش‌های سیستم"}, "roles": {"superAdmin": "مدیر ارشد", "tenantAdmin": "مدیر مستأجر", "storeManager": "مدیر فروشگاه", "staff": "کارکنان", "user": "کاربر"}},
    "uk": {"navigation": {"dashboard": "Панель", "apps": "Додатки", "organization": "Організація", "tenants": "Орендарі", "products": "Продукти", "inventory": "Інвентар", "accessories": "Аксесуари", "orders": "Замовлення", "customers": "Клієнти", "purchaseOrders": "Замовлення на купівлю", "promotions": "Акції", "recommendations": "Рекомендації", "communications": "Комунікації", "deliveries": "Доставки", "aiConfiguration": "Налаштування ШІ", "provincialCatalog": "Провінційний каталог", "database": "База даних", "systemLogs": "Системні журнали"}, "roles": {"superAdmin": "Супер адміністратор", "tenantAdmin": "Адміністратор орендаря", "storeManager": "Менеджер магазину", "staff": "Персонал", "user": "Користувач"}},
    "pl": {"navigation": {"dashboard": "Panel", "apps": "Aplikacje", "organization": "Organizacja", "tenants": "Najemcy", "products": "Produkty", "inventory": "Inwentarz", "accessories": "Akcesoria", "orders": "Zamówienia", "customers": "Klienci", "purchaseOrders": "Zamówienia zakupu", "promotions": "Promocje", "recommendations": "Rekomendacje", "communications": "Komunikacja", "deliveries": "Dostawy", "aiConfiguration": "Konfiguracja AI", "provincialCatalog": "Katalog wojewódzki", "database": "Baza danych", "systemLogs": "Logi systemowe"}, "roles": {"superAdmin": "Super administrator", "tenantAdmin": "Administrator najemcy", "storeManager": "Kierownik sklepu", "staff": "Personel", "user": "Użytkownik"}},
    "vi": {"navigation": {"dashboard": "Bảng điều khiển", "apps": "Ứng dụng", "organization": "Tổ chức", "tenants": "Người thuê", "products": "Sản phẩm", "inventory": "Kho hàng", "accessories": "Phụ kiện", "orders": "Đơn hàng", "customers": "Khách hàng", "purchaseOrders": "Đơn đặt hàng", "promotions": "Khuyến mãi", "recommendations": "Đề xuất", "communications": "Truyền thông", "deliveries": "Giao hàng", "aiConfiguration": "Cấu hình AI", "provincialCatalog": "Danh mục tỉnh", "database": "Cơ sở dữ liệu", "systemLogs": "Nhật ký hệ thống"}, "roles": {"superAdmin": "Quản trị viên cấp cao", "tenantAdmin": "Quản trị viên người thuê", "storeManager": "Quản lý cửa hàng", "staff": "Nhân viên", "user": "Người dùng"}},
    "ko": {"navigation": {"dashboard": "대시보드", "apps": "앱", "organization": "조직", "tenants": "세입자", "products": "제품", "inventory": "재고", "accessories": "액세서리", "orders": "주문", "customers": "고객", "purchaseOrders": "구매 주문", "promotions": "프로모션", "recommendations": "추천", "communications": "통신", "deliveries": "배송", "aiConfiguration": "AI 구성", "provincialCatalog": "지방 카탈로그", "database": "데이터베이스", "systemLogs": "시스템 로그"}, "roles": {"superAdmin": "슈퍼 관리자", "tenantAdmin": "테넌트 관리자", "storeManager": "스토어 매니저", "staff": "직원", "user": "사용자"}},
    "ja": {"navigation": {"dashboard": "ダッシュボード", "apps": "アプリ", "organization": "組織", "tenants": "テナント", "products": "製品", "inventory": "在庫", "accessories": "アクセサリー", "orders": "注文", "customers": "顧客", "purchaseOrders": "発注書", "promotions": "プロモーション", "recommendations": "おすすめ", "communications": "コミュニケーション", "deliveries": "配達", "aiConfiguration": "AI設定", "provincialCatalog": "州のカタログ", "database": "データベース", "systemLogs": "システムログ"}, "roles": {"superAdmin": "スーパー管理者", "tenantAdmin": "テナント管理者", "storeManager": "店舗マネージャー", "staff": "スタッフ", "user": "ユーザー"}},
    "he": {"navigation": {"dashboard": "לוח בקרה", "apps": "אפליקציות", "organization": "ארגון", "tenants": "דיירים", "products": "מוצרים", "inventory": "מלאי", "accessories": "אביזרים", "orders": "הזמנות", "customers": "לקוחות", "purchaseOrders": "הזמנות רכש", "promotions": "מבצעים", "recommendations": "המלצות", "communications": "תקשורת", "deliveries": "משלוחים", "aiConfiguration": "תצורת AI", "provincialCatalog": "קטלוג מחוזי", "database": "מסד נתונים", "systemLogs": "יומני מערכת"}, "roles": {"superAdmin": "מנהל על", "tenantAdmin": "מנהל דייר", "storeManager": "מנהל חנות", "staff": "צוות", "user": "משתמש"}},
    "ur": {"navigation": {"dashboard": "ڈیش بورڈ", "apps": "ایپس", "organization": "تنظیم", "tenants": "کرایہ دار", "products": "مصنوعات", "inventory": "انوینٹری", "accessories": "لوازمات", "orders": "آرڈرز", "customers": "صارفین", "purchaseOrders": "خریداری کے آرڈرز", "promotions": "پروموشنز", "recommendations": "سفارشات", "communications": "مواصلات", "deliveries": "ڈیلیوری", "aiConfiguration": "AI کنفیگریشن", "provincialCatalog": "صوبائی کیٹلاگ", "database": "ڈیٹا بیس", "systemLogs": "سسٹم لاگز"}, "roles": {"superAdmin": "سپر ایڈمن", "tenantAdmin": "ٹینینٹ ایڈمن", "storeManager": "اسٹور مینیجر", "staff": "عملہ", "user": "صارف"}},
    "ru": {"navigation": {"dashboard": "Панель", "apps": "Приложения", "organization": "Организация", "tenants": "Арендаторы", "products": "Продукты", "inventory": "Инвентарь", "accessories": "Аксессуары", "orders": "Заказы", "customers": "Клиенты", "purchaseOrders": "Заказы на покупку", "promotions": "Акции", "recommendations": "Рекомендации", "communications": "Коммуникации", "deliveries": "Доставки", "aiConfiguration": "Настройка ИИ", "provincialCatalog": "Провинциальный каталог", "database": "База данных", "systemLogs": "Системные журналы"}, "roles": {"superAdmin": "Суперадминистратор", "tenantAdmin": "Администратор арендатора", "storeManager": "Менеджер магазина", "staff": "Персонал", "user": "Пользователь"}},
    "el": {"navigation": {"dashboard": "Πίνακας ελέγχου", "apps": "Εφαρμογές", "organization": "Οργανισμός", "tenants": "Ενοικιαστές", "products": "Προϊόντα", "inventory": "Απογραφή", "accessories": "Αξεσουάρ", "orders": "Παραγγελίες", "customers": "Πελάτες", "purchaseOrders": "Παραγγελίες αγοράς", "promotions": "Προωθήσεις", "recommendations": "Συστάσεις", "communications": "Επικοινωνίες", "deliveries": "Παραδόσεις", "aiConfiguration": "Διαμόρφωση AI", "provincialCatalog": "Επαρχιακός κατάλογος", "database": "Βάση δεδομένων", "systemLogs": "Αρχεία συστήματος"}, "roles": {"superAdmin": "Υπερδιαχειριστής", "tenantAdmin": "Διαχειριστής ενοικιαστή", "storeManager": "Διευθυντής καταστήματος", "staff": "Προσωπικό", "user": "Χρήστης"}},
    "ro": {"navigation": {"dashboard": "Panou", "apps": "Aplicații", "organization": "Organizație", "tenants": "Chiriași", "products": "Produse", "inventory": "Inventar", "accessories": "Accesorii", "orders": "Comenzi", "customers": "Clienți", "purchaseOrders": "Comenzi de achiziție", "promotions": "Promoții", "recommendations": "Recomandări", "communications": "Comunicări", "deliveries": "Livrări", "aiConfiguration": "Configurare AI", "provincialCatalog": "Catalog provincial", "database": "Bază de date", "systemLogs": "Jurnale de sistem"}, "roles": {"superAdmin": "Super administrator", "tenantAdmin": "Administrator chiriaș", "storeManager": "Manager magazin", "staff": "Personal", "user": "Utilizator"}},
    "nl": {"navigation": {"dashboard": "Dashboard", "apps": "Apps", "organization": "Organisatie", "tenants": "Huurders", "products": "Producten", "inventory": "Voorraad", "accessories": "Accessoires", "orders": "Bestellingen", "customers": "Klanten", "purchaseOrders": "Inkooporders", "promotions": "Promoties", "recommendations": "Aanbevelingen", "communications": "Communicatie", "deliveries": "Leveringen", "aiConfiguration": "AI-configuratie", "provincialCatalog": "Provinciale catalogus", "database": "Database", "systemLogs": "Systeemlogs"}, "roles": {"superAdmin": "Superbeheerder", "tenantAdmin": "Huurderbeheerder", "storeManager": "Winkelmanager", "staff": "Personeel", "user": "Gebruiker"}},
    "hu": {"navigation": {"dashboard": "Irányítópult", "apps": "Alkalmazások", "organization": "Szervezet", "tenants": "Bérlők", "products": "Termékek", "inventory": "Készlet", "accessories": "Kiegészítők", "orders": "Rendelések", "customers": "Ügyfelek", "purchaseOrders": "Beszerzési rendelések", "promotions": "Promóciók", "recommendations": "Ajánlások", "communications": "Kommunikáció", "deliveries": "Szállítások", "aiConfiguration": "AI konfiguráció", "provincialCatalog": "Tartományi katalógus", "database": "Adatbázis", "systemLogs": "Rendszernaplók"}, "roles": {"superAdmin": "Főrendszergazda", "tenantAdmin": "Bérlői adminisztrátor", "storeManager": "Üzletvezető", "staff": "Személyzet", "user": "Felhasználó"}},
    "cs": {"navigation": {"dashboard": "Přehled", "apps": "Aplikace", "organization": "Organizace", "tenants": "Nájemci", "products": "Produkty", "inventory": "Inventář", "accessories": "Příslušenství", "orders": "Objednávky", "customers": "Zákazníci", "purchaseOrders": "Nákupní objednávky", "promotions": "Propagace", "recommendations": "Doporučení", "communications": "Komunikace", "deliveries": "Dodávky", "aiConfiguration": "Konfigurace AI", "provincialCatalog": "Provinční katalog", "database": "Databáze", "systemLogs": "Systémové protokoly"}, "roles": {"superAdmin": "Super správce", "tenantAdmin": "Správce nájemce", "storeManager": "Manažer obchodu", "staff": "Personál", "user": "Uživatel"}},
    "sv": {"navigation": {"dashboard": "Instrumentpanel", "apps": "Appar", "organization": "Organisation", "tenants": "Hyresgäster", "products": "Produkter", "inventory": "Lager", "accessories": "Tillbehör", "orders": "Beställningar", "customers": "Kunder", "purchaseOrders": "Inköpsorder", "promotions": "Kampanjer", "recommendations": "Rekommendationer", "communications": "Kommunikation", "deliveries": "Leveranser", "aiConfiguration": "AI-konfiguration", "provincialCatalog": "Provinskatalog", "database": "Databas", "systemLogs": "Systemloggar"}, "roles": {"superAdmin": "Superadministratör", "tenantAdmin": "Hyresgästadministratör", "storeManager": "Butikschef", "staff": "Personal", "user": "Användare"}},
    "fi": {"navigation": {"dashboard": "Hallintapaneeli", "apps": "Sovellukset", "organization": "Organisaatio", "tenants": "Vuokralaiset", "products": "Tuotteet", "inventory": "Varasto", "accessories": "Lisävarusteet", "orders": "Tilaukset", "customers": "Asiakkaat", "purchaseOrders": "Ostotilaukset", "promotions": "Kampanjat", "recommendations": "Suositukset", "communications": "Viestintä", "deliveries": "Toimitukset", "aiConfiguration": "AI-määritys", "provincialCatalog": "Maakunnallinen luettelo", "database": "Tietokanta", "systemLogs": "Järjestelmälokit"}, "roles": {"superAdmin": "Pääkäyttäjä", "tenantAdmin": "Vuokralaisen järjestelmänvalvoja", "storeManager": "Myymäläpäällikkö", "staff": "Henkilökunta", "user": "Käyttäjä"}},
    "tr": {"navigation": {"dashboard": "Gösterge Paneli", "apps": "Uygulamalar", "organization": "Organizasyon", "tenants": "Kiracılar", "products": "Ürünler", "inventory": "Envanter", "accessories": "Aksesuarlar", "orders": "Siparişler", "customers": "Müşteriler", "purchaseOrders": "Satın Alma Siparişleri", "promotions": "Promosyonlar", "recommendations": "Öneriler", "communications": "İletişim", "deliveries": "Teslimatlar", "aiConfiguration": "AI Yapılandırması", "provincialCatalog": "İl Kataloğu", "database": "Veritabanı", "systemLogs": "Sistem Günlükleri"}, "roles": {"superAdmin": "Süper Yönetici", "tenantAdmin": "Kiracı Yöneticisi", "storeManager": "Mağaza Müdürü", "staff": "Personel", "user": "Kullanıcı"}},
    "da": {"navigation": {"dashboard": "Dashboard", "apps": "Apps", "organization": "Organisation", "tenants": "Lejere", "products": "Produkter", "inventory": "Lager", "accessories": "Tilbehør", "orders": "Ordrer", "customers": "Kunder", "purchaseOrders": "Indkøbsordrer", "promotions": "Kampagner", "recommendations": "Anbefalinger", "communications": "Kommunikation", "deliveries": "Leveringer", "aiConfiguration": "AI-konfiguration", "provincialCatalog": "Provinskatalog", "database": "Database", "systemLogs": "Systemlogs"}, "roles": {"superAdmin": "Superadministrator", "tenantAdmin": "Lejeradministrator", "storeManager": "Butikschef", "staff": "Personale", "user": "Bruger"}},
    "no": {"navigation": {"dashboard": "Dashboard", "apps": "Apper", "organization": "Organisasjon", "tenants": "Leietakere", "products": "Produkter", "inventory": "Varelager", "accessories": "Tilbehør", "orders": "Bestillinger", "customers": "Kunder", "purchaseOrders": "Innkjøpsordre", "promotions": "Kampanjer", "recommendations": "Anbefalinger", "communications": "Kommunikasjon", "deliveries": "Leveranser", "aiConfiguration": "AI-konfigurasjon", "provincialCatalog": "Provinskatalog", "database": "Database", "systemLogs": "Systemlogger"}, "roles": {"superAdmin": "Superadministrator", "tenantAdmin": "Leietakeradministrator", "storeManager": "Butikksjef", "staff": "Personale", "user": "Bruker"}},
    "cr": {"navigation": {"dashboard": "ᑕᐸᒋᑫᐎᐣ ᑕᐱᐸᐦᐋᑲᐣ", "apps": "ᐊᐱᔑᒧᐃᐧᓇ", "organization": "ᐁᑲᐧ ᐃᑐᒋᑫᐎᐣ", "tenants": "ᑭᑭᐸᒋᐦᐅᑲᑌᒃ", "products": "ᑭᒋᐸᒋᑫᐎᓇ", "inventory": "ᑭᒋ ᑕᐱᔑᓇᐦᐄᑫᐎᓇ", "accessories": "ᑭᒋ ᐃᔑᓇᐦᐄᑫᐎᓇ", "orders": "ᑭᐸᒋᐦᐅᐎᓇ", "customers": "ᑭᑮ ᑭᔑᐱᓂᒃ", "purchaseOrders": "ᑭᐸᒋᐦᐅᐎᓇ ᑭᔑᐱᓇᒃ", "promotions": "ᑭᒋ ᐃᔑᓇᐦᐄᑫᐎᓇ", "recommendations": "ᑭᒋ ᐃᔑᓇᐦᐄᑫᐎᓇ", "communications": "ᑭᑮ ᑕᐱᐸᐦᐋᑲᓂᐎᓇ", "deliveries": "ᑭᒋ ᐱᒥᐯᐦᐄᑫᐎᓇ", "aiConfiguration": "AI ᑭᒋ ᐃᔑᓇᐦᐄᑫᐎᓇ", "provincialCatalog": "ᑭᒋ ᑕᐱᔑᓇᐦᐄᑫᐎᓇ", "database": "ᑭᒋ ᑕᐱᐸᐦᐋᑲᓂᐎᓇ", "systemLogs": "ᑭᒋ ᑕᐱᐸᐦᐋᑲᓂᐎᓇ"}, "roles": {"superAdmin": "ᑭᒋ ᐅᑭᒪᐎᐣ", "tenantAdmin": "ᑭᑮ ᐅᑭᒪᐎᐣ", "storeManager": "ᑭᒋ ᑕᐸᒋᑫᐎᐣ", "staff": "ᐊᓂᔑᓂᓂᐎᐊᒃ", "user": "ᐊᐸᒋᐦᑕᐎᐣ"}}
}

def add_translations():
    """Add navigation and role translations to all language files"""

    base_dir = Path(__file__).parent.parent / "src" / "i18n" / "locales"

    for lang_code, translations in TRANSLATIONS.items():
        common_file = base_dir / lang_code / "common.json"

        if not common_file.exists():
            print(f"⚠️  Skipping {lang_code} - file not found: {common_file}")
            continue

        try:
            # Read existing file
            with open(common_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Add/update navigation and roles sections
            data['navigation'] = translations['navigation']
            data['roles'] = translations['roles']

            # Write back with pretty formatting
            with open(common_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')  # Add trailing newline

            print(f"✅ Updated {lang_code}/common.json")

        except Exception as e:
            print(f"❌ Error processing {lang_code}: {e}")

    print(f"\n{'='*80}")
    print(f"Translation propagation complete!")
    print(f"{'='*80}")

if __name__ == "__main__":
    add_translations()
