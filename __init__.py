# -*- coding: utf-8 -*-

# Modèles
from . import models

# Assistants
from . import wizards

# Contrôleurs
from . import controllers

# Scripts
from . import fix_menu_action
from . import fix_portal_tickets_domain
from . import run_diagnostics

# Correction pour les avertissements de dépréciation Werkzeug
try:
    from .fix_menu_action import fix_menu_actions
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Échec de l'importation du correctif d'actions: {e}")

from .post_init_hook import post_init_hook
from .run_diagnostics import fix_tickets_visibility

from . import utils

def run_fix_tickets():
    """Fonction appelée après le chargement du module pour corriger les tickets dans le portail"""
    import logging
    from odoo import api, SUPERUSER_ID
    import odoo
    
    _logger = logging.getLogger(__name__)
    _logger.info("Exécution de la correction des tickets du portail...")
    
    try:
        # Exécuter directement la correction dans l'environnement actuel
        cr = odoo.registry(odoo.service.db.list_dbs()[0]).cursor()
        try:
            env = api.Environment(cr, SUPERUSER_ID, {})
            from .run_diagnostics import fix_tickets_visibility
            fix_tickets_visibility(env)
            # Valider les modifications
            cr.commit()
            _logger.info("Correction des tickets terminée avec succès")
        finally:
            cr.close()
    except Exception as e:
        _logger.error(f"Erreur lors de la correction des tickets: {str(e)}")

def post_init_hook(env):
    """Post-installation hook pour configurer automatiquement certains éléments"""
    from odoo import SUPERUSER_ID
    
    # Appliquer le correctif pour les actions manquantes
    from .fix_menu_action import fix_menu_actions
    fix_menu_actions(env.cr, env.registry)
    
    # Vérifier si le module helpdesk est installé
    if env.registry._init_modules and 'helpdesk' in env.registry._init_modules:
        # Vérifier si la méthode existe avant de l'appeler
        for company in env['res.company'].search([]):
            if hasattr(company, 'action_setup_helpdesk_integration'):
                company.action_setup_helpdesk_integration()
            else:
                import logging
                logging.getLogger(__name__).info("La méthode action_setup_helpdesk_integration n'est pas disponible dans ce module.") 