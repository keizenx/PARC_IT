#!/usr/bin/env python
# -*- coding: utf-8 -*-

from odoo import api, models, SUPERUSER_ID

def run_diagnostics(env):
    """Exécute le diagnostic des tickets"""
    from datetime import datetime
    import logging
    _logger = logging.getLogger(__name__)

    # Log dans le terminal et dans le fichier de log
    _logger.info("===== DIAGNOSTIC DES TICKETS %s =====", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 1. Vérifier tous les tickets dans la base de données
    all_tickets = env['it.ticket'].search([])
    _logger.info("Nombre total de tickets: %s", len(all_tickets))

    # 2. Afficher les détails de chaque ticket
    for ticket in all_tickets:
        _logger.info("Ticket ID: %s, Référence: %s, Nom: %s", ticket.id, ticket.reference, ticket.name)
        _logger.info("    Client: %s (ID: %s)", ticket.client_id.name, ticket.client_id.id)
        _logger.info("    Partner: %s (ID: %s)", ticket.partner_id.name, ticket.partner_id.id)
        _logger.info("    State: %s", ticket.state)
        _logger.info("    Commercial Partner ID du client: %s", ticket.client_id.commercial_partner_id.id)
        _logger.info("    Commercial Partner ID du partenaire: %s", ticket.partner_id.commercial_partner_id.id)

    # 3. Vérifier les utilisateurs du portail
    portal_users = env['res.users'].search([('share', '=', True)])
    _logger.info("\nUtilisateurs du portail: %s", len(portal_users))

    # 4. Pour chaque utilisateur du portail, vérifier ses tickets
    for user in portal_users:
        _logger.info("\nUser: %s (ID: %s, Login: %s)", user.name, user.id, user.login)
        _logger.info("    Partner ID: %s", user.partner_id.id)
        _logger.info("    Commercial Partner ID: %s", user.partner_id.commercial_partner_id.id)
        
        # Domaine de recherche pour les tickets de cet utilisateur
        domain = ['|', 
            ('client_id', '=', user.partner_id.commercial_partner_id.id),
            ('partner_id', '=', user.partner_id.commercial_partner_id.id)
        ]
        
        # Tickets avec le domaine original
        tickets = env['it.ticket'].search(domain)
        _logger.info("    Tickets trouvés avec le domaine original: %s", len(tickets))
        for t in tickets:
            _logger.info("        - %s (ID: %s, Ref: %s)", t.name, t.id, t.reference)
        
        # Autre test avec client_id uniquement
        tickets_client = env['it.ticket'].search([('client_id', '=', user.partner_id.commercial_partner_id.id)])
        _logger.info("    Tickets avec client_id uniquement: %s", len(tickets_client))

        # Test avec l'ID du partner directement
        tickets_direct = env['it.ticket'].search([('client_id', '=', user.partner_id.id)])
        _logger.info("    Tickets avec partner_id direct: %s", len(tickets_direct))

    # 5. Vérifier les templates de vue du portail
    portal_templates = env['ir.ui.view'].search([('name', 'ilike', 'portal_my_tickets')])
    _logger.info("\nTemplates de vue pour les tickets du portail: %s", len(portal_templates))
    for template in portal_templates:
        _logger.info("    Template: %s (ID: %s, Active: %s)", template.name, template.id, template.active)

    # 6. Vérifier l'accessibilité du modèle it.ticket
    has_access = env['ir.model.access'].search([
        ('model_id.model', '=', 'it.ticket'),
        ('group_id.users', 'in', portal_users.ids)
    ])
    _logger.info("\nRègles d'accès pour it.ticket pour les utilisateurs du portail: %s", len(has_access))
    for access in has_access:
        _logger.info("    - %s: Read: %s, Write: %s, Create: %s", access.name, access.perm_read, access.perm_write, access.perm_create)

    # 7. Appliquer la correction
    fix_tickets_visibility(env)
    
    _logger.info("\n===== FIN DIAGNOSTIC =====")

def fix_tickets_visibility(env):
    """Corrige la visibilité des tickets dans le portail"""
    import logging
    _logger = logging.getLogger(__name__)
    
    _logger.info("\n===== CORRECTION DE LA VISIBILITÉ DES TICKETS =====")
    
    # 1. Vérifier que le template de vue du portail est actif
    portal_template = env['ir.ui.view'].search([('name', '=', 'portal_my_tickets')])
    if portal_template and not portal_template.active:
        portal_template.active = True
        _logger.info("Template 'portal_my_tickets' activé.")

    # 2. Vérifier les règles d'accès aux tickets pour les utilisateurs du portail
    portal_group = env.ref('base.group_portal')
    ticket_model = env['ir.model'].search([('model', '=', 'it.ticket')], limit=1)

    # Chercher la règle d'accès existante
    access_rule = env['ir.model.access'].search([
        ('model_id', '=', ticket_model.id),
        ('group_id', '=', portal_group.id)
    ])

    # Si la règle n'existe pas, la créer avec les droits appropriés
    if not access_rule:
        env['ir.model.access'].create({
            'name': 'it.ticket portal access',
            'model_id': ticket_model.id,
            'group_id': portal_group.id,
            'perm_read': True,
            'perm_write': False,
            'perm_create': True,
            'perm_unlink': False
        })
        _logger.info("Règle d'accès créée pour les tickets dans le portail.")
    else:
        # S'assurer que les droits de lecture sont activés
        if not access_rule.perm_read:
            access_rule.perm_read = True
            _logger.info("Droit de lecture activé pour les tickets dans le portail.")
        if not access_rule.perm_create:
            access_rule.perm_create = True
            _logger.info("Droit de création activé pour les tickets dans le portail.")

    # 3. Vérifier les règles d'enregistrement pour les tickets
    ticket_rule = env['ir.rule'].search([
        ('model_id', '=', ticket_model.id),
        ('groups', 'in', [portal_group.id]),
        ('name', 'ilike', '%portal%')
    ])

    # Si aucune règle n'est trouvée, en créer une
    if not ticket_rule:
        env['ir.rule'].create({
            'name': 'it.ticket: portal users see their own and commercial partner tickets',
            'model_id': ticket_model.id,
            'domain_force': "['|', ('client_id.commercial_partner_id', '=', user.partner_id.commercial_partner_id.id), ('partner_id.commercial_partner_id', '=', user.partner_id.commercial_partner_id.id)]",
            'groups': [(4, portal_group.id)],
            'perm_read': True,
            'perm_write': False,
            'perm_create': True,
            'perm_unlink': False
        })
        _logger.info("Règle d'enregistrement créée pour les tickets dans le portail.")

    # 4. Mettre à jour le compteur de tickets dans le menu
    try:
        ticket_menu = env.ref('it__park.menu_portal_tickets')
        if ticket_menu:
            ticket_menu.sequence = 10  # Remonter dans la liste des menus
            _logger.info("Menu des tickets mis à jour.")
    except Exception as e:
        _logger.error(f"Erreur lors de la mise à jour du menu: {str(e)}")

    # 5. Rafraîchir le cache et vider les caches de vue
    env['ir.ui.view'].clear_caches()
    _logger.info("Cache de vues vidé.")

    _logger.info("Corrections terminées. Redémarrez le serveur Odoo pour appliquer toutes les modifications.")
    
    return True

def main(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        run_diagnostics(env)
        return True 