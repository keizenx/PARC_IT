from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    employee_id = fields.Many2one(
        'it.employee',
        string='Employé IT',
        help="Employé IT associé à cet utilisateur"
    )
    
    it_technician = fields.Boolean(
        string='Technicien IT',
        compute='_compute_it_technician',
        search='_search_it_technician',
        store=True,  # Stocker le champ pour éviter des problèmes de dépendance
        help="Indique si l'utilisateur est associé à un employé qui est un technicien IT",
    )
    
    notes = fields.Text(
        string='Notes',
        related='employee_id.notes',
        help="Notes et commentaires sur ce technicien",
    )
    
    @api.depends('employee_id')
    def _compute_it_technician(self):
        """Calcule si l'utilisateur est un technicien IT en fonction de son employé IT associé"""
        for user in self:
            if user.employee_id:
                # Recherche directe plutôt que d'utiliser la dépendance
                user.it_technician = user.employee_id.it_technician if user.employee_id else False
            else:
                user.it_technician = False
    
    def _search_it_technician(self, operator, value):
        if operator not in ('=', '!='):
            return []
        
        if (operator == '=' and value) or (operator == '!=' and not value):
            # Cherche les utilisateurs dont l'employé est technicien IT
            employees = self.env['it.employee'].search([('it_technician', '=', True)])
            return [('employee_id', 'in', employees.ids)]
        else:
            # Cherche les utilisateurs dont l'employé n'est pas technicien IT
            employees = self.env['it.employee'].search([('it_technician', '=', False)])
            users_without_employee = self.search([('employee_id', '=', False)])
            return ['|', ('employee_id', 'in', employees.ids), ('id', 'in', users_without_employee.ids)] 