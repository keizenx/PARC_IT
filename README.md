[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Stars](https://img.shields.io/github/stars/keizenx/PARC_IT?style=social)](https://github.com/keizenx/PARC_IT/stargazers)
[![Forks](https://img.shields.io/github/forks/keizenx/PARC_IT?style=social)](https://github.com/keizenx/PARC_IT/network/members)
[![Issues](https://img.shields.io/github/issues/keizenx/PARC_IT)](https://github.com/keizenx/PARC_IT/issues)
[![Twitter Follow](https://img.shields.io/twitter/follow/keizensberg?style=social)](https://x.com/keizensberg)

# PARC_IT: Gestion de Parc Informatique pour Odoo 18

PARC_IT est un module Odoo 18 orienté gestion de parc informatique: inventaire, tickets, interventions, contrats, SLA, portail client et suivi opérationnel.

## Fonctionnalités

- Gestion des équipements IT
- Gestion des logiciels et licences
- Gestion des incidents et tickets
- Gestion des interventions techniques
- Gestion des contrats de service
- Gestion des SLA
- Portail client (demandes, suivi, visibilité)
- Dashboard de supervision

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

## Prérequis

- Odoo 18.0
- Dépendances module:
  - `base`, `mail`, `portal`, `website`
  - `contacts`, `product`, `stock`
  - `account`, `helpdesk`
  - `rating`, `auth_signup`

## Installation

### 1. Cloner le module

```bash
cd /chemin/vers/odoo/custom_addons
git clone https://github.com/keizenx/PARC_IT.git
```

Windows PowerShell:

```powershell
cd E:\odoo-18.0+e.20250206\odoo\custom_addons
git clone https://github.com/keizenx/PARC_IT.git
```

### 2. Vérifier `odoo.conf`

```ini
addons_path = E:\odoo-18.0+e.20250206\odoo\addons,E:\odoo-18.0+e.20250206\odoo\custom_addons
```

### 3. Redémarrer Odoo

### 4. Mettre à jour la liste des apps / modules

Via interface:
- Apps -> Update Apps List

Via CLI:

```bash
odoo-bin -c /chemin/vers/odoo.conf -d <nom_base> -u PARC_IT
```

Exemple:

```powershell
.\venv\Scripts\python.exe odoo-bin -c odoo.conf -d odoo_new -u PARC_IT
```

### 5. Installer le module

Dans Apps, rechercher **Gestion de Parc Informatique** et installer.

## Structure du module

```text
PARC_IT/
├── assets/                        # Captures d'écran du module
├── controllers/                   # Points d'entrée web et API REST
│   ├── api.py                     # API REST
│   ├── main.py                    # Contrôleur principal
│   ├── portal.py                  # Gestion du portail client
│   └── website_controllers.py     # Contrôleurs website
├── data/                          # Données de configuration
│   ├── ir_sequence_data.xml
│   ├── it_park_email_templates.xml
│   ├── it_service_type_data.xml
│   └── it_ticket_category_data.xml
├── models/                        # Modèles de données
│   ├── hr_employee.py
│   ├── it_contract.py
│   ├── it_dashboard.py
│   ├── it_equipment.py
│   ├── it_incident.py
│   ├── it_intervention.py
│   ├── it_license.py
│   ├── it_service_request.py
│   ├── it_sla.py
│   ├── it_software.py
│   └── it_ticket.py
├── security/                      # Rôles, règles, ACL
│   ├── ir.model.access.csv
│   ├── it_security.xml
│   └── it_park_portal_rules.xml
├── static/                        # Ressources frontend
│   └── src/
│       ├── css/
│       ├── js/
│       └── scss/
├── utils/
│   └── url_utils.py
├── views/                         # Vues backend + templates portal/website
│   ├── it_contract_views.xml
│   ├── it_equipment_views.xml
│   ├── it_incident_views.xml
│   ├── it_intervention_views.xml
│   ├── it_park_portal_templates.xml
│   ├── it_ticket_views.xml
│   └── portal_templates.xml
├── wizards/                       # Assistants métiers
│   ├── assign_equipment_wizard.py
│   ├── it_incident_resolve_wizard.py
│   └── it_portal_user_wizard.py
├── __manifest__.py
└── README.md
```

## Author, Contributors, and License

- Author: PARC_IT Team
- Contributors: voir l'historique GitHub
- License: LGPL-3
