# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ITServiceRequest(models.Model):
    _name = 'it.service.request'
    _description = 'Demande de prestation IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char('Référence', readonly=True, default='Nouveau')
    partner_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Demandeur', default=lambda self: self.env.user)
    description = fields.Text('Description des besoins', required=True)
    company_size = fields.Selection([
        ('micro', 'Micro-entreprise (1-9 employés)'),
        ('small', 'TPE (10-49 employés)'),
        ('medium', 'PME (50-249 employés)'),
        ('large', 'Grande entreprise (250+ employés)')
    ], string='Taille de l\'entreprise')
    site_count = fields.Integer('Nombre de sites', default=1)
    employee_count = fields.Integer('Nombre d\'utilisateurs')
    services_needed = fields.Many2many('it.service.type', string='Services souhaités')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('under_review', 'En cours d\'analyse'),
        ('proposal_sent', 'Proposition envoyée'),
        ('proposal_accepted', 'Proposition acceptée'),
        ('invoiced', 'Facturée'),
        ('paid', 'Payée'),
        ('contract_created', 'Contrat créé'),
        ('active', 'Active'),
        ('rejected', 'Rejetée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    contract_id = fields.Many2one('it.contract', string='Contrat associé')
    proposal_attachment_id = fields.Many2one('ir.attachment', string='Proposition commerciale')
    proposal_name = fields.Char('Nom de la proposition', compute='_compute_proposal_name', store=True)
    expected_start_date = fields.Date('Date de début souhaitée')
    invoice_id = fields.Many2one('account.move', string='Facture associée')
    invoice_state = fields.Selection(related='invoice_id.state', string='État de la facture', store=True)
    total_amount = fields.Float('Montant total', compute='_compute_total_amount', store=True)
    
    @api.depends('services_needed', 'site_count', 'employee_count')
    def _compute_total_amount(self):
        """Calcule le montant total de la demande en fonction des services sélectionnés"""
        for record in self:
            total = 0.0
            for service in record.services_needed:
                if service.has_fixed_price:
                    total += service.fixed_price
                if service.has_user_price:
                    total += service.price_per_user * record.employee_count
                if service.has_equipment_price:
                    # Nombre d'équipements estimé
                    equipment_count = record.employee_count  # Par défaut, un équipement par utilisateur
                    total += service.price_per_equipment * equipment_count
            record.total_amount = total
    
    @api.depends('proposal_attachment_id')
    def _compute_proposal_name(self):
        """Calcule le nom à afficher pour la proposition commerciale"""
        for record in self:
            if record.proposal_attachment_id:
                record.proposal_name = record.proposal_attachment_id.name
            else:
                record.proposal_name = False
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('it.service.request') or 'Nouveau'
        return super(ITServiceRequest, self).create(vals_list)
    
    def action_submit(self):
        self.write({'state': 'submitted'})
        # Notifier l'équipe commerciale
        
    def action_review(self):
        self.write({'state': 'under_review'})
    
    def action_send_proposal(self):
        """
        Envoi d'une proposition commerciale au client.
        Cette action ouvre un assistant pour télécharger une pièce jointe.
        """
        self.ensure_one()
        
        # Créer un assistant (wizard) pour télécharger la proposition commerciale
        return {
            'name': _("Envoyer une proposition commerciale"),
            'type': 'ir.actions.act_window',
            'res_model': 'it.service.proposal.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_service_request_id': self.id,
            },
        }
    
    def set_proposal_sent(self, attachment_id):
        """
        Définit la demande comme ayant une proposition envoyée.
        Cette méthode est appelée par l'assistant après le téléchargement du fichier.
        """
        self.ensure_one()
        
        # Récupérer la pièce jointe
        attachment = self.env['ir.attachment'].sudo().browse(attachment_id)
        if not attachment.exists():
            raise ValidationError(_("La pièce jointe n'existe pas."))
        
        # Configurer la pièce jointe
        attachment.write({
            'res_model': 'it.service.request',
            'res_id': self.id,
            'public': True,
            'type': 'binary',
            'mimetype': 'application/pdf',
            'name': f"Proposition_{self.name}.pdf"
        })
        
        # Mettre à jour la demande
        self.write({
            'state': 'proposal_sent',
            'proposal_attachment_id': attachment.id,
        })
        
        # Ajouter un message dans le chatter avec la pièce jointe
        msg = _("Une proposition commerciale a été envoyée au client.")
        self.message_post(
            body=msg,
            attachment_ids=[attachment.id],
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )
        
        # Envoyer un email au client
        template = self.env.ref('it__park.email_template_service_proposal', raise_if_not_found=False)
        if template:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'attachment_ids': [(4, attachment.id)]
                }
            )
    
    def action_accept_proposal(self):
        self.write({'state': 'proposal_accepted'})
        # Créer automatiquement une facture
        self.action_create_invoice()
    
    def action_create_invoice(self):
        """Crée une facture basée sur les services demandés"""
        self.ensure_one()
        
        # Vérifier si le module account est installé
        if not self.env['ir.module.module'].sudo().search([('name', '=', 'account'), ('state', '=', 'installed')]):
            # Si le module de facturation n'est pas installé, passer directement à la création du contrat
            self.action_create_contract()
            return
            
        if not self.services_needed:
            raise ValidationError(_("Aucun service n'a été sélectionné. Impossible de créer une facture."))
            
        # Créer les lignes de facture
        invoice_lines = []
        for service in self.services_needed:
            line_vals = {
                'name': service.name,
                'quantity': 1,
            }
            
            # Ajouter le prix selon le type de tarification
            if service.has_fixed_price:
                line_vals['price_unit'] = service.fixed_price
                
            if service.has_user_price:
                line_vals['name'] += f" ({self.employee_count} utilisateurs)"
                line_vals['price_unit'] = service.price_per_user * self.employee_count
                
            if service.has_equipment_price:
                equipment_count = self.employee_count  # Estimation
                line_vals['name'] += f" ({equipment_count} équipements)"
                line_vals['price_unit'] = service.price_per_equipment * equipment_count
                
            invoice_lines.append((0, 0, line_vals))
            
        # Créer la facture
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'move_type': 'out_invoice',
            'ref': f"Prestation {self.name}",
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced'
        })
        
        # Retourner une action pour voir la facture
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
        
    def action_mark_as_paid(self):
        """Marque la demande comme payée et crée le contrat"""
        self.ensure_one()
        
        if self.state != 'invoiced':
            raise ValidationError(_("La demande doit être facturée avant de pouvoir être marquée comme payée."))
            
        self.write({'state': 'paid'})
        return self.action_create_contract()
    
    def action_create_contract(self):
        # Créer un contrat à partir de la demande
        contract = self.env['it.contract'].create({
            'name': f"Contrat - {self.name}",
            'partner_id': self.partner_id.id,
            'start_date': self.expected_start_date or fields.Date.today(),
            'state': 'draft'
        })
        self.write({
            'state': 'contract_created',
            'contract_id': contract.id
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'it.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_activate(self):
        if not self.contract_id or self.contract_id.state != 'active':
            raise ValidationError(_("Le contrat doit être actif pour activer la prestation."))
        
        # Vérifier si la facture est payée
        if self.invoice_id and self.invoice_id.state != 'posted':
            raise ValidationError(_("La facture doit être validée avant d'activer la prestation."))
            
        self.write({'state': 'active'})
        # Activer l'accès au portail si ce n'est pas déjà fait
        if self.partner_id and not self.partner_id.is_it_client_approved:
            self.partner_id.write({'is_it_client_approved': True})
        
    def action_reject(self):
        self.write({'state': 'rejected'})
        
    def action_cancel(self):
        self.write({'state': 'cancelled'}) 