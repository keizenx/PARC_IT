# Ce script est destiné à être exécuté depuis le shell Odoo
# Commande: odoo shell -c odoo.conf < custom_addons/it__park/check_tickets.py

import logging
from datetime import datetime

# Log dans le terminal et dans le fichier de log
print(f"===== DIAGNOSTIC DES TICKETS {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")

# 1. Vérifier tous les tickets dans la base de données
all_tickets = env['it.ticket'].search([])
print(f"Nombre total de tickets: {len(all_tickets)}")

# 2. Afficher les détails de chaque ticket
for ticket in all_tickets:
    print(f"Ticket ID: {ticket.id}, Référence: {ticket.reference}, Nom: {ticket.name}")
    print(f"    Client: {ticket.client_id.name} (ID: {ticket.client_id.id})")
    print(f"    Partner: {ticket.partner_id.name} (ID: {ticket.partner_id.id})")
    print(f"    State: {ticket.state}")
    print(f"    Commercial Partner ID du client: {ticket.client_id.commercial_partner_id.id}")
    print(f"    Commercial Partner ID du partenaire: {ticket.partner_id.commercial_partner_id.id}")

# 3. Vérifier les utilisateurs du portail
portal_users = env['res.users'].search([('share', '=', True)])
print(f"\nUtilisateurs du portail: {len(portal_users)}")

# 4. Pour chaque utilisateur du portail, vérifier ses tickets
for user in portal_users:
    print(f"\nUser: {user.name} (ID: {user.id}, Login: {user.login})")
    print(f"    Partner ID: {user.partner_id.id}")
    print(f"    Commercial Partner ID: {user.partner_id.commercial_partner_id.id}")
    
    # Domaine de recherche pour les tickets de cet utilisateur
    domain = ['|', 
        ('client_id', '=', user.partner_id.commercial_partner_id.id),
        ('partner_id', '=', user.partner_id.commercial_partner_id.id)
    ]
    
    # Tickets avec le domaine original
    tickets = env['it.ticket'].search(domain)
    print(f"    Tickets trouvés avec le domaine original: {len(tickets)}")
    for t in tickets:
        print(f"        - {t.name} (ID: {t.id}, Ref: {t.reference})")
    
    # Autre test avec client_id uniquement
    tickets_client = env['it.ticket'].search([('client_id', '=', user.partner_id.commercial_partner_id.id)])
    print(f"    Tickets avec client_id uniquement: {len(tickets_client)}")

    # Test avec l'ID du partner directement
    tickets_direct = env['it.ticket'].search([('client_id', '=', user.partner_id.id)])
    print(f"    Tickets avec partner_id direct: {len(tickets_direct)}")

# 5. Vérifier les templates de vue du portail
portal_templates = env['ir.ui.view'].search([('name', 'ilike', 'portal_my_tickets')])
print(f"\nTemplates de vue pour les tickets du portail: {len(portal_templates)}")
for template in portal_templates:
    print(f"    Template: {template.name} (ID: {template.id}, Active: {template.active})")
    # Activer tous les templates si nécessaire
    if not template.active:
        template.active = True
        print(f"    --> Template activé: {template.name}")

# 6. Vérifier l'accessibilité du modèle it.ticket
has_access = env['ir.model.access'].search([
    ('model_id.model', '=', 'it.ticket'),
    ('group_id.users', 'in', portal_users.ids)
])
print(f"\nRègles d'accès pour it.ticket pour les utilisateurs du portail: {len(has_access)}")
for access in has_access:
    print(f"    - {access.name}: Read: {access.perm_read}, Write: {access.perm_write}, Create: {access.perm_create}")

print("\n===== FIN DIAGNOSTIC =====") 