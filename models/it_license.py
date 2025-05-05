from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)


class ITLicenseType(models.Model):
    _name = 'it.license.type'
    _description = 'Type de licence'
    _order = 'name'
    
    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    license_count = fields.Integer(string='Nombre de licences', compute='_compute_license_count')
    
    @api.depends('name')
    def _compute_license_count(self):
        for record in self:
            record.license_count = self.env['it.license'].search_count([
                ('license_type_id', '=', record.id)
            ])
            
    def action_view_licenses(self):
        self.ensure_one()
        return {
            'name': _('Licences'),
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'res_model': 'it.license',
            'domain': [('license_type_id', '=', self.id)],
            'context': {'default_license_type_id': self.id},
        }


class ITLicense(models.Model):
    _name = 'it.license'
    _description = 'Licence logicielle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'acquisition_date desc'

    reference = fields.Char(string='Référence', required=True, tracking=True)
    software_id = fields.Many2one('it.software', string='Logiciel', required=True, tracking=True)
    client_id = fields.Many2one('res.partner', string='Client', tracking=True, 
                               domain=[('is_it_client', '=', True), ('is_it_site', '=', False)],
                               help="Sélectionnez uniquement un client IT")
    license_type_id = fields.Many2one('it.license.type', string='Type de licence', tracking=True)
    type = fields.Selection([
        ('perpetual', 'Perpétuelle'),
        ('subscription', 'Abonnement'),
        ('saas', 'SaaS'),
        ('open_source', 'Open Source'),
        ('free', 'Gratuite'),
    ], string='Type de licence', default='subscription', required=True, tracking=True)
    
    key = fields.Char(string='Clé de licence', tracking=True)
    seats = fields.Integer(string='Nombre de postes', default=1, tracking=True)
    
    start_date = fields.Date(string='Date de début', default=fields.Date.today, tracking=True)
    end_date = fields.Date(string='Date de fin', tracking=True)
    acquisition_date = fields.Date(string='Date d\'acquisition', default=fields.Date.today, tracking=True)
    expiration_date = fields.Date(string='Date d\'expiration', related='end_date', store=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Active'),
        ('expiring_soon', 'Expiration proche'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée'),
    ], string='Statut', default='draft', tracking=True, compute='_compute_state', store=True)
    
    contract_id = fields.Many2one('it.contract', string='Contrat associé', tracking=True)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur',
                                 domain="[('is_it_supplier', '=', True)]", 
                                 tracking=True,
                                 context={'create_action': 'it__park.action_it_suppliers'},
                                 help="Sélectionnez uniquement un fournisseur IT")
    
    equipment_ids = fields.Many2many('it.equipment', string='Équipements associés')
    equipment_count = fields.Integer(string='Nombre d\'équipements', compute='_compute_equipment_count')
    used_seats = fields.Integer(string='Sièges utilisés', default=0, tracking=True)
    
    installation_ids = fields.One2many('it.installation', 'license_id', string='Installations')
    
    renewal_reminder = fields.Boolean(string='Rappel de renouvellement', default=True)
    renewal_days = fields.Integer(string='Jours avant rappel', default=30)
    
    cost = fields.Monetary(string='Coût', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    
    note = fields.Text(string='Notes')
    notes = fields.Text(string='Notes', related='note', store=True)
    
    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = len(record.equipment_ids)
    
    @api.depends('start_date', 'end_date', 'type')
    def _compute_state(self):
        today = fields.Date.today()
        for record in self:
            if record.type in ['perpetual', 'open_source', 'free']:
                if record.start_date and record.start_date <= today:
                    record.state = 'active'
                else:
                    record.state = 'draft'
            else:
                if not record.start_date:
                    record.state = 'draft'
                elif record.start_date > today:
                    record.state = 'draft'
                elif not record.end_date:
                    record.state = 'active'
                elif record.end_date >= today:
                    # Vérifier si l'expiration est proche (moins de 30 jours)
                    expiration_delta = (record.end_date - today).days
                    if expiration_delta <= record.renewal_days:
                        record.state = 'expiring_soon'
                    else:
                        record.state = 'active'
                else:
                    record.state = 'expired'
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("La date de fin ne peut pas être antérieure à la date de début."))
    
    @api.constrains('seats')
    def _check_seats(self):
        for record in self:
            if record.seats < 1:
                raise ValidationError(_("Le nombre de postes doit être au moins égal à 1."))
                
    def button_activate(self):
        """Active la licence"""
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'active'})
        return True
        
    def button_renew(self):
        """Renouvelle la licence"""
        for record in self:
            if record.state in ['expired', 'expiring_soon']:
                # Prolonger la date de fin d'un an
                new_end_date = fields.Date.today()
                if record.end_date:
                    new_end_date = fields.Date.from_string(record.end_date)
                    # Si la date de fin est déjà passée, on part de la date d'aujourd'hui
                    if new_end_date < fields.Date.from_string(fields.Date.today()):
                        new_end_date = fields.Date.from_string(fields.Date.today())
                    # Ajouter un an
                    new_end_date = new_end_date.replace(year=new_end_date.year + 1)
                else:
                    # Si pas de date de fin, ajouter un an à partir d'aujourd'hui
                    new_end_date = fields.Date.from_string(fields.Date.today())
                    new_end_date = new_end_date.replace(year=new_end_date.year + 1)
                
                record.write({
                    'end_date': new_end_date,
                    'state': 'active'
                })
        return True
        
    def button_expire(self):
        """Expire manuellement la licence"""
        for record in self:
            if record.state in ['active', 'expiring_soon']:
                record.write({'state': 'expired'})
        return True


class ITInstallation(models.Model):
    _name = 'it.installation'
    _description = 'Installation de licences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    license_id = fields.Many2one('it.license', string='Licence', required=True, ondelete='cascade')
    equipment_id = fields.Many2one('it.equipment', string='Équipement', required=True)
    
    install_date = fields.Date(string='Date d\'installation', default=fields.Date.today)
    state = fields.Selection([
        ('installed', 'Installée'),
        ('uninstalled', 'Désinstallée'),
    ], string='État', default='installed', tracking=True)
    
    @api.depends('license_id', 'equipment_id')
    def _compute_name(self):
        for record in self:
            if record.license_id and record.equipment_id:
                record.name = f"{record.license_id.reference} sur {record.equipment_id.name}"
            else:
                record.name = "Nouvelle installation" 