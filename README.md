# Gestion de Parc Informatique (IT Park Management)

Module Odoo 18.0 pour la gestion complète de parc informatique avec portail client intégré.

## Captures d'écran

### Interface principale
![Interface principale](assets/Screenshot%202025-05-13%20053148.png)

### Gestion des équipements
![Gestion des équipements](assets/Screenshot%202025-05-13%20053227.png)

### Portail client
![Portail client](assets/Screenshot%202025-05-13%20053244.png)

### Tickets de support
![Tickets de support](assets/Screenshot%202025-05-13%20053255.png)

### Tableaux de bord
![Tableaux de bord](assets/Screenshot%202025-05-13%20053334.png)

### Vue des interventions
![Vue des interventions](assets/Screenshot%202025-05-13%20053348.png)

### Formulaire de demande
![Formulaire de demande](assets/Screenshot%202025-05-13%20053402.png)

### Détails d'équipement
![Détails d'équipement](assets/Screenshot%202025-05-13%20053419.png)

## Fonctionnalités

- **Gestion d'équipements informatiques** : Inventaire complet du matériel informatique
- **Gestion des logiciels et licences** : Suivi des logiciels et de leurs licences
- **Gestion des contrats** : Suivi des contrats avec alertes d'échéance
- **Gestion des incidents** : Tickets de support et incidents
- **Gestion des interventions** : Planification et suivi d'interventions
- **Portail client** : Interface utilisateur pour les clients externes
- **Tableau de bord** : Visualisation des métriques clés
- **Accords de niveau de service (SLA)** : Définition et suivi des SLA

## Prérequis

- Odoo 18.0
- Modules dépendants:
  - Base, Mail, Portal, Website
  - Contacts, Product, Stock
  - Account, Helpdesk
  - Rating, Auth Signup

## Installation

### 1) Récupérer le module

Clonez le dépôt dans votre dossier `custom_addons`.

```bash
cd /chemin/vers/odoo/custom_addons
git clone https://github.com/keizenx/PARC_IT.git
```

Exemple Windows (PowerShell):

```powershell
cd E:\odoo-18.0+e.20250206\odoo\custom_addons
git clone https://github.com/keizenx/PARC_IT.git
```

### 2) Vérifier la configuration Odoo

Dans `odoo.conf`, vérifiez que `addons_path` contient bien les addons standards et `custom_addons`:

```ini
addons_path = E:\odoo-18.0+e.20250206\odoo\addons,E:\odoo-18.0+e.20250206\odoo\custom_addons
```

### 3) Redémarrer Odoo

Redémarrez le service Odoo pour prendre en compte le nouveau module.

### 4) Mettre à jour la liste des modules

- Interface: `Apps` -> `Update Apps List`
- Ou en ligne de commande:

```bash
odoo-bin -c /chemin/vers/odoo.conf -d <nom_base> -u PARC_IT
```

Exemple:

```powershell
.\venv\Scripts\python.exe odoo-bin -c odoo.conf -d odoo_new -u PARC_IT
```

### 5) Installer le module

Dans `Apps`, recherchez **Gestion de Parc Informatique** puis cliquez sur **Install**.

## Structure du module


```
PARC_IT/
├── assets/                      # Captures d'écran du module
├── controllers/                 # Points d'entrée web et API REST
│   ├── api.py                   # API REST
│   ├── main.py                  # Contrôleur principal
│   ├── portal.py                # Gestion du portail client
│   └── website_controllers.py   # Contrôleurs pour site web
├── data/                        # Données de configuration
│   ├── ir_sequence_data.xml     # Séquences d'identification
│   ├── it_park_email_templates.xml # Templates emails
│   ├── it_service_type_data.xml # Types de services prédéfinis
│   └── it_ticket_category_data.xml # Catégories de tickets
├── models/                      # Modèles de données
│   ├── hr_employee.py           # Extension employés
│   ├── it_contract.py           # Gestion des contrats
│   ├── it_dashboard.py          # Tableau de bord
│   ├── it_equipment.py          # Équipements informatiques
│   ├── it_incident.py           # Gestion des incidents
│   ├── it_intervention.py       # Interventions techniques
│   ├── it_license.py            # Licences logicielles
│   ├── it_service_request.py    # Demandes de service
│   ├── it_sla.py                # Accords de niveau de service
│   ├── it_software.py           # Logiciels
│   └── it_ticket.py             # Tickets de support
├── security/                    # Sécurité et droits d'accès
│   ├── ir.model.access.csv      # Droits d'accès aux modèles
│   ├── it_security.xml          # Règles de sécurité
│   └── it_park_portal_rules.xml # Règles pour le portail
├── static/                      # Ressources statiques
│   └── src/
│       ├── css/                 # Feuilles de style
│       ├── js/                  # Scripts JavaScript
│       └── scss/                # Styles SCSS
├── utils/                       # Utilitaires
│   └── url_utils.py             # Fonctions de manipulation d'URL
├── views/                       # Vues et templates
│   ├── it_contract_views.xml    # Vues des contrats
│   ├── it_equipment_views.xml   # Vues des équipements
│   ├── it_incident_views.xml    # Vues des incidents
│   ├── it_intervention_views.xml # Vues des interventions
│   ├── it_park_portal_templates.xml # Templates du portail
│   ├── it_ticket_views.xml      # Vues des tickets
│   └── portal_templates.xml     # Templates généraux du portail
└── wizards/                     # Assistants pour actions complexes
    ├── assign_equipment_wizard.py # Assistant d'attribution
    ├── it_incident_resolve_wizard.py # Résolution d'incident
    └── it_portal_user_wizard.py # Création d'utilisateur portail
```

## Scripts de correction

Le module contient plusieurs scripts de correction qui ont été utilisés pour résoudre des problèmes spécifiques:

- `fix_portal_access.py` : Corrige les problèmes d'accès au portail client
- `fix_portal_tickets_domain.py` : Corrige les domaines de filtrage des tickets
- `fix_import_datetime.py` : Ajoute les imports manquants du module datetime
- `fix_xml_error.py` : Corrige les erreurs de syntaxe XML dans les templates
- `run_diagnostics.py` : Diagnostic et identification des problèmes

## Corrections récentes

- Correction des routes du portail client (/my/tickets/create → /my/tickets/add)
- Amélioration de l'affichage des détails d'équipements et factures
- Correction de l'affichage des détails des contrats
- Ajout de boutons d'action manquants dans les listes
- Correction d'erreurs XML dans les templates du portail

## Licence

LGPL-3 
