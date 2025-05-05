# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    # Champ pour lier le ticket Helpdesk à un incident IT
    it_incident_id = fields.Many2one('it.incident', string='Incident IT associé', readonly=True)
    
    # Champs informatifs
    equipment_id = fields.Many2one('it.equipment', string='Équipement', readonly=True)
    sla_deadline = fields.Datetime(string='Échéance SLA', readonly=True)
    sla_reached_date = fields.Datetime(string='Date atteinte SLA', readonly=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge pour créer automatiquement un incident IT si ce n'est pas déjà le cas"""
        tickets = super(HelpdeskTicket, self).create(vals_list)
        
        # Pour chaque ticket créé sans référence à un incident IT, créer un incident
        for ticket in tickets.filtered(lambda t: not t.it_incident_id and t.team_id.is_it_team):
            try:
                # Créer l'incident IT
                incident_vals = {
                    'name': ticket.name,
                    'description': ticket.description or '',
                    'client_id': ticket.partner_id.id if ticket.partner_id else self.env.user.partner_id.id,
                    'reporter_id': self.env.user.partner_id.id,
                    'date_reported': fields.Datetime.now(),
                    'state': 'new',
                }
                
                # Trouver le type d'incident approprié
                if ticket.ticket_type_id:
                    incident_type = self.env['it.incident.type'].search([
                        ('name', 'ilike', ticket.ticket_type_id.name)
                    ], limit=1)
                    if incident_type:
                        incident_vals['type_id'] = incident_type.id
                
                # Trouver la priorité appropriée
                if ticket.priority:
                    # Convertir la priorité Helpdesk (0-3) en priorité IT
                    high_priority = self.env['it.incident.priority'].search([
                        ('high_priority', '=', True)
                    ], limit=1)
                    medium_priority = self.env['it.incident.priority'].search([
                        ('sequence', '>', 0),
                        ('high_priority', '=', False)
                    ], limit=1, order='sequence')
                    low_priority = self.env['it.incident.priority'].search([
                        ('high_priority', '=', False)
                    ], limit=1, order='sequence')
                    
                    if int(ticket.priority) >= 3 and high_priority:
                        incident_vals['priority_id'] = high_priority.id
                    elif int(ticket.priority) >= 1 and medium_priority:
                        incident_vals['priority_id'] = medium_priority.id
                    elif low_priority:
                        incident_vals['priority_id'] = low_priority.id
                
                # Créer l'incident
                incident = self.env['it.incident'].sudo().create(incident_vals)
                
                # Lier le ticket à l'incident
                ticket.write({
                    'it_incident_id': incident.id
                })
                
                # Ajouter un message dans le chatter
                incident.message_post(
                    body=_("Incident créé automatiquement depuis le ticket Helpdesk #%s") % ticket.id,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
                
                ticket.message_post(
                    body=_("Ticket lié à l'incident IT #%s") % incident.reference,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
            
            except Exception as e:
                # Log l'erreur mais ne bloque pas la création du ticket
                ticket.message_post(
                    body=_("Erreur lors de la création de l'incident IT: %s") % str(e),
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
        
        return tickets
    
    def write(self, vals):
        """Surcharge pour synchroniser les mises à jour entre les tickets et les incidents"""
        result = super(HelpdeskTicket, self).write(vals)
        
        # Synchroniser les modifications clés avec l'incident IT
        for ticket in self.filtered(lambda t: t.it_incident_id):
            incident_vals = {}
            
            # Synchroniser le nom
            if vals.get('name'):
                incident_vals['name'] = vals['name']
            
            # Synchroniser la description
            if vals.get('description'):
                incident_vals['description'] = vals['description']
            
            # Synchroniser le statut
            if vals.get('stage_id'):
                stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
                # Mapper les étapes Helpdesk vers les états des incidents
                if stage.is_close:
                    incident_vals['state'] = 'resolved'
                elif stage.name.lower() in ('new', 'nouveau'):
                    incident_vals['state'] = 'new'
                elif stage.name.lower() in ('in progress', 'en cours'):
                    incident_vals['state'] = 'in_progress'
                elif stage.name.lower() in ('waiting', 'en attente'):
                    incident_vals['state'] = 'waiting'
            
            # Mettre à jour l'incident si nécessaire
            if incident_vals:
                ticket.it_incident_id.write(incident_vals)
        
        return result
    
    def action_view_it_incident(self):
        """Action pour voir l'incident IT lié"""
        self.ensure_one()
        
        if not self.it_incident_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aucun incident associé'),
                    'message': _('Ce ticket n\'est pas lié à un incident IT.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        return {
            'name': _('Incident IT'),
            'type': 'ir.actions.act_window',
            'res_model': 'it.incident',
            'res_id': self.it_incident_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'
    
    is_it_team = fields.Boolean('Équipe IT', 
        help="Cette équipe est dédiée au support IT et sera liée au module IT Park")
    
    # Relation avec les types d'incidents
    incident_type_ids = fields.Many2many('it.incident.type', 'helpdesk_team_incident_type_rel',
                                        'team_id', 'type_id', string='Types d\'incidents gérés') 