from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)

def fix_portal_tickets_domain(cr, registry):
    """Script de diagnostic pour afficher les informations sur les tickets et l'accès"""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Récupérer tous les tickets
        all_tickets = env['it.ticket'].search([])
        _logger.info(f"=== DIAGNOSTIC TICKETS ===")
        _logger.info(f"Nombre total de tickets: {len(all_tickets)}")
        
        # Liste des tickets
        for ticket in all_tickets:
            _logger.info(f"Ticket ID: {ticket.id}, Référence: {ticket.reference}, Nom: {ticket.name}")
            _logger.info(f"    Client: {ticket.client_id.name} (ID: {ticket.client_id.id})")
            _logger.info(f"    Partner: {ticket.partner_id.name} (ID: {ticket.partner_id.id})")
            _logger.info(f"    State: {ticket.state}")
        
        # Liste des utilisateurs du portail
        portal_users = env['res.users'].search([('share', '=', True)])
        _logger.info(f"\nUtilisateurs du portail: {len(portal_users)}")
        for user in portal_users:
            _logger.info(f"User: {user.name} (ID: {user.id}, Login: {user.login})")
            _logger.info(f"    Partner: {user.partner_id.name} (ID: {user.partner_id.id})")
            _logger.info(f"    Commercial Partner: {user.partner_id.commercial_partner_id.name} (ID: {user.partner_id.commercial_partner_id.id})")
            
            # Test du domaine pour cet utilisateur
            domain = ['|', 
                ('client_id', '=', user.partner_id.commercial_partner_id.id),
                ('partner_id', '=', user.partner_id.commercial_partner_id.id)
            ]
            tickets = env['it.ticket'].sudo().search(domain)
            _logger.info(f"    Nombre de tickets correspondant au domaine pour cet utilisateur: {len(tickets)}")
            if tickets:
                for t in tickets:
                    _logger.info(f"        Ticket trouvé: {t.name} (ID: {t.id}, Ref: {t.reference})")
        
        _logger.info("\n=== FIN DIAGNOSTIC ===")
        
        # Correction supplémentaire du compteur de tickets dans le portail
        env['ir.model.data'].search([
            ('name', '=', 'portal_my_tickets'),
            ('model', '=', 'ir.ui.view')
        ]).write({'active': True})
