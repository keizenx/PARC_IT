import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def fix_menu_actions(cr, registry):
    """
    Fonction post-init pour créer les actions manquantes référencées dans les menus.
    Cette fonction est appelée après l'installation/mise à jour du module.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Dictionnaire des actions à créer si elles n'existent pas déjà
    actions_to_create = {
        'action_it_software': {
            'name': 'Logiciels',
            'res_model': 'it.software',
            'view_mode': 'kanban,list,form',
        },
        'action_it_license': {
            'name': 'Licences',
            'res_model': 'it.license',
            'view_mode': 'list,form',
        },
        'action_it_contract': {
            'name': 'Contrats',
            'res_model': 'it.contract',
            'view_mode': 'list,form',
        },
        'action_it_tickets_support': {
            'name': 'Tickets IT',
            'res_model': 'it.ticket',
            'view_mode': 'list,form',
        },
        'action_it_incidents': {
            'name': 'Incidents',
            'res_model': 'it.incident',
            'view_mode': 'list,form',
        },
        'action_it_interventions': {
            'name': 'Interventions',
            'res_model': 'it.intervention',
            'view_mode': 'list,form',
        },
        'action_it_dashboard': {
            'name': 'Tableaux de bord',
            'res_model': 'it.dashboard',
            'view_mode': 'kanban,form',
        },
        'action_it_clients': {
            'name': 'Clients IT',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('is_it_client', '=', True)],
            'context': {'default_is_it_client': True},
        },
        'action_it_sites': {
            'name': 'Sites clients',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('type', '=', 'delivery'), ('parent_id.is_it_client', '=', True)],
            'context': {'default_type': 'delivery'},
        },
        'action_it_suppliers': {
            'name': 'Fournisseurs IT',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('is_it_supplier', '=', True)],
            'context': {'default_is_it_supplier': True},
        },
        'action_it_incident_type': {
            'name': 'Types d\'incidents',
            'res_model': 'it.incident.type',
            'view_mode': 'list,form',
        },
        'action_it_incident_priority': {
            'name': 'Priorités d\'incidents',
            'res_model': 'it.incident.priority',
            'view_mode': 'list,form',
        },
        'action_it_contract_type': {
            'name': 'Types de contrats',
            'res_model': 'it.contract.type',
            'view_mode': 'list,form',
        },
        'action_it_software_category': {
            'name': 'Catégories de logiciels',
            'res_model': 'it.software.category',
            'view_mode': 'list,form',
        },
    }
    
    IrModelData = env['ir.model.data']
    ActWindow = env['ir.actions.act_window']
    
    for action_id, action_vals in actions_to_create.items():
        # Vérifier si l'action existe déjà
        external_id = f'it__park.{action_id}'
        try:
            IrModelData._xmlid_lookup(external_id)
            _logger.info(f"L'action {external_id} existe déjà")
        except ValueError:
            # Créer l'action si elle n'existe pas
            action = ActWindow.create(action_vals)
            
            # Créer l'enregistrement ir.model.data pour lier l'action à son external_id
            IrModelData.create({
                'name': action_id,
                'module': 'it__park',
                'model': 'ir.actions.act_window',
                'res_id': action.id,
                'noupdate': True,
            })
            
            _logger.info(f"Action {external_id} créée avec succès")
    
    _logger.info("Fix des actions de menu terminé avec succès")
    return True 