# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ITIncidentPriority(models.Model):
    _name = 'it.incident.priority'
    _description = 'Priorité d\'incident'
    _order = 'sequence, name'

    name = fields.Char('Nom', required=True)
    sequence = fields.Integer('Séquence', default=10)
    active = fields.Boolean('Actif', default=True)
    description = fields.Text('Description')
    color = fields.Integer('Couleur', default=0)
    high_priority = fields.Boolean('Haute priorité', default=False,
                                 help="Indique si cette priorité doit être considérée comme haute dans les filtres et vues")
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Le nom de la priorité doit être unique !')
    ] 