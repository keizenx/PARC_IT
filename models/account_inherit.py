from odoo import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    it_intervention_id = fields.Many2one(
        'it.intervention', 
        string='Intervention',
        help="Intervention liée à cette ligne analytique"
    ) 