from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    # Champ pour la relation avec l'équipement informatique
    it_equipment_dest_id = fields.Many2one('it.equipment', string='Équipement de destination')

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    # Champ pour la relation avec l'équipement informatique
    it_equipment_id = fields.Many2one('it.equipment', string='Équipement IT') 