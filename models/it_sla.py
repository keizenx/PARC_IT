from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class ITSLAPolicy(models.Model):
    _name = 'it.sla.policy'
    _description = 'Politique SLA'
    _order = 'sequence, id'
    
    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, string='Actif')
    sequence = fields.Integer(default=10)
    
    # Configuration de temps
    time_days = fields.Integer(string='Jours', default=0)
    time_hours = fields.Integer(string='Heures', default=0)
    time_minutes = fields.Integer(string='Minutes', default=0)
    
    # Type de SLA
    sla_type = fields.Selection([
        ('response', 'Temps de réponse'),
        ('resolution', 'Temps de résolution')
    ], string='Type de SLA', default='response', required=True)
    
    # Critères d'applicabilité
    priority = fields.Selection([
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('all', 'Toutes')
    ], string='Priorité applicable', default='all', required=True)
    
    # Renommer category_ids en incident_category_ids pour correspondre à la vue
    incident_category_ids = fields.Many2many(
        'it.incident.category',
        'it_sla_category_rel',
        'sla_id',
        'category_id',
        string='Catégories applicables'
    )
    
    incident_type_ids = fields.Many2many(
        'it.incident.type',
        'it_sla_incident_type_rel',
        'sla_id',
        'type_id',
        string='Types d\'incidents applicables'
    )
    
    # Ajouter les champs manquants
    incident_priority_ids = fields.Many2many(
        'it.incident.priority',
        'it_sla_priority_rel',
        'sla_id',
        'priority_id',
        string='Priorités applicables'
    )
    
    team_ids = fields.Many2many(
        'helpdesk.team',
        'it_sla_team_rel',
        'sla_id',
        'team_id',
        string='Équipes applicables'
    )
    
    # Utilisé pour lier aux incidents
    incident_count = fields.Integer(compute='_compute_incident_count', string='Nombre d\'incidents')
    incident_ids = fields.One2many('it.incident', 'sla_policy_id', string='Incidents associés')
    
    # Règles de notification
    notify_before_deadline = fields.Boolean(string='Notifier avant l\'échéance', default=True)
    notify_hours_before = fields.Integer(string='Heures avant échéance', default=2)
    notify_on_breach = fields.Boolean(string='Notifier en cas de dépassement', default=True)
    
    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for record in self:
            record.incident_count = len(record.incident_ids)
    
    def get_target_deadline(self, creation_date):
        """Calcule la date limite cible en fonction des paramètres du SLA"""
        self.ensure_one()
        if not creation_date:
            return False
            
        deadline = fields.Datetime.from_string(creation_date)
        deadline += timedelta(days=self.time_days, hours=self.time_hours, minutes=self.time_minutes)
        
        return fields.Datetime.to_string(deadline)
    
    def action_view_incidents(self):
        self.ensure_one()
        return {
            'name': _('Incidents'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'it.incident',
            'domain': [('sla_policy_id', '=', self.id)],
            'context': {'default_sla_policy_id': self.id},
        }


class ITSLAStatus(models.Model):
    _name = 'it.sla.status'
    _description = 'Statut SLA'
    
    name = fields.Char(related='sla_policy_id.name', string='Nom du SLA')
    sla_policy_id = fields.Many2one('it.sla.policy', string='Politique SLA', required=True, ondelete='cascade')
    incident_id = fields.Many2one('it.incident', string='Incident', required=True, ondelete='cascade')
    
    deadline = fields.Datetime(string='Date limite')
    reached_date = fields.Datetime(string='Date atteinte')
    status = fields.Selection([
        ('ongoing', 'En cours'),
        ('reached', 'Atteint'),
        ('failed', 'Échoué')
    ], string='Statut', default='ongoing', compute='_compute_status', store=True)
    
    sla_type = fields.Selection(related='sla_policy_id.sla_type', string='Type de SLA', store=True)
    color = fields.Integer(compute='_compute_color', string='Couleur')
    
    @api.depends('deadline', 'reached_date')
    def _compute_status(self):
        now = fields.Datetime.now()
        for record in self:
            if record.reached_date:
                if record.reached_date <= record.deadline:
                    record.status = 'reached'
                else:
                    record.status = 'failed'
            elif record.deadline and record.deadline < now:
                record.status = 'failed'
            else:
                record.status = 'ongoing'
    
    @api.depends('status')
    def _compute_color(self):
        for record in self:
            if record.status == 'reached':
                record.color = 10  # Vert
            elif record.status == 'failed':
                record.color = 1   # Rouge
            else:
                record.color = 4   # Bleu
    
    def mark_as_reached(self):
        self.write({'reached_date': fields.Datetime.now()})
        
    def get_remaining_time(self):
        """Retourne le temps restant avant la date limite en format lisible"""
        self.ensure_one()
        if not self.deadline or self.status != 'ongoing':
            return False
            
        now = fields.Datetime.now()
        if now > self.deadline:
            return _("Dépassé")
            
        delta = fields.Datetime.from_string(self.deadline) - fields.Datetime.from_string(now)
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return _("{} jours, {} heures").format(days, hours)
        elif hours > 0:
            return _("{} heures, {} minutes").format(hours, minutes)
        else:
            return _("{} minutes").format(minutes)
            
    @api.model
    def _cron_check_sla_status(self):
        """Tâche planifiée pour vérifier et mettre à jour les statuts SLA"""
        _logger.info("Exécution de la tâche planifiée : Vérification des statuts SLA")
        
        now = fields.Datetime.now()
        
        # Trouver tous les SLA en cours dont la deadline est dépassée
        overdue_slas = self.search([
            ('status', '=', 'ongoing'),
            ('deadline', '<', now)
        ])
        
        if overdue_slas:
            # Marquer les SLA comme échoués
            overdue_slas.write({
                'status': 'failed'
            })
            
            # Notifier les administrateurs pour chaque SLA échoué
            for sla in overdue_slas:
                # Vérifier si l'incident existe encore
                if sla.incident_id:
                    sla.incident_id.message_post(
                        body=_("⚠️ SLA non respecté: %s. La date limite était %s.") % 
                             (sla.name, fields.Datetime.to_string(sla.deadline)),
                        message_type='notification',
                        subtype_xmlid='mail.mt_comment'
                    )
                    
                    # Informer le technicien assigné si disponible
                    if sla.incident_id.tech_id and sla.incident_id.tech_id.user_id:
                        tech_partner = sla.incident_id.tech_id.user_id.partner_id
                        if tech_partner:
                            sla.incident_id.message_post(
                                body=_("⚠️ Alerte SLA: La date limite pour '%s' a été dépassée.") % sla.name,
                                message_type='notification',
                                subtype_xmlid='mail.mt_comment',
                                partner_ids=[tech_partner.id]
                            )

class ITSLA(models.Model):
    _name = 'it.sla'
    _description = 'Accord de niveau de service IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nom', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Actif', default=True)
    
    # Délais de réponse et résolution
    response_time = fields.Float('Temps de réponse (heures)', default=4.0)
    resolution_time = fields.Float('Temps de résolution (heures)', default=24.0)
    
    # Priorités et types d'incidents concernés
    priority_ids = fields.Many2many('it.incident.priority', string='Priorités applicables')
    incident_type_ids = fields.Many2many('it.incident.type', string='Types d\'incidents')
    
    # Heures de service
    working_hours_start = fields.Float('Début des heures de service', default=8.0)
    working_hours_end = fields.Float('Fin des heures de service', default=18.0)
    working_days = fields.Many2many('resource.calendar.attendance', string='Jours ouvrés')
    
    # Pénalités et escalade
    penalty_amount = fields.Float('Montant des pénalités', help="Montant des pénalités en cas de non-respect du SLA")
    escalation_user_ids = fields.Many2many('res.users', string='Utilisateurs pour l\'escalade',
        help="Utilisateurs à notifier en cas de dépassement du SLA")
    
    @api.model
    def calculate_deadline(self, create_date, hours):
        """Calcule la date limite en tenant compte des heures de travail"""
        if not hours:
            return False
            
        deadline = fields.Datetime.from_string(create_date)
        working_hours = self.working_hours_end - self.working_hours_start
        
        remaining_hours = hours
        while remaining_hours > 0:
            # Ajouter un jour si on dépasse les heures de travail
            if deadline.hour >= int(self.working_hours_end):
                deadline = deadline + timedelta(days=1)
                deadline = deadline.replace(hour=int(self.working_hours_start))
            
            # Calculer les heures restantes dans la journée
            hours_today = min(
                remaining_hours,
                self.working_hours_end - max(deadline.hour, self.working_hours_start)
            )
            
            deadline = deadline + timedelta(hours=hours_today)
            remaining_hours -= hours_today
            
        return fields.Datetime.to_string(deadline)