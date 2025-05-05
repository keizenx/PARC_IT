from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    it_equipment_dest_id = fields.Many2one(
        'it.equipment', 
        string='Équipement associé',
        help="Équipement informatique associé à ce bon de livraison"
    )
    
    it_contract_id = fields.Many2one(
        'it.contract',
        string='Contrat associé',
        help="Contrat de maintenance associé à cette livraison"
    )


class StockMove(models.Model):
    _inherit = 'stock.move'

    it_equipment_id = fields.Many2one(
        'it.equipment', 
        string='Équipement associé',
        help="Équipement informatique associé à ce mouvement"
    ) 