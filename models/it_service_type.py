# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ITServiceType(models.Model):
    _name = 'it.service.type'
    _description = 'IT Service Type'
    _order = 'sequence, name'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Sequence', default=10)
    description = fields.Text('Description')
    
    # Prix et facturation
    has_fixed_price = fields.Boolean('Fixed Price', default=False)
    fixed_price = fields.Float('Fixed Price Amount')
    has_user_price = fields.Boolean('Price per User', default=False)
    price_per_user = fields.Float('Price per User')
    has_equipment_price = fields.Boolean('Price per Equipment', default=False)
    price_per_equipment = fields.Float('Price per Equipment')
    base_price = fields.Float('Base Price')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    
    # Configuration
    requires_contract = fields.Boolean('Requires Contract', default=True)
    requires_approval = fields.Boolean('Requires Approval', default=True)
    requires_payment = fields.Boolean('Requires Payment', default=True)
    
    # Relations
    contract_type_ids = fields.Many2many('it.contract.type', string='Contract Types')
    
    # Documents requis
    required_documents = fields.Many2many('ir.attachment', string='Required Documents')
    document_checklist = fields.Text('Document Checklist')
    
    # SLA
    sla_id = fields.Many2one('it.sla', string='Service Level Agreement')
    response_time = fields.Float('Response Time (hours)')
    resolution_time = fields.Float('Resolution Time (hours)')
    
    # Facturation
    billing_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Rate'),
        ('monthly', 'Monthly Subscription'),
        ('yearly', 'Yearly Subscription')
    ], string='Billing Type', required=True, default='fixed')
    
    min_contract_duration = fields.Integer('Minimum Contract Duration (months)', default=1)
    notice_period = fields.Integer('Notice Period (days)', default=30)
    
    # Relations
    request_ids = fields.Many2many('it.service.request', 'it_service_request_type_rel', 'service_type_id', 'request_id', string='Service Requests')
    
    # Statistiques
    request_count = fields.Integer('Request Count', compute='_compute_request_count')
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Service type code must be unique!')
    ]
    
    @api.depends('request_ids')
    def _compute_request_count(self):
        for service_type in self:
            service_type.request_count = len(service_type.request_ids)
    
    def name_get(self):
        result = []
        for service_type in self:
            name = f'[{service_type.code}] {service_type.name}'
            result.append((service_type.id, name))
        return result
        
    def action_view_requests(self):
        self.ensure_one()
        action = {
            'name': _('Service Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'it.service.request',
            'view_mode': 'list,form',
            'domain': [('services_needed', 'in', self.id)],
            'context': {'default_services_needed': [(4, self.id)]}
        }
        return action 