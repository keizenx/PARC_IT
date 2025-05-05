# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR, AND
from collections import OrderedDict
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.tools import format_datetime, format_date
import base64
import logging

_logger = logging.getLogger(__name__)

class ITPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        if 'it_incident_count' in counters:
            it_incident_count = request.env['it.incident'].search_count([
                ('partner_id', '=', partner.id)
            ]) if request.env['it.incident'].check_access_rights('read', raise_exception=False) else 0
            values['it_incident_count'] = it_incident_count
            
        if 'it_ticket_count' in counters:
            it_ticket_count = request.env['it.ticket'].search_count([
                ('partner_id', '=', partner.id)
            ]) if request.env['it.ticket'].check_access_rights('read', raise_exception=False) else 0
            values['it_ticket_count'] = it_ticket_count
            
        if 'it_equipment_count' in counters:
            it_equipment_count = request.env['it.equipment'].search_count([
                ('assigned_to', '=', partner.id)
            ]) if request.env['it.equipment'].check_access_rights('read', raise_exception=False) else 0
            values['it_equipment_count'] = it_equipment_count
            
        if 'it_contract_count' in counters:
            it_contract_count = request.env['it.contract'].search_count([
                ('partner_id', '=', partner.id)
            ]) if request.env['it.contract'].check_access_rights('read', raise_exception=False) else 0
            values['it_contract_count'] = it_contract_count
            
        if 'ticket_count' in counters:
            values['ticket_count'] = request.env['it.incident'].search_count([
                ('client_id', '=', partner.id)
            ]) if request.env['it.incident'].check_access_rights('read', raise_exception=False) else 0

        if 'equipment_count' in counters:
            values['equipment_count'] = request.env['it.equipment'].search_count([
                ('client_id', '=', partner.id)
            ]) if request.env['it.equipment'].check_access_rights('read', raise_exception=False) else 0

        return values

    @http.route(['/my/incidents', '/my/incidents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_incidents(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        IncidentSudo = request.env['it.incident'].sudo()

        domain = [
            ('client_id', '=', partner.commercial_partner_id.id)
        ]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_reported desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'new': {'label': _('New'), 'domain': [('state', '=', 'new')]},
            'in_progress': {'label': _('In Progress'), 'domain': [('state', '=', 'in_progress')]},
            'resolved': {'label': _('Resolved'), 'domain': [('state', '=', 'resolved')]},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        incident_count = IncidentSudo.search_count(domain)

        # make pager
        pager = portal_pager(
            url="/my/incidents",
            url_args={'sortby': sortby, 'filterby': filterby},
            total=incident_count,
            page=page,
            step=self._items_per_page
        )

        # search the count to display, according to the pager data
        incidents = IncidentSudo.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            'incidents': incidents,
            'page_name': 'incidents',
            'pager': pager,
            'default_url': '/my/incidents',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
        })
        return request.render("it__park.portal_my_incidents", values)

    @http.route(['/my/incidents/<int:incident_id>'], type='http', auth="user", website=True)
    def portal_incident_detail(self, incident_id, **kw):
        try:
            incident_sudo = self._document_check_access('it.incident', incident_id)
        except (AccessError, MissingError):
            return request.redirect('/my/incidents')

        values = {
            'incident': incident_sudo,
            'page_name': 'incident',
        }
        return request.render("it__park.portal_incident_detail", values)

    @http.route(['/my/ticket/<int:ticket_id>/follow'], type='http', auth="user", website=True, csrf=True)
    def ticket_follow(self, ticket_id, **kw):
        """Permet au client de suivre un ticket en particulier"""
        incident = request.env['it.incident'].sudo().browse(ticket_id)
        partner = request.env.user.partner_id
        
        # Vérifier que le ticket appartient bien au client connecté
        if not incident.exists() or incident.client_id.id != partner.id:
            return request.redirect('/my/incidents')
            
        # Ajouter le partenaire comme follower du ticket
        incident.message_subscribe(partner_ids=[partner.id])
        
        return request.redirect('/my/incidents/%s' % ticket_id)

    @http.route(['/my/incidents/comment'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_incident_comment(self, **post):
        """Traitement du formulaire d'ajout de commentaire à un incident"""
        incident_id = int(post.get('incident_id', 0))
        message = post.get('message', '')
        partner = request.env.user.partner_id
        
        if not incident_id or not message:
            return request.redirect('/my/incidents')
            
        incident = request.env['it.incident'].sudo().browse(incident_id)
        
        # Vérifier que l'incident appartient bien au client
        if not incident.exists() or incident.client_id != partner.commercial_partner_id:
            return request.redirect('/my/incidents')
            
        # Ajouter le message
        body = f"<p><strong>Commentaire du client</strong></p><p>{message}</p>"
        incident.sudo().message_post(
            body=body,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            author_id=partner.id
        )
        
        return request.redirect(f'/my/incidents/{incident.id}')

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        TicketObj = request.env['it.ticket']
        
        domain = [('partner_id', '=', partner.id)]
        
        # Filtres et tri
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'priority': {'label': _('Priority'), 'order': 'priority desc'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
        }
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('Open'), 'domain': [('stage_id.is_closed', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('stage_id.is_closed', '=', True)]},
        }
        
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # count for pager
        ticket_count = TicketObj.search_count(domain)
        
        # make pager
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=ticket_count,
            page=page,
            step=self._items_per_page
        )
        
        # search the records to display
        tickets = TicketObj.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        
        values.update({
            'tickets': tickets,
            'page_name': 'tickets',
            'pager': pager,
            'default_url': '/my/tickets',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
        })
        
        return request.render("it__park.portal_my_tickets", values)
    
    @http.route(['/my/tickets/add'], type='http', auth="user", website=True)
    def portal_create_ticket(self, **kw):
        values = self._prepare_portal_layout_values()
        
        # Catégories disponibles
        categories = request.env['it.ticket.category'].search([])
        
        values.update({
            'page_name': 'create_ticket',
            'categories': categories,
        })
        
        return request.render("it__park.portal_create_ticket", values)
    
    @http.route(['/my/tickets/submit'], type='http', auth="user", website=True)
    def portal_submit_ticket(self, **post):
        partner = request.env.user.partner_id
        
        # Création du ticket
        vals = {
            'name': post.get('name'),
            'description': post.get('description'),
            'partner_id': partner.id,
            'email': partner.email,
            'phone': partner.phone,
            'priority': post.get('priority'),
        }
        
        if post.get('category_id'):
            vals['category_id'] = int(post.get('category_id'))
        
        # Gestion du fichier joint
        attachment = post.get('attachment')
        if attachment:
            vals['attachment_ids'] = [(0, 0, {
                'name': attachment.filename,
                'datas': attachment.read(),
                'res_model': 'it.ticket',
            })]
        
        # Création effective du ticket
        ticket = request.env['it.ticket'].sudo().create(vals)
        
        return request.redirect('/my/tickets/thankyou/%s' % ticket.id)
    
    @http.route(['/my/tickets/thankyou/<int:ticket_id>'], type='http', auth="user", website=True)
    def portal_ticket_thankyou(self, ticket_id, **kw):
        ticket = request.env['it.ticket'].browse(ticket_id)
        values = {'ticket': ticket}
        return request.render("it__park.portal_ticket_thankyou", values)
    
    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="user", website=True)
    def portal_ticket_detail(self, ticket_id, **kw):
        ticket = request.env['it.ticket'].browse(ticket_id)
        
        # Vérification des droits d'accès
        if ticket.partner_id != request.env.user.partner_id:
            return request.redirect('/my/tickets')
        
        values = self._prepare_portal_layout_values()
        values.update({
            'ticket': ticket,
            'page_name': 'ticket_detail',
        })
        
        return request.render("it__park.portal_ticket_detail", values)
    
    @http.route(['/my/tickets/<int:ticket_id>/comment'], type='http', auth="user", website=True)
    def portal_ticket_comment(self, ticket_id, **post):
        ticket = request.env['it.ticket'].browse(ticket_id)
        
        # Vérification des droits d'accès
        if ticket.partner_id != request.env.user.partner_id:
            return request.redirect('/my/tickets')
        
        if post.get('comment'):
            ticket.message_post(
                body=post.get('comment'),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
        
        return request.redirect('/my/tickets/%s' % ticket_id)

    @http.route(['/my/equipment', '/my/equipment/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipment(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
        return request.render("it__park.portal_my_equipment", {
            'page_name': 'equipment',
        })

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contracts(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
        return request.render("it__park.portal_my_contracts", {
            'page_name': 'contracts',
        }) 