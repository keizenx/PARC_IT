#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def fix_email_validation(env):
    """Force la validation des emails pour tous les partenaires en attente"""
    # Rechercher tous les partenaires en attente
    partners = env['res.partner'].search([
        ('is_it_client_pending', '=', True),
        ('email_validated', '=', False),
    ])
    
    _logger.info(f"Validation forcée des emails pour {len(partners)} partenaires en attente")
    
    # Forcer la validation pour chaque partenaire
    for partner in partners:
        try:
            _logger.info(f"Traitement du partenaire {partner.name} (ID: {partner.id})")
            partner.write({
                'email_validated': True,
                'email_validation_token': False,
                'email_validation_expiration': False,
                'is_it_client': True,
                'is_it_client_pending': False
            })
            _logger.info(f"Email validé avec succès pour {partner.name}")
        except Exception as e:
            _logger.error(f"Erreur lors de la validation de l'email pour {partner.name}: {str(e)}")
    
    _logger.info("Processus de validation terminé")
    return True

def main(env):
    return fix_email_validation(env)

if __name__ == '__main__':
    # Si exécuté directement depuis le shell Odoo
    from odoo.api import Environment
    import odoo
    
    # Créer un environnement en tant que superutilisateur
    with odoo.registry().cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {})
        main(env) 