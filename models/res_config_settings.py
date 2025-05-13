# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Configuration générale
    it_email_notifications = fields.Boolean(string="Notifications Email", default=True)
    it_auto_assignment = fields.Boolean(string="Auto-assignation des tickets", default=False)
    
    # SLA et Support
    it_default_sla_id = fields.Many2one('it.sla', string="SLA par défaut")
    it_support_hours_from = fields.Float(string="Heures de support depuis", default=8.0)
    it_support_hours_to = fields.Float(string="Heures de support jusqu'à", default=18.0)
    
    # Portail Client
    it_enable_customer_portal = fields.Boolean(string="Accès portail client", default=True)
    it_enable_customer_signup = fields.Boolean(string="Inscription client", default=True)
    it_require_admin_validation = fields.Boolean(string="Validation admin", default=True)

    # Méthode pour récupérer les paramètres depuis les paramètres système
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        
        res.update(
            it_email_notifications=param.get_param('it_park.it_email_notifications', default=True),
            it_auto_assignment=param.get_param('it_park.it_auto_assignment', default=False),
            it_support_hours_from=float(param.get_param('it_park.it_support_hours_from', default=8.0)),
            it_support_hours_to=float(param.get_param('it_park.it_support_hours_to', default=18.0)),
            it_enable_customer_portal=param.get_param('it_park.it_enable_customer_portal', default=True),
            it_enable_customer_signup=param.get_param('it_park.it_enable_customer_signup', default=True),
            it_require_admin_validation=param.get_param('it_park.it_require_admin_validation', default=True),
        )
        
        # Récupération du SLA par défaut
        default_sla_id = param.get_param('it_park.it_default_sla_id')
        if default_sla_id:
            res['it_default_sla_id'] = int(default_sla_id)
        
        return res

    # Méthode pour stocker les paramètres dans les paramètres système
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        
        param.set_param('it_park.it_email_notifications', self.it_email_notifications)
        param.set_param('it_park.it_auto_assignment', self.it_auto_assignment)
        param.set_param('it_park.it_support_hours_from', self.it_support_hours_from)
        param.set_param('it_park.it_support_hours_to', self.it_support_hours_to)
        param.set_param('it_park.it_enable_customer_portal', self.it_enable_customer_portal)
        param.set_param('it_park.it_enable_customer_signup', self.it_enable_customer_signup)
        param.set_param('it_park.it_require_admin_validation', self.it_require_admin_validation)
        
        if self.it_default_sla_id:
            param.set_param('it_park.it_default_sla_id', self.it_default_sla_id.id)
        else:
            param.set_param('it_park.it_default_sla_id', False) 