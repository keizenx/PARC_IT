#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def fix_tickets_portal(env):
    """Corrige les problèmes de visibilité des tickets dans le portail client"""
    _logger.info("=== DÉBUT DE LA RÉPARATION DES TICKETS POUR LE PORTAIL ===")
    
    # 1. Récupérer tous les tickets existants
    tickets = env['it.ticket'].sudo().search([])
    _logger.info(f"Nombre total de tickets trouvés: {len(tickets)}")
    
    corrected_tickets = 0
    missing_partner = 0
    missing_client = 0
    
    # 2. Pour chaque ticket, assurer la cohérence entre client_id et partner_id
    for ticket in tickets:
        _logger.info(f"Traitement du ticket #{ticket.id} ({ticket.reference}) - État actuel:")
        _logger.info(f"  - client_id: {ticket.client_id.id} ({ticket.client_id.name if ticket.client_id else 'Non défini'})")
        _logger.info(f"  - partner_id: {ticket.partner_id.id if ticket.partner_id else 'Non défini'} ({ticket.partner_id.name if ticket.partner_id else 'Non défini'})")
        
        modified = False
        
        # A. Si client_id est défini mais pas partner_id
        if ticket.client_id and not ticket.partner_id:
            missing_partner += 1
            ticket.partner_id = ticket.client_id.id
            _logger.info(f"  > Correction: partner_id défini à {ticket.client_id.id} ({ticket.client_id.name})")
            modified = True
            
        # B. Si partner_id est défini mais pas client_id
        elif ticket.partner_id and not ticket.client_id:
            missing_client += 1
            # Vérifier si partner_id est une entreprise ou a un parent
            partner = ticket.partner_id
            if partner.is_company:
                ticket.client_id = partner.id
                _logger.info(f"  > Correction: client_id défini à {partner.id} ({partner.name}) (entreprise)")
            elif partner.parent_id:
                ticket.client_id = partner.parent_id.id
                _logger.info(f"  > Correction: client_id défini à {partner.parent_id.id} ({partner.parent_id.name}) (parent)")
            else:
                _logger.warning(f"  > PROBLÈME: Impossible de trouver un client approprié pour le ticket #{ticket.id}")
                continue
            modified = True
            
        if modified:
            corrected_tickets += 1
            _logger.info(f"  > Ticket corrigé avec succès")
        else:
            _logger.info(f"  > Aucune correction nécessaire")
    
    # 3. Force le rafraîchissement du cache
    env.cr.commit()
    
    _logger.info("=== RÉSUMÉ DE LA CORRECTION ===")
    _logger.info(f"Total de tickets traités: {len(tickets)}")
    _logger.info(f"Tickets corrigés: {corrected_tickets}")
    _logger.info(f"Tickets sans partner_id corrigés: {missing_partner}")
    _logger.info(f"Tickets sans client_id corrigés: {missing_client}")
    
    return {
        'total': len(tickets),
        'corrected': corrected_tickets,
        'missing_partner': missing_partner,
        'missing_client': missing_client
    }

def main(db_name):
    from odoo import api, registry
    with registry(db_name).cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        return fix_tickets_portal(env)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_tickets_portal_final.py [database_name]")
        sys.exit(1)
        
    db_name = sys.argv[1]
    result = main(db_name)
    
    print(f"\nCorrection terminée!")
    print(f"Total de tickets traités: {result['total']}")
    print(f"Tickets corrigés: {result['corrected']}")
    print(f"Détails des corrections:")
    print(f"- Partner manquant: {result['missing_partner']}")
    print(f"- Client manquant: {result['missing_client']}")
    print("\nRedémarrez le serveur Odoo pour appliquer toutes les modifications.") 