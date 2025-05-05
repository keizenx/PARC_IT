from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReturnEquipmentWizard(models.TransientModel):
    _name = 'it.return.equipment.wizard'
    _description = 'Assistant de retour d\'équipement'

    equipment_id = fields.Many2one('it.equipment', string='Équipement', required=True,
                                  domain=[('state', '=', 'assigned')])
    return_date = fields.Date(string='Date de retour', default=fields.Date.today, required=True)
    reason = fields.Selection([
        ('end_of_use', 'Fin d\'utilisation'),
        ('malfunction', 'Dysfonctionnement'),
        ('upgrade', 'Mise à niveau'),
        ('employee_departure', 'Départ de l\'employé'),
        ('other', 'Autre')
    ], string='Raison du retour', required=True)
    condition = fields.Selection([
        ('good', 'Bon état'),
        ('fair', 'État moyen'),
        ('poor', 'Mauvais état'),
        ('damaged', 'Endommagé'),
        ('not_working', 'Ne fonctionne pas')
    ], string='État de l\'équipement', required=True)
    notes = fields.Text(string='Notes')
    
    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        if self.equipment_id and self.equipment_id.state != 'assigned':
            return {'warning': {
                'title': _('Équipement non assigné'),
                'message': _('Cet équipement n\'est pas actuellement assigné.')
            }}
    
    def action_return_equipment(self):
        self.ensure_one()
        if self.equipment_id.state != 'assigned':
            raise UserError(_('Cet équipement n\'est pas actuellement assigné.'))
        
        # Mise à jour de l'équipement
        new_state = 'available'
        if self.condition in ['damaged', 'not_working']:
            new_state = 'maintenance'
            
        employee_id = self.equipment_id.employee_id.id
        self.equipment_id.write({
            'employee_id': False,
            'state': new_state,
            'condition': self.condition,
            'notes': self.notes,
        })
        
        # Création d'une entrée dans l'historique
        self.env['it.equipment.history'].create({
            'equipment_id': self.equipment_id.id,
            'employee_id': employee_id,
            'date': self.return_date,
            'action': 'return',
            'notes': f"Raison: {dict(self._fields['reason'].selection).get(self.reason)}\n{self.notes or ''}",
        })
        
        # Si l'équipement nécessite une maintenance, créer un ticket d'incident
        if new_state == 'maintenance':
            self.env['it.incident'].create({
                'name': f"Maintenance requise pour {self.equipment_id.name}",
                'equipment_id': self.equipment_id.id,
                'description': f"L'équipement a été retourné en état {dict(self._fields['condition'].selection).get(self.condition)}.\n"
                              f"Raison du retour: {dict(self._fields['reason'].selection).get(self.reason)}\n\n"
                              f"Notes: {self.notes or ''}",
                'priority': 'medium',
                'type': 'incident',
            })
        
        return {'type': 'ir.actions.act_window_close'} 