from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ITInterventionType(models.Model):
    _name = 'it.intervention.type'
    _description = 'Type d\'intervention'
    _order = 'name'
    
    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    is_billable = fields.Boolean(string='Facturable par défaut', default=False)
    
    intervention_count = fields.Integer(string='Nombre d\'interventions', compute='_compute_intervention_count')
    
    @api.depends('name')
    def _compute_intervention_count(self):
        for record in self:
            record.intervention_count = self.env['it.intervention'].search_count([
                ('intervention_type_id', '=', record.id)
            ])


class ITIntervention(models.Model):
    _name = 'it.intervention'
    _description = 'Intervention Technique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'
    
    name = fields.Char(string='Titre', required=True, tracking=True)
    reference = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('Nouvelle'))
    
    incident_id = fields.Many2one('it.incident', string='Incident', ondelete='cascade', tracking=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement', tracking=True)
    
    client_id = fields.Many2one('res.partner', string='Client', tracking=True)
    
    intervention_type = fields.Selection([
        ('installation', 'Installation'),
        ('maintenance', 'Maintenance'),
        ('repair', 'Réparation'),
        ('support', 'Support'),
        ('training', 'Formation'),
        ('other', 'Autre')
    ], string='Type d\'intervention', default='support', tracking=True)
    
    intervention_type_id = fields.Many2one('it.intervention.type', string='Type d\'intervention', tracking=True)
    
    is_billable = fields.Boolean(string='Facturable', default=False, tracking=True)
    invoiced = fields.Boolean(string='Facturé', default=False, tracking=True)
    
    # Champs pour la facturation (commenté car account.move n'existe pas)
    # invoice_ids = fields.Many2many('account.move', string='Factures', copy=False)
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Nombre de factures')
    invoice_status = fields.Selection([
        ('to_invoice', 'À facturer'),
        ('invoiced', 'Facturé'),
        ('no', 'Non facturable')
    ], string='Statut de facturation', compute='_compute_invoice_status', store=True)
    
    # Prix et produit pour la facturation
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    hourly_rate = fields.Float(string='Taux horaire', default=75.0)
    price_total = fields.Monetary(string='Montant total', compute='_compute_price_total', store=True, currency_field='currency_id')
    # Commenté car product.product n'existe pas
    # product_id = fields.Many2one('product.product', string='Produit de service', 
    #                           domain=[('type', '=', 'service')],
    #                           help="Produit utilisé pour la facturation de cette intervention")
    
    equipment_ids = fields.Many2many('it.equipment', string='Équipements', tracking=True)
    
    report = fields.Text(string='Rapport d\'intervention', tracking=True)
    
    employee_id = fields.Many2one('it.employee', string='Technicien', required=True, tracking=True)
    technician_id = fields.Many2one('res.users', string='Utilisateur associé', related='employee_id.user_id', store=True, readonly=True)
    
    department_id = fields.Many2one('res.partner', string='Département', related='employee_id.department_id', store=True, readonly=True)
    
    team_member_ids = fields.Many2many('it.employee', 'it_intervention_team_rel', 'intervention_id', 'employee_id', 
                                        string='Équipe d\'intervention', domain=[('it_technician', '=', True)])
    
    start_datetime = fields.Datetime(string='Date de début', required=True, default=fields.Datetime.now, tracking=True)
    end_datetime = fields.Datetime(string='Date de fin', tracking=True)
    duration = fields.Float(string='Durée (heures)', compute='_compute_duration', store=True, tracking=True)
    
    description = fields.Text(string='Description des travaux', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('done', 'Terminée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='draft', tracking=True)
    
    # Commenté car account.analytic.line n'existe pas
    # timesheet_ids = fields.One2many('account.analytic.line', 'it_intervention_id', string='Feuilles de temps')
    contract_id = fields.Many2one('it.contract', string='Contrat associé', tracking=True)
    
    planned_hours = fields.Float(string='Heures prévues', default=1.0)
    effective_hours = fields.Float(string='Heures effectuées', compute='_compute_effective_hours', store=True)
    remaining_hours = fields.Float(string='Heures restantes', compute='_compute_remaining_hours', store=True)
    overtime = fields.Float(string='Heures supplémentaires', compute='_compute_overtime', store=True)
    
    @api.depends()
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = 0  # Valeur par défaut car invoice_ids n'existe pas
            
    @api.depends('is_billable', 'invoiced', 'state')
    def _compute_invoice_status(self):
        for record in self:
            if not record.is_billable:
                record.invoice_status = 'no'
            elif record.invoiced:
                record.invoice_status = 'invoiced'
            elif record.state == 'done':
                record.invoice_status = 'to_invoice'
            else:
                record.invoice_status = 'no'
    
    @api.depends('duration', 'hourly_rate')
    def _compute_price_total(self):
        for record in self:
            record.price_total = record.duration * record.hourly_rate
    
    @api.depends()
    def _compute_effective_hours(self):
        for record in self:
            # record.effective_hours = sum(record.timesheet_ids.mapped('unit_amount'))
            record.effective_hours = 0  # Valeur par défaut car timesheet_ids est commenté
    
    @api.depends('planned_hours', 'effective_hours')
    def _compute_remaining_hours(self):
        for record in self:
            if record.state == 'done':
                record.remaining_hours = 0
            else:
                record.remaining_hours = record.planned_hours - record.effective_hours
    
    @api.depends('planned_hours', 'effective_hours')
    def _compute_overtime(self):
        for record in self:
            if record.effective_hours > record.planned_hours:
                record.overtime = record.effective_hours - record.planned_hours
            else:
                record.overtime = 0
    
    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for record in self:
            if record.start_datetime and record.end_datetime:
                duration = (record.end_datetime - record.start_datetime).total_seconds() / 3600.0
                record.duration = round(duration, 2)
            else:
                record.duration = 0.0
    
    @api.onchange('intervention_type_id')
    def _onchange_intervention_type(self):
        if self.intervention_type_id:
            self.is_billable = self.intervention_type_id.is_billable
    
    @api.onchange('equipment_id')
    def _onchange_equipment(self):
        if self.equipment_id:
            self.client_id = self.equipment_id.client_id
            self.contract_id = self.equipment_id.contract_id
            
            # Vérifier si l'intervention est couverte par un contrat
            if self.contract_id and self.contract_id.state == 'running':
                self.is_billable = False
    
    def action_view_timesheets(self):
        """Voir les feuilles de temps associées à cette intervention"""
        self.ensure_one()
        # Commenté car account.analytic.line n'existe pas
        # return {
        #    'name': _('Feuilles de temps'),
        #    'type': 'ir.actions.act_window',
        #    'view_mode': 'tree,form',
        #    'res_model': 'account.analytic.line',
        #    'domain': [('it_intervention_id', '=', self.id)],
        #    'context': {'default_it_intervention_id': self.id}
        # }
        return {
            'name': _('Intervention'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'it.intervention',
            'res_id': self.id,
        }
        
    def action_view_invoices(self):
        """Voir les factures associées à cette intervention"""
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
            'name': _('Intervention'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'it.intervention',
            'res_id': self.id,
        }
    
    def action_create_invoice(self):
        """Créer une facture pour cette intervention"""
        self.ensure_one()
        
        if not self.is_billable or self.state != 'done':
            raise ValidationError(_("Seules les interventions terminées et facturables peuvent être facturées."))
            
        if not self.client_id:
            raise ValidationError(_("Veuillez spécifier un client pour cette intervention."))
        
        # Cette fonction est désactivée car elle utilise account.move et product.product qui n'existent pas
        self.write({'invoiced': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Facturation'),
                'message': _('Cette fonctionnalité est désactivée car elle nécessite des modules qui ne sont pas installés (account, product).'),
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def action_start(self):
        """Démarrer l'intervention"""
        for record in self:
            if not self._check_technician_availability(record.employee_id, record.start_datetime):
                raise ValidationError(_("Le technicien %s n'est pas disponible à cette date.") % record.employee_id.name)
                
            record.write({
                'state': 'in_progress',
                'start_datetime': fields.Datetime.now(),
            })
            
            # Méthodes commentées car account.analytic.line n'existe pas
            # self._create_timesheet_entry(record, 0.0)
            
        return True
    
    def action_done(self):
        """Terminer l'intervention"""
        for record in self:
            end_time = fields.Datetime.now()
            record.write({
                'state': 'done',
                'end_datetime': end_time,
            })
            
            duration = (end_time - record.start_datetime).total_seconds() / 3600.0
            # Méthodes commentées car account.analytic.line n'existe pas
            # self._update_timesheet_entry(record, duration)
            
            if record.incident_id and record.incident_id.state != 'resolved':
                record.incident_id.write({
                    'state': 'resolved',
                    'resolution_date': fields.Datetime.now(),
                    'resolution_summary': record.report,
                })
                
        return True
    
    def action_cancel(self):
        """Annuler l'intervention"""
        for record in self:
            record.write({
                'state': 'cancelled',
            })
            # Méthodes commentées car account.analytic.line n'existe pas
            # record.timesheet_ids.unlink()
        return True
    
    def action_reset(self):
        """Réinitialiser l'intervention"""
        for record in self:
            record.write({
                'state': 'draft',
                'end_datetime': False,
            })
            # Méthodes commentées car account.analytic.line n'existe pas
            # record.timesheet_ids.unlink()
        return True
        
    def button_plan(self):
        """Planifier l'intervention"""
        for record in self:
            record.write({
                'state': 'planned',
            })
        return True
    
    def _check_technician_availability(self, employee, start_datetime):
        """Vérifier si le technicien est disponible à la date donnée"""
        # Vérifier si le module hr_holidays est installé
        if 'hr.leave' in self.env:
            holidays = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('date_from', '<=', start_datetime),
                ('date_to', '>=', start_datetime),
                ('state', '=', 'validate'),
            ])
            if holidays:
                return False
            
        # Vérifier les autres interventions
        other_interventions = self.search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['planned', 'in_progress']),
            ('start_datetime', '<=', start_datetime),
            ('end_datetime', '>=', start_datetime),
            ('id', '!=', self.id),
        ])
        if other_interventions:
            return False
            
        return True
    
    # Méthodes commentées car account.analytic.line n'existe pas
    # def _create_timesheet_entry(self, intervention, hours):
    #     """Créer une entrée de feuille de temps pour cette intervention"""
    #     analytic_line_vals = {
    #         'name': intervention.name,
    #         'date': fields.Date.today(),
    #         'unit_amount': hours,
    #         'employee_id': intervention.employee_id.id,
    #         'it_intervention_id': intervention.id,
    #     }
    #     
    #     # Si le module account_analytic_default est installé, chercher le compte analytique par défaut
    #     AnalyticDefault = self.env.get('account.analytic.default')
    #     if AnalyticDefault:
    #         domain = [
    #             ('employee_id', '=', intervention.employee_id.id),
    #         ]
    #         analytic_default = AnalyticDefault.sudo().search(domain, limit=1)
    #         if analytic_default and analytic_default.analytic_id:
    #             analytic_line_vals['account_id'] = analytic_default.analytic_id.id
    #     
    #     # Vérifier si intervention.contract_id a un compte analytique
    #     if intervention.contract_id and intervention.contract_id.analytic_account_id:
    #         analytic_line_vals['account_id'] = intervention.contract_id.analytic_account_id.id
    #     
    #     # Créer l'entrée de feuille de temps
    #     try:
    #         timesheet = self.env['account.analytic.line'].sudo().create(analytic_line_vals)
    #         return timesheet
    #     except Exception as e:
    #         _logger.error(f"Erreur lors de la création de la feuille de temps: {str(e)}")
    #         return False
    # 
    # def _update_timesheet_entry(self, intervention, hours):
    #     """Mettre à jour l'entrée de feuille de temps existante pour cette intervention"""
    #     # Chercher la dernière entrée de feuille de temps
    #     timesheet = self.env['account.analytic.line'].sudo().search([
    #         ('it_intervention_id', '=', intervention.id),
    #     ], order='create_date desc', limit=1)
    #     
    #     if not timesheet:
    #         return self._create_timesheet_entry(intervention, hours)
    #     
    #     try:
    #         timesheet.write({
    #             'unit_amount': hours,
    #         })
    #         return timesheet
    #     except Exception as e:
    #         _logger.error(f"Erreur lors de la mise à jour de la feuille de temps: {str(e)}")
    #         return False 