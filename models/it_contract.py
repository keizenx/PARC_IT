from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import logging

_logger = logging.getLogger(__name__)


class ITContractType(models.Model):
    _name = 'it.contract.type'
    _description = 'Type de contrat'
    _order = 'name'
    
    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    
    contract_count = fields.Integer(string='Nombre de contrats', compute='_compute_contract_count')
    
    @api.depends('name')
    def _compute_contract_count(self):
        for record in self:
            record.contract_count = self.env['it.contract'].search_count([
                ('contract_type_id', '=', record.id)
            ])


class ITContract(models.Model):
    _name = 'it.contract'
    _description = 'Contrat de maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    
    name = fields.Char(string='Nom', required=True, tracking=True)
    reference = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('Nouveau'))
    
    partner_id = fields.Many2one('res.partner', string='Client', domain=[('is_company', '=', True)], required=True, tracking=True)
    contract_type_id = fields.Many2one('it.contract.type', string='Type de contrat', tracking=True)
    type = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('support', 'Support'),
        ('rental', 'Location'),
        ('other', 'Autre'),
    ], string='Type', default='maintenance', tracking=True)
    
    start_date = fields.Date(string='Date de début', required=True, tracking=True)
    end_date = fields.Date(string='Date de fin', tracking=True)
    renewal_date = fields.Date(string='Date de renouvellement', tracking=True)
    renewal_reminder = fields.Boolean(string='Rappel de renouvellement', default=True)
    reminder_days = fields.Integer(string='Jours de rappel avant expiration', default=30)
    
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id, tracking=True)
    amount = fields.Monetary(string='Montant', tracking=True, currency_field='currency_id')
    
    # Champs pour la facturation récurrente
    is_recurring = fields.Boolean(string='Facturation récurrente', default=True, tracking=True)
    recurring_interval = fields.Integer(string='Intervalle de facturation', default=1, tracking=True,
                                       help="Intervalle entre deux facturations")
    recurring_rule_type = fields.Selection([
        ('daily', 'Jour(s)'),
        ('weekly', 'Semaine(s)'),
        ('monthly', 'Mois'),
        ('yearly', 'Année(s)'),
    ], string='Fréquence de facturation', default='monthly', tracking=True)
    recurring_invoice_day = fields.Integer(string='Jour de facturation', default=1, tracking=True,
                                          help="Jour du mois pour la facturation")
    recurring_next_date = fields.Date(string='Prochaine date de facturation', tracking=True,
                                    default=lambda self: fields.Date.today())
    # Commenté car les modèles référencés n'existent pas
    # analytic_account_id = fields.Many2one('account.analytic.account', string='Compte analytique', tracking=True)
    # product_id = fields.Many2one('product.product', string='Produit de service', 
    #                            domain=[('type', '=', 'service')], tracking=True,
    #                            help="Produit utilisé pour la facturation de ce contrat")
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'En cours'),
        ('expiring_soon', 'Expirant bientôt'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft', tracking=True)
    
    equipment_ids = fields.One2many('it.equipment', 'contract_id', string='Équipements')
    equipment_count = fields.Integer(string='Nombre d\'équipements', compute='_compute_equipment_count')
    
    license_ids = fields.One2many('it.license', 'contract_id', string='Licences')
    document_ids = fields.One2many('it.document', 'contract_id', string='Documents')
    
    notes = fields.Text(string='Notes')
    
    # Nouveaux champs pour l'intégration avec la facturation récurrente
    # Commenté car sale.subscription n'est pas disponible
    # subscription_id = fields.Many2one('sale.subscription', string='Abonnement associé', tracking=True)
    
    # Produits et services associés au contrat (commenté car product.product n'existe pas)
    # product_ids = fields.Many2many('product.product', 
    #                               'it_contract_product_rel', 'contract_id', 'product_id', 
    #                               string='Produits et services', 
    #                               domain=[('type', '=', 'service')])
    
    # Liens vers les factures générées (commenté car account.move n'existe pas)
    invoice_ids = fields.Many2many('account.move', 
                                 'it_contract_invoice_rel', 'contract_id', 'invoice_id',
                                 string='Factures', copy=False)
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Nombre de factures')
    
    # Champs liés aux livraisons (commentés car stock.picking n'existe pas dans le registre)
    # stock_picking_ids = fields.One2many('stock.picking', 'it_contract_id', string='Livraisons de matériel')
    stock_picking_count = fields.Integer(compute='_compute_stock_picking_count', string='Nombre de livraisons')
    
    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = len(record.equipment_ids)
    
    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)
    
    @api.depends()
    def _compute_stock_picking_count(self):
        """Calcule le nombre de livraisons associées au contrat"""
        for record in self:
            # Commenté car stock.picking n'existe pas dans le registre
            # record.stock_picking_count = len(record.stock_picking_ids)
            record.stock_picking_count = 0
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("La date de fin ne peut pas être antérieure à la date de début."))
    
    @api.model
    def _cron_generate_recurring_invoices(self):
        """Cron pour générer automatiquement les factures récurrentes"""
        today = fields.Date.today()
        
        # Récupérer les contrats actifs avec facturation récurrente et à facturer aujourd'hui
        contracts = self.search([
            ('state', '=', 'active'),
            ('is_recurring', '=', True),
            ('recurring_next_date', '<=', today)
        ])
        
        _logger.info(f"Génération de factures récurrentes pour {len(contracts)} contrats")
        
        created_invoices = self.env['account.move']
        for contract in contracts:
            try:
                invoice = contract._create_recurring_invoice()
                if invoice:
                    created_invoices += invoice
                    _logger.info(f"Facture créée pour le contrat {contract.name} (ID: {contract.id})")
                else:
                    _logger.warning(f"Échec de création de facture pour le contrat {contract.name} (ID: {contract.id})")
            except Exception as e:
                _logger.error(f"Erreur lors de la création de facture pour le contrat {contract.name} (ID: {contract.id}): {str(e)}")
        
        return created_invoices
    
    def _create_recurring_invoice(self):
        """Créer une facture récurrente pour ce contrat"""
        self.ensure_one()
        
        # Cette fonction est désactivée car elle utilise account.move et product.product qui n'existent pas
        _logger.warning(f"Fonction _create_recurring_invoice désactivée pour le contrat {self.name} car elle dépend de modules non installés")
        return False
    
    def _compute_next_invoice_date(self):
        """Calculer la prochaine date de facturation"""
        self.ensure_one()
        
        current_date = self.recurring_next_date or fields.Date.today()
        
        if self.recurring_rule_type == 'daily':
            next_date = current_date + timedelta(days=self.recurring_interval)
        elif self.recurring_rule_type == 'weekly':
            next_date = current_date + timedelta(weeks=self.recurring_interval)
        elif self.recurring_rule_type == 'monthly':
            # Ajouter le nombre de mois
            next_date = current_date + relativedelta(months=self.recurring_interval)
            # Ajuster au jour de facturation spécifié
            if self.recurring_invoice_day:
                # Vérifier si le jour existe dans le mois (ex: 31 pour février)
                max_day = calendar.monthrange(next_date.year, next_date.month)[1]
                day = min(self.recurring_invoice_day, max_day)
                next_date = next_date.replace(day=day)
        elif self.recurring_rule_type == 'yearly':
            next_date = current_date + relativedelta(years=self.recurring_interval)
        else:
            # Par défaut, mensuel
            next_date = current_date + relativedelta(months=1)
        
        self.recurring_next_date = next_date
        
        return next_date
    
    def button_sign(self):
        """Signer le contrat et le mettre en état actif"""
        for record in self:
            record.write({
                'state': 'active',
                'recurring_next_date': fields.Date.today(),  # Première facturation dès aujourd'hui ou selon paramétrage
            })
        return True
    
    def button_renew(self):
        """Renouveler le contrat expiré ou expirant bientôt"""
        for record in self:
            record.write({'state': 'active'})
            # Commenté car sale.subscription n'est pas disponible
            # if record.subscription_id:
            #     record.subscription_id.write({
            #         'date': record.end_date,
            #         'recurring_next_date': fields.Date.today(),
            #     })
        return True
    
    def button_expire(self):
        """Marquer le contrat comme expiré"""
        for record in self:
            record.write({'state': 'expired'})
            # Commenté car sale.subscription n'est pas disponible
            # if record.subscription_id:
            #     record.subscription_id.set_close()
        return True
    
    def button_cancel(self):
        """Annuler le contrat"""
        for record in self:
            record.write({'state': 'cancelled'})
            # Commenté car sale.subscription n'est pas disponible
            # if record.subscription_id:
            #     record.subscription_id.set_close()
        return True
    
    def _create_subscription(self):
        """Créer un abonnement pour la facturation récurrente du contrat"""
        # Méthode commentée car sale.subscription n'est pas disponible
        return False
    
    def action_view_subscription(self):
        """Ouvrir la vue de l'abonnement associé"""
        # Méthode commentée car sale.subscription n'est pas disponible
        return False
    
    def action_view_invoices(self):
        """Voir les factures liées à ce contrat"""
        self.ensure_one()
        # Commenté car account.move n'existe pas
        # return {
        #    'name': _('Factures'),
        #    'type': 'ir.actions.act_window',
        #    'view_mode': 'tree,form',
        #    'res_model': 'account.move',
        #    'domain': [('id', 'in', self.invoice_ids.ids)],
        # }
        return {
            'name': _('Contrat'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'it.contract',
            'res_id': self.id,
        }
    
    def action_view_stock_pickings(self):
        """Affiche les livraisons liées à ce contrat"""
        # Commenté car stock.picking n'existe pas dans le registre
        return {
            'name': 'Livraisons',
            'type': 'ir.actions.act_window',
            'res_model': 'it.contract',  # Modifié pour éviter l'erreur
            'view_mode': 'list,form',
            'domain': [('id', '=', self.id)],
            'context': {'create': False}
        }
    
    def action_create_delivery(self):
        """Créer une livraison pour les équipements du contrat"""
        self.ensure_one()
        if not self.equipment_ids:
            return False
            
        # À implémenter en fonction des besoins spécifiques
        return True
    
    @api.model
    def _cron_check_contracts_expiration(self):
        """Vérifier chaque jour les contrats qui arrivent à expiration"""
        today = fields.Date.today()
        
        # Contrats actifs arrivant à expiration
        soon_expired_contracts = self.search([
            ('state', '=', 'active'),
            ('end_date', '!=', False),
            ('end_date', '<=', today + timedelta(days=30)),
            ('end_date', '>=', today)
        ])
        
        for contract in soon_expired_contracts:
            if contract.state != 'expiring_soon':
                contract.write({'state': 'expiring_soon'})
                # Notifier les personnes concernées
                contract.message_post(
                    body=_("Ce contrat arrive à expiration le %s.") % format(contract.end_date),
                    subject=_("Contrat arrivant à expiration"),
                    message_type='notification'
                )
                
        # Contrats expirés mais toujours actifs
        expired_contracts = self.search([
            ('state', 'in', ['active', 'expiring_soon']),
            ('end_date', '!=', False),
            ('end_date', '<', today)
        ])
        
        for contract in expired_contracts:
            contract.write({'state': 'expired'})
            contract.message_post(
                body=_("Ce contrat a expiré le %s.") % format(contract.end_date),
                subject=_("Contrat expiré"),
                message_type='notification'
            )
            
        return True
        
    @api.model
    def _init_missing_tables(self):
        """Initialise les tables de relation manquantes pour les contrats"""
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'it_contract_invoice_rel'
            )
        """)
        table_exists = self.env.cr.fetchone()[0]
        
        if not table_exists:
            _logger.info("Création de la table de relation it_contract_invoice_rel")
            self.env.cr.execute("""
                CREATE TABLE it_contract_invoice_rel (
                    contract_id INTEGER NOT NULL,
                    invoice_id INTEGER NOT NULL,
                    PRIMARY KEY (contract_id, invoice_id)
                )
            """)
            
        return True 
    
    def action_view_contract_detail(self):
        """Afficher les détails du contrat dans le portail"""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        contract_url = f"{base_url}/my/contracts/{self.id}"
        return {
            'type': 'ir.actions.act_url',
            'url': contract_url,
            'target': 'self',
        } 