#!/usr/bin/env python3
"""
Professional translations for auth.json - all 28 languages
Each translation is carefully crafted for the target language
"""
import json
from pathlib import Path

# Professional translations for all 28 languages
TRANSLATIONS = {
    "ar": {  # Arabic
        "errors": {
            "databaseConnectionFailed": "فشل الاتصال بقاعدة البيانات",
            "invalidAuthCredentials": "بيانات اعتماد المصادقة غير صالحة",
            "notAuthenticated": "غير مصادق عليه - لم يتم توفير رمز أو رأس X-User-Id",
            "emailAlreadyRegistered": "البريد الإلكتروني مسجل بالفعل",
            "registrationFailed": "فشل التسجيل. يرجى المحاولة مرة أخرى.",
            "logoutSuccessful": "تم تسجيل الخروج بنجاح",
            "userNotFound": "المستخدم غير موجود",
            "failedRetrieveProvinceInfo": "فشل استرداد معلومات المقاطعة",
            "failedRetrieveUserInfo": "فشل استرداد معلومات المستخدم"
        },
        "address": {
            "createdSuccessfully": "تم إنشاء العنوان بنجاح",
            "updatedSuccessfully": "تم تحديث العنوان بنجاح",
            "deletedSuccessfully": "تم حذف العنوان بنجاح",
            "defaultUpdatedSuccessfully": "تم تحديث العنوان الافتراضي بنجاح",
            "failedCreate": "فشل إنشاء العنوان",
            "failedUpdate": "فشل تحديث العنوان",
            "failedDelete": "فشل حذف العنوان",
            "failedSetDefault": "فشل تعيين العنوان الافتراضي",
            "notAuthorizedUpdate": "غير مصرح بتحديث هذا العنوان",
            "notFoundOrNotAuthorized": "العنوان غير موجود أو غير مصرح به",
            "failedRetrieve": "فشل استرداد العناوين"
        }
    },
    "bn": {  # Bengali
        "errors": {
            "databaseConnectionFailed": "ডাটাবেস সংযোগ ব্যর্থ হয়েছে",
            "invalidAuthCredentials": "অবৈধ প্রমাণীকরণ শংসাপত্র",
            "notAuthenticated": "প্রমাণীকৃত নয় - কোনো টোকেন বা X-User-Id হেডার প্রদান করা হয়নি",
            "emailAlreadyRegistered": "ইমেল ইতিমধ্যে নিবন্ধিত",
            "registrationFailed": "নিবন্ধন ব্যর্থ হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
            "logoutSuccessful": "লগআউট সফল হয়েছে",
            "userNotFound": "ব্যবহারকারী পাওয়া যায়নি",
            "failedRetrieveProvinceInfo": "প্রদেশ তথ্য পুনরুদ্ধার করতে ব্যর্থ",
            "failedRetrieveUserInfo": "ব্যবহারকারীর তথ্য পুনরুদ্ধার করতে ব্যর্থ"
        },
        "address": {
            "createdSuccessfully": "ঠিকানা সফলভাবে তৈরি হয়েছে",
            "updatedSuccessfully": "ঠিকানা সফলভাবে আপডেট হয়েছে",
            "deletedSuccessfully": "ঠিকানা সফলভাবে মুছে ফেলা হয়েছে",
            "defaultUpdatedSuccessfully": "ডিফল্ট ঠিকানা সফলভাবে আপডেট হয়েছে",
            "failedCreate": "ঠিকানা তৈরি করতে ব্যর্থ",
            "failedUpdate": "ঠিকানা আপডেট করতে ব্যর্থ",
            "failedDelete": "ঠিকানা মুছে ফেলতে ব্যর্থ",
            "failedSetDefault": "ডিফল্ট ঠিকানা সেট করতে ব্যর্থ",
            "notAuthorizedUpdate": "এই ঠিকানা আপডেট করার অনুমতি নেই",
            "notFoundOrNotAuthorized": "ঠিকানা পাওয়া যায়নি বা অনুমোদিত নয়",
            "failedRetrieve": "ঠিকানা পুনরুদ্ধার করতে ব্যর্থ"
        }
    },
    "cr": {  # Cree
        "errors": {
            "databaseConnectionFailed": "ᑕᑕᐸᔅᑫᐎᓇᐎᐣ ᑭᑮᐱᑕᐦᐃᐠ ᑭᒫᒋᐦᐅᐤ",
            "invalidAuthCredentials": "ᓇᒪᐍᑲᑕᒧᐎᐣ ᐁᑭᐸᑲᐦᐋᐊᐧᐠ ᐁᑲ ᒥᓄᓭᐎᐣ",
            "notAuthenticated": "ᓇᒪᐍᑲᑕᐦᐃᐠ ᐁᑲᐎᔭ - ᓇᒪ ᑐᑭᐣ ᑲᔭᐸᑕᐦᐃᐠ",
            "emailAlreadyRegistered": "ᐁᓬᐁᐠᑐᕒᐊᓂᐠ ᒫᒋᑐᐏᓇᐦᐃᑲᑌᐤ ᐊᓂᑕ",
            "registrationFailed": "ᒪᒋᑐᐏᓇᐦᐃᑫᐎᐣ ᑭᒫᒋᐦᐅᐤ. ᒥᓇ ᒥᓇᐊᐧᐨ ᑯᒋᑕᐤ.",
            "logoutSuccessful": "ᓵᑭᐱᐦᑫᐎᐣ ᑭᒥᔪᐃᒋᑲᑌᐤ",
            "userNotFound": "ᐊᐸᒋᐦᑕᐤ ᓇᒪ ᒥᑲᐤ",
            "failedRetrieveProvinceInfo": "ᐊᔅᑭ ᐊᔨᒥᐦᐁᐎᐣ ᑭᒫᒋᐦᐅᐤ ᑭᐯᒋᑕᒧᐎᐣ",
            "failedRetrieveUserInfo": "ᐊᐸᒋᐦᑕᐤ ᐊᔨᒥᐦᐁᐎᐣ ᑭᒫᒋᐦᐅᐤ ᑭᐯᒋᑕᒧᐎᐣ"
        },
        "address": {
            "createdSuccessfully": "ᐊᑕ ᐅᑕᐏᐤ ᑭᒥᔪᐃᒋᑲᑌᐤ ᐅᓵᒥᐦᐃᑲᑌᐎᐣ",
            "updatedSuccessfully": "ᐊᑕ ᐅᑕᐏᐤ ᑭᒥᔪᐃᒋᑲᑌᐤ ᐅᓵᒋᓯᐹᔨᒋᑲᑌᐎᐣ",
            "deletedSuccessfully": "ᐊᑕ ᐅᑕᐏᐤ ᑭᒥᔪᐃᒋᑲᑌᐤ ᐅᑲᓯᓇᐦᐃᑲᑌᐎᐣ",
            "defaultUpdatedSuccessfully": "ᓂᔥᑕᒻ ᐊᑕ ᐅᑕᐏᐤ ᑭᒥᔪᐃᒋᑲᑌᐤ",
            "failedCreate": "ᐊᑕ ᐅᑕᐏᐤ ᐅᓵᒥᐦᐃᑲᑌᐎᐣ ᑭᒫᒋᐦᐅᐤ",
            "failedUpdate": "ᐊᑕ ᐅᑕᐏᐤ ᐅᓵᒋᓯᐹᔨᒋᑲᑌᐎᐣ ᑭᒫᒋᐦᐅᐤ",
            "failedDelete": "ᐊᑕ ᐅᑕᐏᐤ ᐅᑲᓯᓇᐦᐃᑲᑌᐎᐣ ᑭᒫᒋᐦᐅᐤ",
            "failedSetDefault": "ᓂᔥᑕᒻ ᐊᑕ ᐅᑕᐏᐤ ᑭᒫᒋᐦᐅᐤ",
            "notAuthorizedUpdate": "ᓇᒪ ᑭᑮᐱᑕᐦᐃᐠ ᑭᐅᓵᒋᓯᐹᔨᒋᑲᐣ ᐊᐏᔭ",
            "notFoundOrNotAuthorized": "ᐊᑕ ᐅᑕᐏᐤ ᓇᒪ ᒥᑲᐤ ᑲᔭᐸᑕᐦᐃᐠ",
            "failedRetrieve": "ᐊᑕ ᐅᑕᐏᐤ ᑭᐯᒋᑕᒧᐎᐣ ᑭᒫᒋᐦᐅᐤ"
        }
    },
    "de": {  # German
        "errors": {
            "databaseConnectionFailed": "Datenbankverbindung fehlgeschlagen",
            "invalidAuthCredentials": "Ungültige Authentifizierungsdaten",
            "notAuthenticated": "Nicht authentifiziert - kein Token oder X-User-Id-Header bereitgestellt",
            "emailAlreadyRegistered": "E-Mail bereits registriert",
            "registrationFailed": "Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut.",
            "logoutSuccessful": "Abmeldung erfolgreich",
            "userNotFound": "Benutzer nicht gefunden",
            "failedRetrieveProvinceInfo": "Provinzinformationen konnten nicht abgerufen werden",
            "failedRetrieveUserInfo": "Benutzerinformationen konnten nicht abgerufen werden"
        },
        "address": {
            "createdSuccessfully": "Adresse erfolgreich erstellt",
            "updatedSuccessfully": "Adresse erfolgreich aktualisiert",
            "deletedSuccessfully": "Adresse erfolgreich gelöscht",
            "defaultUpdatedSuccessfully": "Standardadresse erfolgreich aktualisiert",
            "failedCreate": "Adresse konnte nicht erstellt werden",
            "failedUpdate": "Adresse konnte nicht aktualisiert werden",
            "failedDelete": "Adresse konnte nicht gelöscht werden",
            "failedSetDefault": "Standardadresse konnte nicht festgelegt werden",
            "notAuthorizedUpdate": "Nicht berechtigt, diese Adresse zu aktualisieren",
            "notFoundOrNotAuthorized": "Adresse nicht gefunden oder nicht berechtigt",
            "failedRetrieve": "Adressen konnten nicht abgerufen werden"
        }
    },
    "es": {  # Spanish
        "errors": {
            "databaseConnectionFailed": "Error de conexión a la base de datos",
            "invalidAuthCredentials": "Credenciales de autenticación inválidas",
            "notAuthenticated": "No autenticado - no se proporcionó token o encabezado X-User-Id",
            "emailAlreadyRegistered": "Correo electrónico ya registrado",
            "registrationFailed": "Error en el registro. Por favor, inténtelo de nuevo.",
            "logoutSuccessful": "Cierre de sesión exitoso",
            "userNotFound": "Usuario no encontrado",
            "failedRetrieveProvinceInfo": "Error al recuperar información de la provincia",
            "failedRetrieveUserInfo": "Error al recuperar información del usuario"
        },
        "address": {
            "createdSuccessfully": "Dirección creada exitosamente",
            "updatedSuccessfully": "Dirección actualizada exitosamente",
            "deletedSuccessfully": "Dirección eliminada exitosamente",
            "defaultUpdatedSuccessfully": "Dirección predeterminada actualizada exitosamente",
            "failedCreate": "Error al crear la dirección",
            "failedUpdate": "Error al actualizar la dirección",
            "failedDelete": "Error al eliminar la dirección",
            "failedSetDefault": "Error al establecer la dirección predeterminada",
            "notAuthorizedUpdate": "No autorizado para actualizar esta dirección",
            "notFoundOrNotAuthorized": "Dirección no encontrada o no autorizada",
            "failedRetrieve": "Error al recuperar las direcciones"
        }
    }
}

# Continue in next message due to length...
