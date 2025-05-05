# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ITIncidentType(models.Model):
    _name = 'it.incident.type'
    _description = 'Type d\'incident'
    _order = 'sequence, name'

    name = fields.Char('Nom', required=True)
    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Séquence', default=10)
    active = fields.Boolean('Actif', default=True)
    description = fields.Text('Description')
    color = fields.Integer('Couleur', default=0)
    
    # Configuration par défaut
    default_priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Urgente')
    ], string='Priorité par défaut', default='1')
    
    # Équipe Helpdesk par défaut (si le module helpdesk est installé)
    helpdesk_team_id = fields.Many2one('helpdesk.team', string='Équipe Helpdesk par défaut')
    team_ids = fields.Many2many('helpdesk.team', 'helpdesk_team_incident_type_rel', 
                                'type_id', 'team_id', string='Équipes Helpdesk')
    
    # Statistiques
    incident_count = fields.Integer(compute='_compute_incident_count', string='Nombre d\'incidents')
    
    @api.depends()
    def _compute_incident_count(self):
        for record in self:
            record.incident_count = self.env['it.incident'].search_count([
                ('type_id', '=', record.id)
            ])
    
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Le code doit être unique !')
    ] 