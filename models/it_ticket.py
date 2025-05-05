from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class ITTicket(models.Model):
    _name = 'it.ticket'
    _description = 'Ticket IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc, id desc'
    
    name = fields.Char('Titre', required=True, tracking=True)
    reference = fields.Char('Référence', readonly=True, copy=False, default='Nouveau')
    description = fields.Text('Description', required=True, tracking=True)
    date_created = fields.Datetime('Date de création', required=True, default=fields.Datetime.now, tracking=True)
    date_closed = fields.Datetime('Date de clôture', tracking=True)
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('in_progress', 'En cours'),
        ('waiting', 'En attente'),
        ('resolved', 'Résolu'),
        ('closed', 'Clôturé'),
        ('cancelled', 'Annulé'),
    ], string='État', default='new', tracking=True)
    
    client_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True, 
                            domain=[('is_it_client', '=', True), ('is_company', '=', True)])
    partner_id = fields.Many2one('res.partner', string='Partenaire', related='client_id', store=True, readonly=False, tracking=True,
                            help="Partenaire associé au ticket (utilisé pour la compatibilité)")
    reporting_user_id = fields.Many2one('res.users', string='Créé par', default=lambda self: self.env.user, tracking=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement concerné', tracking=True)
    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Urgente')
    ], string='Priorité', default='1', tracking=True)
    tech_id = fields.Many2one('it.employee', string='Technicien assigné', tracking=True,
                        domain=[('is_it_technician', '=', True)])
    
    # Champs pour la résolution
    resolution_note = fields.Text('Notes de résolution', tracking=True)
    
    # Notifications
    is_portal_created = fields.Boolean('Créé depuis le portail', default=False)
    notification_sent = fields.Boolean('Notification envoyée', default=False)
    
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence du ticket doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('it.ticket') or 'TIC/000'
        tickets = super(ITTicket, self).create(vals_list)
        for ticket in tickets:
            if ticket.is_portal_created and not ticket.notification_sent:
                ticket._send_notification()
        return tickets
    
    def write(self, values):
        # Mettre à jour les dates de changement d'état
        if values.get('state'):
            if values['state'] == 'closed':
                values['date_closed'] = fields.Datetime.now()
        
        res = super(ITTicket, self).write(values)
        return res
    
    def _send_notification(self):
        """Envoyer une notification aux administrateurs IT"""
        self.ensure_one()
        
        # Trouver les administrateurs IT
        admin_group = self.env.ref('it__park.group_it_admin')
        admin_users = admin_group.users if admin_group else []
        
        if not admin_users:
            _logger.warning("Aucun administrateur IT n'a été trouvé pour envoyer la notification")
            return False
        
        # Créer et envoyer l'e-mail
        mail_template = self.env.ref('it__park.email_template_new_ticket_notification')
        if mail_template:
            for admin in admin_users:
                try:
                    mail_template.send_mail(
                        self.id, 
                        force_send=True,
                        email_values={'recipient_ids': [(6, 0, [admin.partner_id.id])]}
                    )
                except Exception as e:
                    _logger.error(f"Erreur lors de l'envoi de la notification par email: {str(e)}")
        
        # Marquer comme envoyé
        self.notification_sent = True
        
        # Envoyer une notification en temps réel (pour le son)
        self.env['bus.bus']._sendone(
            'it_park_tickets',
            'new_ticket',
            {
                'ticket_id': self.id,
                'title': self.name,
                'reference': self.reference,
                'client_name': self.client_id.name,
                'priority': self.priority,
                'description': self.description[:100] + ('...' if len(self.description) > 100 else ''),
            }
        )
        
        return True
    
    def action_close(self):
        """Clôturer le ticket"""
        if not self.resolution_note:
            raise ValidationError(_("Veuillez fournir des notes de résolution avant de clôturer le ticket."))
            
        self.write({
            'state': 'closed',
            'date_closed': fields.Datetime.now(),
        })
        
        # Ajouter un message dans le chatter
        self.message_post(
            body=_("Ticket clôturé."),
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )
        
    def action_cancel(self):
        """Annuler le ticket"""
        self.write({
            'state': 'cancelled'
        })
        
    def action_resolve(self):
        """Marquer le ticket comme résolu"""
        return {
            'name': _('Résoudre le ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'it.ticket.resolve.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_ticket_name': self.name,
            }
        }
    
    def action_start(self):
        """Démarrer le traitement du ticket"""
        self.write({
            'state': 'in_progress',
        })
        
        # Ajouter un message dans le chatter
        self.message_post(
            body=_("Traitement du ticket démarré."),
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )
        
    def action_wait(self):
        """Mettre le ticket en attente"""
        self.write({
            'state': 'waiting'
        })
        
        # Ajouter un message dans le chatter
        self.message_post(
            body=_("Ticket mis en attente."),
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        ) 