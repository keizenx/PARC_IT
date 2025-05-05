# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    it_equipment_id = fields.Many2one('it.equipment', string='Équipement IT', index=True,
                                     help="Équipement IT associé à ce mouvement de stock")
    
    # Surcharger la méthode _get_display_name pour inclure la référence de l'équipement
    def _get_display_name(self):
        display_name = super(StockMove, self)._get_display_name()
        if self.it_equipment_id:
            display_name = f"{display_name} - {self.it_equipment_id.reference}"
        return display_name 