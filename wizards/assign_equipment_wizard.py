# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssignEquipmentWizard(models.TransientModel):
    _name = 'it.assign.equipment.wizard'
    _description = 'Assistant d\'assignation d\'équipement'

    equipment_id = fields.Many2one('it.equipment', string='Équipement', required=True)
    employee_id = fields.Many2one('it.employee', string='Employé', required=True)
    partner_id = fields.Many2one('res.partner', string='Client')
    assignment_date = fields.Date(string='Date d\'assignation', default=fields.Date.today, required=True)
    notes = fields.Text(string='Notes')
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.employee_id = False
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.partner_id = False
    
    def action_assign(self):
        self.ensure_one()
        
        if self.equipment_id.state != 'available':
            raise ValidationError(_("Cet équipement n'est pas disponible pour assignation."))
        
        if self.employee_id:
            self.equipment_id.write({
                'state': 'assigned',
                'assigned_employee_id': self.employee_id.id,
                'assigned_partner_id': False,
                'assignment_date': self.assignment_date,
                'notes': self.notes,
            })
        elif self.partner_id:
            self.equipment_id.write({
                'state': 'assigned',
                'assigned_employee_id': False,
                'assigned_partner_id': self.partner_id.id,
                'assignment_date': self.assignment_date,
                'notes': self.notes,
            })
        else:
            raise ValidationError(_("Vous devez spécifier un employé ou un client."))
        
        # Créer une entrée dans l'historique
        self.env['it.equipment.history'].create({
            'equipment_id': self.equipment_id.id,
            'date': self.assignment_date,
            'employee_id': self.employee_id.id if self.employee_id else False,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'action': 'assign',
            'notes': self.notes,
        })
        
        return {'type': 'ir.actions.act_window_close'} 