# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Configuration pour le parc informatique
    it_manager_id = fields.Many2one('res.users', string='Responsable du service IT')
    it_email = fields.Char('Email du service IT')
    it_phone = fields.Char('Téléphone du service IT')
    
    # Numérotation et référencement
    next_equipment_number = fields.Integer('Prochain numéro d\'équipement', default=1)
    next_sn_number = fields.Integer('Prochain numéro de série', default=1)
    
    # Produits et services
    default_service_product_id = fields.Many2one('product.product', string='Produit service par défaut',
        domain=[('type', '=', 'service')])
        
    # Configuration facturation des contrats
    use_contract_billing = fields.Boolean('Facturation automatique des contrats', default=False)
    contract_billing_product_id = fields.Many2one('product.product', string='Produit pour contrats',
        domain=[('type', '=', 'service')])
    contract_journal_id = fields.Many2one('account.journal', string='Journal de facturation contrats',
        domain=[('type', '=', 'sale')])
        
    # Configuration facturation des interventions
    use_intervention_billing = fields.Boolean('Facturation des interventions', default=False)
    intervention_billing_product_id = fields.Many2one('product.product', string='Produit pour interventions',
        domain=[('type', '=', 'service')])
    default_hourly_rate = fields.Float('Taux horaire par défaut', default=75.0)
    
    # Configuration pour l'intégration Helpdesk
    use_helpdesk_for_incidents = fields.Boolean('Utiliser Helpdesk pour les incidents', 
        default=True, 
        help="Lorsque cette option est activée, chaque nouvel incident crée automatiquement un ticket dans le module Helpdesk")
    default_helpdesk_team_id = fields.Many2one('helpdesk.team', string='Équipe Helpdesk par défaut',
        help="Équipe Helpdesk à utiliser par défaut pour les incidents sans type spécifique")
    
    # Configuration de notifications
    notify_on_incident_creation = fields.Boolean('Notifier à la création d\'incident', default=True)
    notify_on_equipment_expiration = fields.Boolean('Notifier à l\'expiration d\'équipement', default=True)
    notify_on_license_expiration = fields.Boolean('Notifier à l\'expiration de licence', default=True)
    notify_on_maintenance_due = fields.Boolean('Notifier pour la maintenance planifiée', default=True)
    notify_days_before_expiration = fields.Integer('Jours avant notification', default=30,
        help="Nombre de jours avant expiration pour envoyer une notification")
    
    # Configuration générale
    incident_auto_assign = fields.Boolean('Assignation automatique', 
        help="Assigner automatiquement les incidents aux techniciens en fonction de leur charge de travail")
    sla_reminder_delay = fields.Integer('Rappel SLA (heures)', default=1,
        help="Nombre d'heures avant échéance SLA pour envoyer un rappel")
    
    def action_setup_helpdesk_integration(self):
        """Assistant pour configurer l'intégration Helpdesk"""
        self.ensure_one()
        
        # Vérifier si le module helpdesk est installé (compat Odoo 18)
        helpdesk_installed = bool(self.env['ir.module.module'].sudo().search_count([
            ('name', '=', 'helpdesk'),
            ('state', '=', 'installed'),
        ]))
        if not helpdesk_installed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Module Helpdesk non installé'),
                    'message': _('Veuillez installer le module Helpdesk pour activer cette fonctionnalité.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Chercher ou créer l'équipe Helpdesk pour le service IT
        it_team = self.env['helpdesk.team'].search([
            ('name', 'ilike', 'IT'),
            ('company_id', '=', self.id)
        ], limit=1)
        
        if not it_team:
            it_team = self.env['helpdesk.team'].create({
                'name': 'Support IT',
                'company_id': self.id,
                'use_sla': True,
                'assign_method': 'balanced',
            })
        
        # Mettre à jour la configuration
        self.write({
            'use_helpdesk_for_incidents': True,
            'default_helpdesk_team_id': it_team.id,
        })
        
        # Créer ou mettre à jour les étapes de ticket Helpdesk
        stage_vals = [
            {'name': 'Nouveau', 'sequence': 10},
            {'name': 'En attente d\'attribution', 'sequence': 20},
            {'name': 'En cours', 'sequence': 30},
            {'name': 'En attente', 'sequence': 40},
            {'name': 'Résolu', 'sequence': 50},
            {'name': 'Fermé', 'sequence': 60},
        ]
        
        for vals in stage_vals:
            stage = self.env['helpdesk.stage'].search([
                ('name', '=', vals['name']),
                ('team_ids', 'in', it_team.id)
            ], limit=1)
            
            if not stage:
                vals.update({
                    'team_ids': [(4, it_team.id)],
                })
                self.env['helpdesk.stage'].create(vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Configuration terminée'),
                'message': _('L\'intégration Helpdesk a été configurée avec succès.'),
                'sticky': False,
                'type': 'success',
            }
        }
        
    def action_configure_helpdesk(self):
        """Action pour configurer l'intégration Helpdesk"""
        return self.action_setup_helpdesk_integration() 
