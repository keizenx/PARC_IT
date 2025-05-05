# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ReporterType(models.Model):
    _name = 'it.reporter.type'
    _description = 'Type de rapporteur d\'incident'
    
    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    active = fields.Boolean(default=True)

class Reporter(models.Model):
    _name = 'it.reporter'
    _description = 'Rapporteur d\'incident'
    _rec_name = 'display_name'
    
    name = fields.Char(string='Nom', required=True)
    type_id = fields.Many2one('it.reporter.type', string='Type de rapporteur', required=True)
    partner_id = fields.Many2one('res.partner', string='Contact associé')
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.depends('name', 'type_id', 'partner_id')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id:
                record.display_name = f"{record.name} ({record.type_id.name} - {record.partner_id.name})"
            else:
                record.display_name = f"{record.name} ({record.type_id.name})"
    
    _sql_constraints = [
        ('name_type_unique', 'unique(name, type_id)', 'Ce rapporteur existe déjà pour ce type!')
    ] 