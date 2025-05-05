# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging
import base64

_logger = logging.getLogger(__name__)

class ITSupportWebsite(http.Controller):
    """Contrôleur pour la partie site web du module IT Park"""
    
    @http.route(['/it-support'], type='http', auth="user", website=True, csrf=True)
    def it_support_home(self, **kwargs):
        """Page d'accueil du support technique"""
        return request.render("it__park.it_support_home")
    
    @http.route(['/it-support/new-ticket'], type='http', auth="user", website=True, methods=['GET'], csrf=True)
    def it_support_new_ticket(self, **kwargs):
        """Page de création d'un nouveau ticket de support"""
        partner = request.env.user.partner_id
        
        # Obtenir le client IT (si l'utilisateur est un contact, utiliser sa société parente)
        client = partner
        if not partner.is_company and partner.parent_id and partner.parent_id.is_it_client:
            client = partner.parent_id
        
        # Récupérer les équipements du client
        equipment = request.env['it.equipment'].sudo().search([
            ('client_id', '=', client.id),
            ('state', 'in', ['installed', 'maintenance'])  # Seulement les équipements actifs
        ])
        
        # Récupérer les types d'incidents
        incident_types = request.env['it.incident.type'].sudo().search([])
        
        values = {
            'equipment': equipment,
            'incident_types': incident_types,
            'page_name': 'new_ticket',
        }
        
        return request.render("it__park.it_support_new_ticket", values)
    
    @http.route(['/it-support/submit-ticket'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def it_support_submit_ticket(self, **kwargs):
        """Traitement du formulaire de création de ticket"""
        partner = request.env.user.partner_id
        
        # Obtenir le client IT (si l'utilisateur est un contact, utiliser sa société parente)
        client = partner
        if not partner.is_company and partner.parent_id and partner.parent_id.is_it_client:
            client = partner.parent_id
        
        # Récupérer les champs du formulaire
        title = kwargs.get('title')
        description = kwargs.get('description')
        equipment_id = kwargs.get('equipment_id')
        other_equipment = kwargs.get('other_equipment')
        priority = kwargs.get('priority', '1')
        incident_type_id = kwargs.get('incident_type_id')
        attachment = kwargs.get('attachment')
        
        # Validation de base
        if not title or not description:
            return request.redirect('/it-support/new-ticket')
        
        # Créer l'incident
        vals = {
            'name': title,
            'description': description,
            'client_id': client.id,
            'date_reported': fields.Datetime.now(),
            'state': 'new',
            'priority': priority,
            'is_portal_created': True,  # Marquer comme créé depuis le portail web
        }
        
        # Rechercher ou créer un rapporteur lié au partenaire actuel
        ReporterType = request.env['it.reporter.type'].sudo()
        Reporter = request.env['it.reporter'].sudo()
        
        # Chercher un type de rapporteur "Client" ou créer un par défaut
        reporter_type = ReporterType.search([('code', '=', 'client')], limit=1)
        if not reporter_type:
            reporter_type = ReporterType.search([], limit=1)
        if not reporter_type:
            reporter_type = ReporterType.create({
                'name': 'Client',
                'code': 'client',
            })
        
        # Chercher un rapporteur existant pour ce partenaire
        reporter = Reporter.search([
            ('partner_id', '=', partner.id),
            ('type_id', '=', reporter_type.id)
        ], limit=1)
        
        # S'il n'existe pas, le créer
        if not reporter:
            reporter = Reporter.create({
                'name': partner.name,
                'type_id': reporter_type.id,
                'partner_id': partner.id,
            })
        
        # Ajouter le reporter_id au dictionnaire de valeurs
        vals['reporter_id'] = reporter.id
        
        # Ajouter les champs optionnels
        if equipment_id == 'other' and other_equipment:
            # Cas où l'utilisateur a choisi "Autre équipement" et a fourni une description
            vals['description'] = f"{description}\n\n**Équipement non listé**: {other_equipment}"
        elif equipment_id and equipment_id.isdigit():
            equipment = request.env['it.equipment'].sudo().browse(int(equipment_id))
            if equipment.exists() and equipment.client_id.id == client.id:
                vals['equipment_id'] = int(equipment_id)
        
        if incident_type_id and incident_type_id.isdigit():
            vals['type_id'] = int(incident_type_id)
        
        # Créer l'incident
        incident = request.env['it.incident'].sudo().create(vals)
        
        # Traiter la pièce jointe s'il y en a une
        if attachment and hasattr(attachment, 'filename') and attachment.filename:
            attachment_data = attachment.read()
            if attachment_data:
                attachment_vals = {
                    'name': attachment.filename,
                    'datas': base64.b64encode(attachment_data),
                    'res_model': 'it.incident',
                    'res_id': incident.id,
                }
                request.env['ir.attachment'].sudo().create(attachment_vals)
        
        # La méthode send_realtime_notification n'existe pas
        # incident.send_realtime_notification()
        
        # Rediriger vers la page de confirmation
        return request.render("it__park.it_support_ticket_submitted", {
            'ticket_reference': incident.reference,
            'ticket_id': incident.id,
        })
    
    @http.route(['/it-support/equipment-info'], type='json', auth="user", website=True, csrf=True)
    def get_equipment_info(self, equipment_id, **kwargs):
        """Récupérer les informations d'un équipement pour compléter le formulaire"""
        try:
            equipment_id = int(equipment_id)
            equipment = request.env['it.equipment'].sudo().browse(equipment_id)
            
            if not equipment.exists() or equipment.client_id.id != request.env.user.partner_id.id:
                return {'error': 'Équipement non trouvé'}
            
            return {
                'equipment': {
                    'id': equipment.id,
                    'name': equipment.name,
                    'type_id': equipment.type_id.read(['id', 'name']) if equipment.type_id else False,
                    'state': equipment.state,
                }
            }
            
        except Exception as e:
            _logger.error("Erreur lors de la récupération des informations de l'équipement: %s", str(e))
            return {'error': str(e)}
    
    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True, csrf=True)
    def my_tickets(self, page=1, state=None, search=None, **kwargs):
        """Liste des tickets de l'utilisateur connecté"""
        partner = request.env.user.partner_id
        
        # Obtenir le client IT (si l'utilisateur est un contact, utiliser sa société parente)
        client = partner
        if not partner.is_company and partner.parent_id:
            client = partner.parent_id
        
        # Construire le domaine
        domain = [('client_id', '=', client.id)]
        
        # Filtrer par état si spécifié
        if state:
            if state == 'open':
                domain.append(('state', 'in', ['new', 'assigned', 'in_progress', 'waiting']))
            elif state == 'resolved':
                domain.append(('state', 'in', ['resolved', 'closed']))
            else:
                domain.append(('state', '=', state))
        
        # Recherche
        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('description', 'ilike', search))
        
        # Récupérer les tickets
        Incident = request.env['it.incident'].sudo()
        tickets_count = Incident.search_count(domain)
        
        # Pagination
        page_size = 10
        pager = request.website.pager(
            url='/my/tickets',
            url_args={'state': state, 'search': search},
            total=tickets_count,
            page=page,
            step=page_size
        )
        
        # Récupérer les tickets pour la page courante
        tickets = Incident.search(domain, order='date_reported desc', limit=page_size, offset=pager['offset'])
        
        values = {
            'tickets': tickets,
            'pager': pager,
            'state': state,
            'search': search,
            'page_name': 'my_tickets',
        }
        
        return request.render("it__park.it_support_ticket_list", values)
    
    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="user", website=True, csrf=True)
    def my_ticket_detail(self, ticket_id, **kwargs):
        """Détail d'un ticket de support"""
        partner = request.env.user.partner_id
        
        # Obtenir le client IT (si l'utilisateur est un contact, utiliser sa société parente)
        client = partner
        if not partner.is_company and partner.parent_id:
            client = partner.parent_id
        
        # Récupérer le ticket
        ticket = request.env['it.incident'].sudo().browse(ticket_id)
        
        # Vérifier que le ticket appartient bien au client
        if not ticket.exists() or ticket.client_id.id != client.id:
            return request.redirect('/my/tickets')
        
        # Récupérer les statuts SLA
        sla_statuses = ticket.sla_status_ids
        
        # Préparer les pièces jointes
        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'it.incident'),
            ('res_id', '=', ticket.id)
        ])
        
        values = {
            'ticket': ticket,
            'sla_statuses': sla_statuses,
            'attachments': attachments,
            'page_name': 'ticket_detail',
        }
        
        return request.render("it__park.it_support_ticket_detail", values)
    
    @http.route(['/it-support/ticket-status'], type='json', auth="user", website=True, csrf=True)
    def get_ticket_status(self, ticket_id, **kwargs):
        """API pour récupérer l'état d'un ticket sans recharger la page"""
        try:
            ticket_id = int(ticket_id)
            ticket = request.env['it.incident'].sudo().browse(ticket_id)
            
            # Vérifier que le ticket appartient bien au client
            if not ticket.exists() or ticket.client_id.id != request.env.user.partner_id.commercial_partner_id.id:
                return {'error': 'Ticket non trouvé'}
            
            # État traduit
            state_labels = {
                'new': _('Nouveau'),
                'assigned': _('Assigné'),
                'in_progress': _('En cours'),
                'waiting': _('En attente'),
                'resolved': _('Résolu'),
                'closed': _('Clôturé'),
                'cancelled': _('Annulé'),
            }
            
            # Préparer la réponse
            return {
                'state': ticket.state,
                'state_label': state_labels.get(ticket.state, _('Inconnu')),
                'last_update': fields.Datetime.to_string(ticket.write_date),
                'resolution': ticket.resolution_note if ticket.state in ['resolved', 'closed'] else False,
            }
            
        except Exception as e:
            _logger.error("Erreur lors de la récupération de l'état du ticket: %s", str(e))
            return {'error': str(e)}
    
    @http.route(['/my/tickets/comment'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def ticket_add_comment(self, **kwargs):
        """Ajouter un commentaire à un ticket"""
        ticket_id = kwargs.get('ticket_id')
        message = kwargs.get('message')
        
        if not ticket_id or not message:
            return request.redirect('/my/tickets')
        
        try:
            ticket_id = int(ticket_id)
            ticket = request.env['it.incident'].sudo().browse(ticket_id)
            
            # Vérifier que le ticket appartient bien au client
            if not ticket.exists() or ticket.client_id.id != request.env.user.partner_id.commercial_partner_id.id:
                return request.redirect('/my/tickets')
            
            # Ajouter le commentaire
            ticket.message_post(
                body=f"<p><strong>Commentaire du client:</strong></p><p>{message}</p>",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=request.env.user.partner_id.id
            )
            
            # Traiter la pièce jointe s'il y en a une
            attachment = kwargs.get('attachment')
            if attachment and hasattr(attachment, 'filename') and attachment.filename:
                attachment_data = attachment.read()
                if attachment_data:
                    attachment_vals = {
                        'name': attachment.filename,
                        'datas': base64.b64encode(attachment_data),
                        'res_model': 'it.incident',
                        'res_id': ticket.id,
                    }
                    request.env['ir.attachment'].sudo().create(attachment_vals)
            
            # Rediriger vers le détail du ticket
            return request.redirect(f'/my/tickets/{ticket_id}')
            
        except Exception as e:
            _logger.error("Erreur lors de l'ajout d'un commentaire au ticket: %s", str(e))
            return request.redirect('/my/tickets')
    
    @http.route(['/it-park'], type='http', auth="public", website=True)
    def it_park_homepage(self, **kw):
        """Page d'accueil du module IT Park"""
        # Utiliser un nouveau nom de template pour éviter les conflits
        values = {
            'page_title': 'Gestion de parc informatique',
            'page_subtitle': 'Solution complète pour gérer vos équipements IT'
        }
        return request.render('it__park.it_park_homepage_simple', values)
        
    @http.route(['/my/create-incident'], type='http', auth="user", website=True)
    def create_incident(self, **kw):
        """Page de création d'un nouvel incident"""
        # Rediriger vers la nouvelle route de création de tickets
        return request.redirect('/my/tickets/add')
            
    @http.route(['/services-it'], type='http', auth="public", website=True)
    def services_it(self, **kw):
        """Page présentant les services IT offerts"""
        return request.render("it__park.services_it", {
            'page_name': 'services_it',
        })
        
    @http.route(['/services-it/catalogue'], type='http', auth="public", website=True)
    def services_it_catalogue(self, **kw):
        """Catalogue détaillé des services IT offerts"""
        return request.render("it__park.services_it_catalogue", {
            'page_name': 'services_it_catalogue',
        }) 