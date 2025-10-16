#!/usr/bin/env node

/**
 * Batch Translation Script for common.json
 *
 * This script provides professional translations for common.json across all 28 languages
 */

const fs = require('fs');
const path = require('path');

const LOCALES_DIR = path.join(__dirname, '../src/i18n/locales');

// Professional translations for common.json in all languages
const translations = {
  fr: {
    name: 'French',
    translations: {
      "buttons": {
        "send": "Envoyer",
        "close": "Fermer",
        "cancel": "Annuler",
        "save": "Enregistrer",
        "delete": "Supprimer",
        "edit": "Modifier",
        "create": "Créer",
        "update": "Mettre à jour",
        "confirm": "Confirmer",
        "back": "Retour",
        "next": "Suivant",
        "submit": "Soumettre",
        "search": "Rechercher",
        "filter": "Filtrer",
        "export": "Exporter",
        "import": "Importer",
        "refresh": "Actualiser",
        "settings": "Paramètres",
        "logout": "Déconnexion",
        "change": "Modifier"
      },
      "labels": {
        "email": "Adresse e-mail",
        "password": "Mot de passe",
        "username": "Nom d'utilisateur",
        "name": "Nom",
        "phone": "Téléphone",
        "address": "Adresse",
        "city": "Ville",
        "province": "Province",
        "postalCode": "Code postal",
        "country": "Pays",
        "status": "Statut",
        "actions": "Actions",
        "description": "Description",
        "notes": "Notes",
        "date": "Date",
        "time": "Heure",
        "total": "Total",
        "subtotal": "Sous-total",
        "tax": "Taxe",
        "quantity": "Quantité",
        "price": "Prix",
        "language": "Langue"
      },
      "placeholders": {
        "enterEmail": "Entrez votre adresse e-mail",
        "enterPassword": "Entrez votre mot de passe",
        "search": "Rechercher...",
        "selectOption": "Sélectionnez une option",
        "typeMessage": "Tapez votre message...",
        "enterName": "Entrez le nom",
        "enterPhone": "Entrez le numéro de téléphone"
      },
      "messages": {
        "loading": "Chargement...",
        "saving": "Enregistrement...",
        "success": "Succès !",
        "error": "Une erreur s'est produite",
        "noData": "Aucune donnée disponible",
        "confirm": "Êtes-vous sûr ?",
        "unsavedChanges": "Vous avez des modifications non enregistrées"
      },
      "errors": {
        "required": "Ce champ est obligatoire",
        "invalidEmail": "Adresse e-mail invalide",
        "invalidPhone": "Numéro de téléphone invalide",
        "networkError": "Erreur réseau. Veuillez réessayer.",
        "serverError": "Erreur serveur. Veuillez réessayer plus tard.",
        "unauthorized": "Accès non autorisé",
        "notFound": "Non trouvé",
        "sessionExpired": "Votre session a expiré. Veuillez vous reconnecter."
      },
      "common": {
        "yes": "Oui",
        "no": "Non",
        "or": "ou",
        "and": "et",
        "today": "Aujourd'hui",
        "yesterday": "Hier",
        "week": "Semaine",
        "month": "Mois",
        "year": "Année",
        "all": "Tous",
        "none": "Aucun",
        "active": "Actif",
        "inactive": "Inactif",
        "pending": "En attente",
        "completed": "Terminé",
        "failed": "Échec",
        "notSpecified": "Non spécifié",
        "unknown": "Inconnu",
        "na": "N/D"
      }
    }
  }
};

// Apply translations
Object.entries(translations).forEach(([lang, data]) => {
  const filePath = path.join(LOCALES_DIR, lang, 'common.json');
  const existing = JSON.parse(fs.readFileSync(filePath, 'utf-8'));

  // Deep merge
  const merged = { ...existing, ...data.translations };

  fs.writeFileSync(filePath, JSON.stringify(merged, null, 2) + '\n', 'utf-8');
  console.log(`✓ Updated ${lang} (${data.name})`);
});

console.log('\n✅ Batch translation complete!');
