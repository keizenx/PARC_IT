# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class ITIncident(models.Model):
    _name = 'it.incident'
    _description = 'Incident IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_reported desc, id desc'
    
    name = fields.Char('Titre', required=True, tracking=True)
    reference = fields.Char('Référence', readonly=True, copy=False, default='Nouveau')
    description = fields.Text('Description', required=True, tracking=True)
    date_reported = fields.Datetime('Date de signalement', required=True, default=fields.Datetime.now, tracking=True)
    date_assigned = fields.Datetime('Date d\'assignation', tracking=True)
    date_start = fields.Datetime('Date de début', tracking=True)
    date_end = fields.Datetime('Date de fin', tracking=True)
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('assigned', 'Assigné'),
        ('in_progress', 'En cours'),
        ('waiting', 'En attente'),
        ('resolved', 'Résolu'),
        ('closed', 'Clôturé'),
        ('cancelled', 'Annulé'),
    ], string='État', default='new', tracking=True)
    
    client_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True, 
                             domain=[('is_it_client', '=', True), ('is_company', '=', True)])
    partner_id = fields.Many2one('res.partner', string='Partenaire', related='client_id', store=True, readonly=False, tracking=True,
                             help="Partenaire associé à l'incident (utilisé pour la compatibilité)")
    equipment_id = fields.Many2one('it.equipment', string='Équipement concerné', tracking=True)
    type_id = fields.Many2one('it.incident.type', string='Type d\'incident', tracking=True)
    priority = fields.Selection([
        ('0', 'Basse'),
        ('1', 'Normale'),
        ('2', 'Haute'),
        ('3', 'Urgente')
    ], string='Priorité', default='1', tracking=True)
    priority_id = fields.Many2one('it.incident.priority', string='Priorité (nouvelle)', tracking=True)
    tech_id = fields.Many2one('it.employee', string='Technicien assigné', tracking=True,
                           domain=[('is_it_technician', '=', True)])
    
    # Champs pour les rapporteurs d'incidents
    reporter_type_id = fields.Many2one('it.reporter.type', string='Type de rapporteur', tracking=True)
    is_new_reporter = fields.Boolean('Nouveau rapporteur', default=False)
    reporter_id = fields.Many2one('it.reporter', string='Rapporteur existant', tracking=True)
    reporter_name = fields.Char('Nom du nouveau rapporteur')
    
    # Champs pour la résolution
    resolution_note = fields.Text('Notes de résolution', tracking=True)
    resolution_date = fields.Datetime('Date de résolution', readonly=True)
    resolution_time = fields.Float('Temps de résolution (heures)', readonly=True)
    
    # Statistiques
    intervention_count = fields.Integer('Nombre d\'interventions', compute='_compute_intervention_count')
    
    # Notifications
    is_portal_created = fields.Boolean('Créé depuis le portail', default=False)
    notification_sent = fields.Boolean('Notification envoyée', default=False)
    
    # Champs SLA
    sla_policy_id = fields.Many2one('it.sla.policy', string='Politique SLA', tracking=True)
    sla_status_ids = fields.One2many('it.sla.status', 'incident_id', string='Statuts SLA')
    
    @api.depends()
    def _compute_intervention_count(self):
        for record in self:
            record.intervention_count = self.env['it.intervention'].search_count([
                ('incident_id', '=', record.id)
            ])
    
    def create_reporter(self):
        """Créer un nouveau rapporteur"""
        self.ensure_one()
        if not self.reporter_name or not self.reporter_type_id:
            raise ValidationError(_("Le nom du rapporteur et le type de rapporteur sont obligatoires."))
        
        reporter = self.env['it.reporter'].create({
            'name': self.reporter_name,
            'type_id': self.reporter_type_id.id,
            'partner_id': self.client_id.id,
        })
        
        self.write({
            'reporter_id': reporter.id,
            'is_new_reporter': False
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def _create_helpdesk_ticket(self):
        """Créer un ticket Helpdesk associé à l'incident"""
        try:
            use_helpdesk = self.env.company.use_helpdesk_for_incidents
        except Exception:
            _logger.warning("L'attribut 'use_helpdesk_for_incidents' n'existe pas sur la société. L'intégration Helpdesk est désactivée.")
            return
            
        if not self.helpdesk_ticket_id and use_helpdesk:
            try:
                # Trouver l'équipe Helpdesk appropriée
                team_id = False
                if self.env.company.default_helpdesk_team_id:
                    team_id = self.env.company.default_helpdesk_team_id.id
                
                if self.type_id and hasattr(self.type_id, 'helpdesk_team_id') and self.type_id.helpdesk_team_id:
                    team_id = self.type_id.helpdesk_team_id.id
                
                # Si aucune équipe n'est trouvée, chercher la première équipe disponible
                if not team_id:
                    team = self.env['helpdesk.team'].search([], limit=1)
                    if team:
                        team_id = team.id
                
                if not team_id:
                    return  # Pas d'équipe Helpdesk disponible
                
                # Créer le ticket Helpdesk
                ticket_vals = {
                    'name': self.name,
                    'description': self.description,
                    'partner_id': self.client_id.id,
                    'team_id': team_id,
                    'priority': '3' if self.priority == '3' else '1',
                    'user_id': False,  # Sera assigné automatiquement
                    'it_incident_id': self.id,
                }
                
                # Si un équipement est concerné, l'ajouter dans la description
                if self.equipment_id:
                    ticket_vals['description'] += f"\n\nÉquipement concerné: {self.equipment_id.name}"
                
                helpdesk_ticket = self.env['helpdesk.ticket'].sudo().create(ticket_vals)
                self.helpdesk_ticket_id = helpdesk_ticket.id
                
                _logger.info(f"Ticket Helpdesk créé: {helpdesk_ticket.name} (ID: {helpdesk_ticket.id}) pour l'incident {self.reference}")
            
            except Exception as e:
                _logger.error(f"Erreur lors de la création du ticket Helpdesk pour l'incident {self.reference}: {str(e)}")
    
    def write(self, values):
        # Mettre à jour les dates de changement d'état
        if values.get('state'):
            if values['state'] == 'assigned' and self.state != 'assigned':
                values['date_assigned'] = fields.Datetime.now()
            elif values['state'] == 'in_progress' and self.state != 'in_progress':
                values['date_start'] = fields.Datetime.now()
            elif values['state'] == 'resolved' and self.state != 'resolved':
                values['date_end'] = fields.Datetime.now()
                values['resolution_date'] = fields.Datetime.now()
                
                # Calculer le temps de résolution si nous avons une date de début
                if self.date_start:
                    start_dt = fields.Datetime.from_string(self.date_start)
                    end_dt = fields.Datetime.from_string(fields.Datetime.now())
                    delta = end_dt - start_dt
                    hours = delta.total_seconds() / 3600
                    values['resolution_time'] = hours
        
        return super(ITIncident, self).write(values)
    
    def assign_to_me(self):
        """Assigner l'incident à l'utilisateur courant"""
        current_employee = self.env['it.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('is_it_technician', '=', True)
        ], limit=1)
        
        if not current_employee:
            raise ValidationError(_("Vous devez être enregistré comme technicien IT pour vous assigner cet incident."))
        
        return self.write({
            'tech_id': current_employee.id,
            'state': 'assigned',
            'date_assigned': fields.Datetime.now()
        })
    
    def action_start(self):
        """Démarrer l'intervention"""
        self.write({
            'state': 'in_progress',
            'date_start': fields.Datetime.now()
        })
    
    def action_pause(self):
        """Mettre en pause l'incident"""
        self.write({
            'state': 'waiting'
        })
    
    def action_resolve(self):
        """Marquer l'incident comme résolu"""
        self.write({
            'state': 'resolved',
            'date_end': fields.Datetime.now()
        })
    
    def action_close(self):
        """Clôturer l'incident"""
        if not self.resolution_note:
            raise ValidationError(_("Veuillez ajouter une note de résolution avant de clôturer l'incident."))
        
        self.write({
            'state': 'closed'
        })
    
    def action_cancel(self):
        """Annuler l'incident"""
        self.write({
            'state': 'cancelled'
        }) 