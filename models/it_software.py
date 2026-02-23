from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class ITSoftware(models.Model):
    _name = 'it.software'
    _description = 'Logiciel informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom', required=True, tracking=True)
    version = fields.Char(string='Version', tracking=True)
    editor_id = fields.Many2one('res.partner', string='Éditeur', 
                              domain=[('is_it_editor', '=', True)], 
                              tracking=True,
                              context={'create_action': 'PARC_IT.action_it_editors'},
                              help="Sélectionnez l'éditeur du logiciel")
    
    category = fields.Selection([
        ('os', 'Système d\'exploitation'),
        ('office', 'Bureautique'),
        ('accounting', 'Comptabilité'),
        ('erp', 'ERP'),
        ('crm', 'CRM'),
        ('database', 'Base de données'),
        ('development', 'Développement'),
        ('security', 'Sécurité'),
        ('utility', 'Utilitaire'),
        ('other', 'Autre'),
    ], string='Catégorie', default='other', tracking=True)
    
    category_id = fields.Many2one('it.software.category', string='Catégorie', tracking=True)
    
    license_required = fields.Boolean(string='Licence requise', default=True, tracking=True)
    license_ids = fields.One2many('it.license', 'software_id', string='Licences')
    license_count = fields.Integer(string='Nombre de licences', compute='_compute_license_count')
    
    equipment_ids = fields.Many2many('it.equipment', string='Équipements')
    equipment_count = fields.Integer(string='Nombre d\'équipements', compute='_compute_equipment_count')
    
    purchase_url = fields.Char(string='URL d\'achat')
    documentation_url = fields.Char(string='URL de documentation')
    support_url = fields.Char(string='URL de support')
    
    description = fields.Text(string='Description')
    note = fields.Text(string='Notes internes')
    
    @api.depends('license_ids')
    def _compute_license_count(self):
        for record in self:
            record.license_count = len(record.license_ids)
    
    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = len(record.equipment_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('editor_id'):
                # Marquer automatiquement comme éditeur de logiciels
                partner = self.env['res.partner'].browse(vals['editor_id'])
                if partner and not partner.is_it_editor:
                    partner.is_it_editor = True
        return super(ITSoftware, self).create(vals_list)


class ITSoftwareCategory(models.Model):
    _name = 'it.software.category'
    _description = 'Catégorie de logiciel'
    _order = 'name'
    
    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    
    software_ids = fields.One2many('it.software', 'category_id', string='Logiciels')
    software_count = fields.Integer(string='Nombre de logiciels', compute='_compute_software_count')
    
    @api.depends('software_ids')
    def _compute_software_count(self):
        for record in self:
            record.software_count = len(record.software_ids)
            
    def action_view_softwares(self):
        self.ensure_one()
        return {
            'name': _('Logiciels'),
            'type': 'ir.actions.act_window',
            'res_model': 'it.software',
            'view_mode': 'kanban,tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        } 