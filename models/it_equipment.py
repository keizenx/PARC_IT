from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class ITEquipmentType(models.Model):
    _name = 'it.equipment.type'
    _description = 'Type d\'équipement informatique'
    _order = 'name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    equipment_count = fields.Integer(string='Nombre d\'équipements', compute='_compute_equipment_count')
    
    # Intégration stock (commenté car product.product n'existe pas)
    # product_id = fields.Many2one('product.product', string='Produit associé', 
    #                           domain=[('type', 'in', ['product', 'consu'])],
    #                           help="Produit de stock associé à ce type d'équipement")
    track_in_stock = fields.Boolean(string='Suivre en stock', default=True,
                                   help="Cocher pour suivre ce type d'équipement dans le stock")
    
    @api.depends('name')
    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = self.env['it.equipment'].search_count([
                ('type_id', '=', record.id)
            ])


class ITEquipment(models.Model):
    _name = 'it.equipment'
    _description = 'Équipement informatique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    @api.model
    def _valid_field_parameter(self, field, name):
        return name == 'options' or super(ITEquipment, self)._valid_field_parameter(field, name)

    name = fields.Char(string='Nom', required=True, tracking=True)
    reference = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('Nouveau'))
    serial_number = fields.Char(string='Numéro de série', tracking=True)
    type_id = fields.Many2one('it.equipment.type', string='Type d\'équipement', required=True, tracking=True)
    client_id = fields.Many2one('res.partner', string='Client', domain=[('is_company', '=', True), ('is_it_client', '=', True)], required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Propriétaire', related='client_id', store=True, readonly=False, tracking=True,
                            help="Propriétaire de l'équipement (utilisé pour la compatibilité)")
    site_id = fields.Many2one('res.partner', string='Site client', domain="[('is_it_site', '=', True), ('parent_it_client_id', '=', client_id)]", tracking=True,
                            help="Site où est installé l'équipement")
    user_id = fields.Many2one('res.partner', string='Utilisateur', domain=[('is_company', '=', False)], tracking=True)
    
    # Intégration stock (commenté car les modèles n'existent pas)
    # product_id = fields.Many2one('product.product', string='Produit', related='type_id.product_id', store=True, readonly=True)
    # Commenté pour résoudre l'erreur KeyError: 'it_equipment_id'
    # stock_move_ids = fields.One2many('stock.move', 'it_equipment_id', string='Mouvements de stock')
    # stock_location_id = fields.Many2one('stock.location', string='Emplacement de stock',
    #                                  help="Emplacement actuel de l'équipement dans le stock")
    stock_state = fields.Selection([
        ('in_stock', 'En stock'),
        ('allocated', 'Alloué'),
        ('delivered', 'Livré'),
        ('returned', 'Retourné'),
    ], string='État du stock', compute='_compute_stock_state', store=True)
    # warehouse_id = fields.Many2one('stock.warehouse', string='Entrepôt')
    
    purchase_date = fields.Date(string='Date d\'achat', tracking=True)
    warranty_end_date = fields.Date(string='Fin de garantie', tracking=True)
    installation_date = fields.Date(string='Date d\'installation', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_stock', 'En stock'),
        ('installed', 'Installé'),
        ('maintenance', 'En maintenance'),
        ('end_of_life', 'Fin de vie'),
    ], string='État', default='draft', tracking=True)
    
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', tracking=True)
    purchase_price = fields.Float(string='Prix d\'achat', tracking=True)
    current_value = fields.Float(string='Valeur actuelle', compute='_compute_current_value', store=True)
    depreciation_period = fields.Integer(string='Période d\'amortissement (mois)', default=36)
    
    contract_id = fields.Many2one('it.contract', string='Contrat de maintenance', tracking=True)
    
    software_ids = fields.Many2many('it.software', string='Logiciels installés')
    software_count = fields.Integer(string='Nombre de logiciels', compute='_compute_software_count')
    
    incident_ids = fields.One2many('it.incident', 'equipment_id', string='Incidents')
    incident_count = fields.Integer(string='Nombre d\'incidents', compute='_compute_incident_count')
    
    intervention_ids = fields.One2many('it.intervention', 'equipment_id', string='Interventions')
    intervention_count = fields.Integer(string='Nombre d\'interventions', compute='_compute_intervention_count')
    
    note = fields.Text(string='Notes')
    
    # Champs pour intégration avec l'inventaire (commenté car stock.quant n'existe pas)
    # stock_quant_id = fields.Many2one('stock.quant', string='Stock Quant', compute='_compute_stock_quant')
    
    # Champs pour les mouvements de stock (commentés pour résoudre l'erreur "stock.picking does not exist in registry")
    picking_count = fields.Integer(string='Nombre de livraisons', compute='_compute_picking_count', default=0)
    
    # Pour le suivi d'amortissement
    depreciation_start_date = fields.Date(string='Date de début d\'amortissement', 
                                        default=lambda self: fields.Date.today())
    depreciation_end_date = fields.Date(string='Date de fin d\'amortissement', compute='_compute_depreciation_end_date')
    depreciation_value = fields.Float(string='Valeur d\'amortissement', tracking=True)
    depreciation_method = fields.Selection([
        ('linear', 'Linéaire'),
        ('degressive', 'Dégressif'),
    ], string='Méthode d\'amortissement', default='linear')
    
    # Méthodes pour les transitions d'état
    def action_draft(self):
        """Passer l'équipement à l'état Brouillon"""
        self.write({'state': 'draft'})
        return True
    
    def action_in_stock(self):
        """Passer l'équipement à l'état En stock"""
        self.write({'state': 'in_stock'})
        return True
    
    def action_install(self):
        """Passer l'équipement à l'état Installé"""
        # Si pas de date d'installation, définir la date du jour
        for equipment in self:
            vals = {'state': 'installed'}
            if not equipment.installation_date:
                vals['installation_date'] = fields.Date.today()
            equipment.write(vals)
        return True
    
    def action_maintenance(self):
        """Passer l'équipement à l'état En maintenance"""
        self.write({'state': 'maintenance'})
        return True
    
    def action_end_of_life(self):
        """Passer l'équipement à l'état Fin de vie"""
        self.write({'state': 'end_of_life'})
        return True
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('Nouveau')) == _('Nouveau'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('it.equipment') or _('Nouveau')
        
        equipments = super(ITEquipment, self).create(vals_list)
        
        # Commenté car les méthodes font référence à des modèles qui n'existent pas
        # # Créer un lot pour le produit si numéro de série fourni
        # for equipment in equipments:
        #     if equipment.product_id and equipment.serial_number:
        #         self._create_lot_for_product(equipment)
        #     
        # # Créer un mouvement de stock si nécessaire
        # if equipment.type_id.track_in_stock and equipment.type_id.product_id:
        #     equipment._create_initial_stock_move()
            
        return equipments
    
    def write(self, vals):
        result = super(ITEquipment, self).write(vals)
        
        # Commenté car fait référence à product_id qui n'existe pas
        # # Si le produit ou le numéro de série a changé, mettre à jour le lot
        # if 'product_id' in vals or 'serial_number' in vals:
        #     for equipment in self:
        #         if equipment.product_id and equipment.serial_number:
        #             self._create_lot_for_product(equipment)
                    
        return result
    
    @api.depends('purchase_price', 'purchase_date', 'depreciation_period')
    def _compute_current_value(self):
        for equipment in self:
            if not equipment.purchase_price or not equipment.purchase_date:
                equipment.current_value = 0
                continue
                
            # Calcul de l'amortissement linéaire
            months_passed = 0
            if equipment.purchase_date:
                purchase_date = equipment.purchase_date
                today = date.today()
                months_passed = (today.year - purchase_date.year) * 12 + today.month - purchase_date.month
            
            if equipment.depreciation_period > 0 and months_passed < equipment.depreciation_period:
                equipment.current_value = equipment.purchase_price * (1 - months_passed / equipment.depreciation_period)
            else:
                equipment.current_value = 0
    
    @api.depends('software_ids')
    def _compute_software_count(self):
        for record in self:
            record.software_count = len(record.software_ids)
    
    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for record in self:
            record.incident_count = len(record.incident_ids)
    
    @api.depends('intervention_ids')
    def _compute_intervention_count(self):
        for record in self:
            record.intervention_count = len(record.intervention_ids)
    
    @api.constrains('purchase_date', 'warranty_end_date', 'installation_date')
    def _check_dates(self):
        for record in self:
            if record.purchase_date and record.warranty_end_date and record.purchase_date > record.warranty_end_date:
                raise ValidationError(_("La date de fin de garantie ne peut pas être antérieure à la date d'achat."))
            if record.purchase_date and record.installation_date and record.purchase_date > record.installation_date:
                raise ValidationError(_("La date d'installation ne peut pas être antérieure à la date d'achat."))
    
    @api.depends('depreciation_start_date', 'depreciation_period')
    def _compute_depreciation_end_date(self):
        for record in self:
            if record.depreciation_start_date:
                record.depreciation_end_date = record.depreciation_start_date + timedelta(days=30*record.depreciation_period)
            else:
                record.depreciation_end_date = False
    
    @api.depends()
    def _compute_picking_count(self):
        for record in self:
            # Commenté car stock.picking n'existe pas dans le registre
            # record.picking_count = self.env['stock.picking'].search_count([
            #    ('it_equipment_dest_id', '=', record.id)
            # ])
            record.picking_count = 0
    
    def _create_lot_for_product(self, equipment):
        """Créer un lot pour le produit avec le numéro de série"""
        # Commenté car product.product n'existe pas dans le registre
        # if not equipment.product_id.tracking in ['serial', 'lot']:
        #     # Configurer le produit pour qu'il soit suivi par numéro de série
        #     equipment.product_id.tracking = 'serial'
        # 
        # # Vérifier si le lot existe déjà
        # lot = self.env['stock.lot'].search([
        #     ('name', '=', equipment.serial_number),
        #     ('product_id', '=', equipment.product_id.id),
        #     ('company_id', '=', self.env.company.id)
        # ], limit=1)
        # 
        # if not lot:
        #     # Créer un nouveau lot
        #     lot = self.env['stock.lot'].create({
        #         'name': equipment.serial_number,
        #         'product_id': equipment.product_id.id,
        #         'company_id': self.env.company.id,
        #     })
        #     
        # return lot
        return True
    
    def _create_initial_stock_move(self):
        """Créer un mouvement de stock initial pour l'équipement"""
        # Commenté car stock.warehouse n'existe pas dans le registre
        # self.ensure_one()
        # 
        # # Vérifier si un entrepôt existe
        # warehouse = self.warehouse_id or self.env['stock.warehouse'].search([], limit=1)
        # if not warehouse:
        #     return False
        #     
        # # Emplacement source (fournisseur virtuel)
        # location_src = self.env.ref('stock.stock_location_suppliers')
        # # Emplacement destination (stock)
        # location_dest = warehouse.lot_stock_id
        # 
        # # Valeurs du mouvement
        # move_vals = {
        #     'name': f"Entrée en stock: {self.reference}",
        #     'product_id': self.type_id.product_id.id,
        #     'product_uom': self.type_id.product_id.uom_id.id,
        #     'product_uom_qty': 1,
        #     'location_id': location_src.id,
        #     'location_dest_id': location_dest.id,
        #     'it_equipment_id': self.id,
        #     'state': 'draft',
        # }
        # 
        # # Créer le mouvement
        # move = self.env['stock.move'].create(move_vals)
        # 
        # # Mettre à jour l'emplacement de l'équipement
        # self.stock_location_id = location_dest.id
        # 
        # return move
        return True
    
    @api.depends()
    def _compute_stock_state(self):
        """Calcule l'état du stock de l'équipement"""
        for record in self:
            if not record.type_id.track_in_stock:
                record.stock_state = False
                continue
            
            # Valeur par défaut simplifiée car les champs liés au stock sont commentés
            record.stock_state = 'in_stock'
    
    def action_view_incidents(self):
        """Ouvrir la vue des incidents liés à cet équipement"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incidents',
            'res_model': 'it.incident',
            'view_mode': 'tree,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id, 'default_client_id': self.client_id.id},
        }
    
    def action_view_interventions(self):
        """Ouvrir la vue des interventions liées à cet équipement"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interventions',
            'res_model': 'it.intervention',
            'view_mode': 'tree,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id, 'default_client_id': self.client_id.id},
        }
    
    def action_view_stock_moves(self):
        """Ouvrir la vue des mouvements de stock liés à cet équipement"""
        self.ensure_one()
        # Commenté car stock.move n'existe pas dans le registre
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Mouvements de stock',
        #     'res_model': 'stock.move',
        #     'view_mode': 'tree,form',
        #     'domain': [('it_equipment_id', '=', self.id)],
        # }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Équipement',
            'res_model': 'it.equipment',
            'view_mode': 'form',
            'res_id': self.id,
        }
    
    def action_view_pickings(self):
        """Afficher les bons de livraison liés à cet équipement"""
        # Commenté car stock.picking n'existe pas dans le registre
        # pickings = self.env['stock.picking'].search([
        #    ('it_equipment_dest_id', '=', self.id)
        # ])
        
        return {
            'name': 'Livraisons',
            'type': 'ir.actions.act_window',
            'res_model': 'it.equipment',  # Modifié pour éviter l'erreur
            'view_mode': 'list,form',
            'domain': [('id', '=', self.id)],
            'context': {'create': False}
        }
    
    def create_delivery_request(self):
        """Créer une demande de livraison pour cet équipement"""
        # Commenté car stock.picking n'existe pas dans le registre
        # picking_type = self.env['stock.picking.type'].search([
        #    ('code', '=', 'outgoing'),
        #    ('company_id', '=', self.company_id.id)
        # ], limit=1)
        #
        # if not picking_type:
        #    raise UserError(_("Aucun type d'opération trouvé pour les livraisons sortantes"))
        #
        # picking_vals = {
        #    'picking_type_id': picking_type.id,
        #    'partner_id': self.assigned_user_partner_id.id or self.company_id.partner_id.id,
        #    'origin': f'Équipement {self.name}',
        #    'it_equipment_dest_id': self.id,
        #    'location_id': picking_type.default_location_src_id.id,
        #    'location_dest_id': picking_type.default_location_dest_id.id,
        # }
        #
        # picking = self.env['stock.picking'].create(picking_vals)
        
        return {
            'name': 'Nouvelle livraison',
            'type': 'ir.actions.act_window',
            'res_model': 'it.equipment',  # Modifié pour éviter l'erreur
            'view_mode': 'form',
            'res_id': self.id,
            'context': {'create': False}
        }
    
    def action_allocate_to_client(self):
        """Allouer l'équipement à un client"""
        self.ensure_one()
        
        if not self.client_id:
            raise ValidationError(_("Veuillez d'abord sélectionner un client."))
            
        # Commenté car fait référence à des modèles qui n'existent pas (stock.warehouse, etc.)
        # if not self.type_id.track_in_stock or not self.type_id.product_id:
        #     # Simplement changer l'état
        #     self.write({'state': 'installed'})
        #     return True
        #     
        # # Créer un mouvement de stock pour l'allocation
        # warehouse = self.warehouse_id or self.env['stock.warehouse'].search([], limit=1)
        # 
        # # Emplacement source (stock)
        # location_src = self.stock_location_id or warehouse.lot_stock_id
        # # Emplacement destination (client)
        # location_dest = self.env.ref('stock.stock_location_customers')
        # 
        # # Valeurs du mouvement
        # move_vals = {
        #     'name': f"Livraison: {self.reference} à {self.client_id.name}",
        #     'product_id': self.type_id.product_id.id,
        #     'product_uom': self.type_id.product_id.uom_id.id,
        #     'product_uom_qty': 1,
        #     'location_id': location_src.id,
        #     'location_dest_id': location_dest.id,
        #     'it_equipment_id': self.id,
        #     'state': 'draft',
        # }
        # 
        # # Créer le mouvement
        # move = self.env['stock.move'].create(move_vals)
        # move._action_confirm()
        # move._action_assign()
        # move._action_done()
        
        # Mettre à jour l'état
        self.write({
            'state': 'installed',
            # 'stock_location_id': location_dest.id,
            'installation_date': fields.Date.today(),
        })
        
        return True 