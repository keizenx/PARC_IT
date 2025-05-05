# -*- coding: utf-8 -*-

# Modèles
from . import models

# Assistants
from . import wizards

# Contrôleurs
from . import controllers

# Scripts
from . import fix_menu_action

# Correction pour les avertissements de dépréciation Werkzeug
try:
    from .fix_menu_action import fix_menu_actions
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Échec de l'importation du correctif d'actions: {e}")

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