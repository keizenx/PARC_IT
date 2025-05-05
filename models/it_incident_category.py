# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ITIncidentCategory(models.Model):
    _name = 'it.incident.category'
    _description = 'Catégorie d\'incident'
    _parent_store = True
    _order = 'sequence, name'

    name = fields.Char('Nom', required=True)
    sequence = fields.Integer('Séquence', default=10)
    active = fields.Boolean('Actif', default=True)
    description = fields.Text('Description')
    color = fields.Integer('Couleur', default=0)
    
    # Hiérarchie des catégories
    parent_id = fields.Many2one('it.incident.category', string='Catégorie parente', ondelete='restrict')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('it.incident.category', 'parent_id', string='Sous-catégories')
    
    # Configuration par défaut
    default_priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Urgente')
    ], string='Priorité par défaut', default='1')
    
    # Statistiques
    incident_count = fields.Integer(compute='_compute_incident_count', string='Nombre d\'incidents')
    
    @api.depends()
    def _compute_incident_count(self):
        for record in self:
            record.incident_count = self.env['it.incident'].search_count([
                ('category_id', '=', record.id)
            ])
    
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Erreur ! Vous ne pouvez pas créer de catégories récursives.'))
            
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            current = record.parent_id
            while current:
                name = f"{current.name} / {name}"
                current = current.parent_id
            result.append((record.id, name))
        return result 