from odoo import models, fields, api, _
from datetime import date


class ITDocument(models.Model):
    _name = 'it.document'
    _description = 'Document IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'
    
    name = fields.Char(string='Nom', required=True, tracking=True)
    date = fields.Date(string='Date', default=fields.Date.today, tracking=True)
    
    file = fields.Binary(string='Fichier', attachment=True, required=True)
    file_name = fields.Char(string='Nom du fichier')
    
    description = fields.Text(string='Description')
    
    contract_id = fields.Many2one('it.contract', string='Contrat associé', tracking=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement associé', tracking=True)
    license_id = fields.Many2one('it.license', string='Licence associée', tracking=True)
    
    type = fields.Selection([
        ('contract', 'Contrat'),
        ('invoice', 'Facture'),
        ('manual', 'Manuel'),
        ('certificate', 'Certificat'),
        ('other', 'Autre'),
    ], string='Type de document', default='other', required=True, tracking=True)
    
    @api.onchange('contract_id', 'equipment_id', 'license_id')
    def _onchange_related_entity(self):
        """Assure qu'un seul des trois champs soit rempli à la fois"""
        if self.contract_id:
            self.equipment_id = False
            self.license_id = False
        elif self.equipment_id:
            self.contract_id = False
            self.license_id = False
        elif self.license_id:
            self.contract_id = False
            self.equipment_id = False 