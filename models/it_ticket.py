from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger(__name__)

class ITTicket(models.Model):
    _name = 'it.ticket'
    _description = 'Ticket IT'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date_created desc, id desc'
    
    name = fields.Char('Titre', required=True, tracking=True)
    reference = fields.Char('Référence', readonly=True, copy=False, default='Nouveau')
    ticket_ref = fields.Char('ID Ticket', compute='_compute_ticket_ref', store=True, index=True)
    description = fields.Text('Description', required=True, tracking=True)
    date_created = fields.Datetime('Date de création', required=True, default=fields.Datetime.now, tracking=True)
    date_closed = fields.Datetime('Date de clôture', tracking=True)
    category_id = fields.Many2one('it.ticket.category', string='Catégorie', required=True, tracking=True)
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
    partner_id = fields.Many2one('res.partner', string='Contact', tracking=True,
                            help="Contact spécifique associé au ticket")
    reporting_user_id = fields.Many2one('res.users', string='Créé par', default=lambda self: self.env.user, tracking=True)
    equipment_id = fields.Many2one('it.equipment', string='Équipement concerné', tracking=True)
    site_id = fields.Many2one('res.partner', string='Site concerné', domain="[('is_it_site', '=', True)]", tracking=True)
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
    
    # Pièces jointes
    attachment_ids = fields.Many2many('ir.attachment', string='Pièces jointes', copy=False)
    
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence du ticket doit être unique!')
    ]
    
    @api.model
    def create_test_ticket(self):
        """
        Créer un ticket de test pour l'utilisateur actuellement connecté
        pour vérifier si l'affichage dans le portail fonctionne correctement
        """
        # Récupérer l'utilisateur courant et son partenaire associé
        user = self.env.user
        partner = user.partner_id
        
        # Trouver le client associé (la société)
        client = partner
        if not partner.is_company and partner.parent_id:
            client = partner.parent_id
        
        # Trouver une catégorie
        category = self.env['it.ticket.category'].search([], limit=1)
        if not category:
            # Créer une catégorie si aucune n'existe
            category = self.env['it.ticket.category'].create({
                'name': 'Test Category',
                'code': 'TEST'
            })
        
        # Créer le ticket
        vals = {
            'name': 'Ticket de test pour portail',
            'description': 'Ceci est un ticket de test créé pour vérifier l\'affichage dans le portail client.',
            'client_id': client.id,
            'partner_id': partner.id,
            'category_id': category.id,
            'priority': '1',
            'state': 'new',
            'is_portal_created': True
        }
        
        ticket = self.create(vals)
        _logger.info(f"Ticket de test créé: ID={ticket.id}, Référence={ticket.reference}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ticket de test créé',
                'message': f'Un ticket de test a été créé avec la référence {ticket.reference}',
                'sticky': False,
                'type': 'success'
            }
        }
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('it.ticket') or 'TIC/000'
            
            # Assurer la cohérence entre client_id et partner_id pour le portail
            if vals.get('client_id') and not vals.get('partner_id'):
                # Le contact par défaut est le client lui-même
                vals['partner_id'] = vals['client_id']
            elif vals.get('partner_id') and not vals.get('client_id'):
                # Si on a seulement partner_id, on vérifie si c'est une entreprise, sinon on prend son parent
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if partner.is_company:
                    vals['client_id'] = vals['partner_id']
                elif partner.parent_id:
                    vals['client_id'] = partner.parent_id.id
                else:
                    # Si le partenaire n'a pas de parent, on l'utilise comme client aussi
                    vals['client_id'] = vals['partner_id']

        tickets = super(ITTicket, self).create(vals_list)
        
        # Après création, vérifier et envoyer notifications si nécessaire
        for ticket in tickets:
            if ticket.is_portal_created and not ticket.notification_sent:
                ticket._send_notification()
                
            # On s'assure que le client a accès au portail IT
            if ticket.client_id:
                if not ticket.client_id.is_it_client:
                    ticket.client_id.write({
                        'is_it_client': True,
                        'is_it_client_approved': True
                    })
                    _logger.info(f"Client {ticket.client_id.name} (ID: {ticket.client_id.id}) activé comme client IT")
        
        return tickets
    
    def write(self, values):
        # Mettre à jour les dates de changement d'état
        if values.get('state'):
            if values['state'] == 'closed':
                values['date_closed'] = fields.Datetime.now()
        
        res = super(ITTicket, self).write(values)
        return res
    
    def _send_notification(self):
        """Envoyer une notification aux administrateurs IT via l'interface Odoo"""
        self.ensure_one()
        
        # Trouver les administrateurs IT
        admin_users = []
        try:
            admin_group = self.env.ref('it__park.group_it_admin', raise_if_not_found=False)
            if admin_group:
                admin_users = admin_group.users
        except Exception as e:
            _logger.warning(f"Groupe d'administrateurs IT non trouvé: {str(e)}")
        
        # Si aucun admin trouvé, utiliser les administrateurs système
        if not admin_users:
            admin_users = self.env['res.users'].sudo().search([('share', '=', False)])
            _logger.info(f"Utilisation des administrateurs généraux ({len(admin_users)}) car aucun administrateur IT n'a été trouvé")
        
        if not admin_users:
            _logger.warning("Aucun administrateur n'a été trouvé pour envoyer la notification")
            return False

        try:
            # Créer une notification utilisateur directement dans Odoo
            title = f"Nouveau ticket: {self.name}"
            message = f"Un nouveau ticket a été créé par {self.client_id.name}\nRéférence: {self.reference}\nPriorité: {self.get_priority_display()}"
            
            admin_users_ids = admin_users.ids
            
            if admin_users_ids:
                # Envoyer les notifications dans l'interface
                self.env['mail.bus']._sendmany([
                    (admin_id, 'mail.simple_notification', 
                     {'title': title, 'message': message, 'sticky': True, 'warning': True}) 
                    for admin_id in admin_users_ids
                ])
                
                # Créer des activités pour chaque administrateur
                for admin in admin_users:
                    self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'note': f'Nouveau ticket #{self.reference} créé par {self.client_id.name}: {self.name}',
                        'user_id': admin.id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1).id,
                        'summary': 'Nouveau ticket créé via le portail',
                    })
                
                _logger.info(f"Notifications envoyées à {len(admin_users_ids)} administrateurs")
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi des notifications: {str(e)}")
        
        # Marquer comme envoyé
        self.notification_sent = True
        
        # Envoyer une notification en temps réel (pour le son)
        try:
            self.env['bus.bus']._sendone(
                'it_park_tickets',
                'new_ticket',
                {
                    'ticket_id': self.id,
                    'title': self.name,
                    'reference': self.reference,
                    'client_name': self.client_id.name,
                    'priority': self.get_priority_display(),
                    'description': self.description[:100] + ('...' if len(self.description) > 100 else ''),
                    'sound': True,
                    'notification_type': 'new_ticket_alert'
                }
            )
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de la notification en temps réel: {str(e)}")
        
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

    @api.depends('reference')
    def _compute_ticket_ref(self):
        """Calcule ticket_ref à partir de reference pour la compatibilité avec les templates de portail"""
        for ticket in self:
            ticket.ticket_ref = ticket.reference

    def get_priority_display(self):
        """Retourne la valeur affichable de la priorité"""
        priorities = {
            '0': 'Basse',
            '1': 'Normale',
            '2': 'Haute',
            '3': 'Urgente'
        }
        return priorities.get(self.priority, 'Normale')

class ITTicketCategory(models.Model):
    _name = 'it.ticket.category'
    _description = 'Catégorie de ticket IT'
    _order = 'sequence, name'

    name = fields.Char('Nom', required=True, translate=True)
    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Séquence', default=10)
    active = fields.Boolean('Actif', default=True)
    description = fields.Text('Description', translate=True)
    parent_id = fields.Many2one('it.ticket.category', string='Catégorie parente')
    child_ids = fields.One2many('it.ticket.category', 'parent_id', string='Sous-catégories')
    color = fields.Integer('Couleur')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code de la catégorie doit être unique!')
    ] 