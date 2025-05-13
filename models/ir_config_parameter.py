# -*- coding: utf-8 -*-
from odoo import models, api

class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'
    
    @api.model
    def init_disable_duplicate_menus(self):
        """
        Méthode appelée par le fichier data/init_sql.xml pour désactiver les menus dupliqués
        """
        sql_query = self.get_param('disable_duplicate_menus_sql')
        if sql_query:
            self.env.cr.execute(sql_query)
            
        # Vider le cache des menus
        self.env['ir.ui.menu'].clear_caches()
        return True 