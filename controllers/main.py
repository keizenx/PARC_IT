# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import logging

_logger = logging.getLogger(__name__)

class ITMainController(http.Controller):
    @http.route('/', type='http', auth="public", website=True)
    def index(self, **kw):
        return request.redirect('/my/home')
    
    @http.route('/contact', type='http', auth="public", website=True)
    def contact(self, **kw):
        return request.render("it__park.contact_us_page", {})

class ITSignup(AuthSignupHome):
    @http.route('/it/inscription', type='http', auth='public', website=True)
    def it_signup(self, **kw):
        qcontext = self.get_auth_signup_qcontext()
        qcontext['is_it_client'] = True  # Marquer comme inscription IT
        
        if request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Rediriger vers la page de connexion après l'inscription
                return request.redirect('/web/login')
            except Exception as e:
                qcontext['error'] = str(e)
        
        response = request.render('it__park.it_signup_form', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response 

class ITNotificationController(http.Controller):

    @http.route('/it_park/check_is_admin', type='json', auth="user")
    def check_is_admin(self):
        """Vérifie si l'utilisateur est un administrateur IT"""
        try:
            is_admin = False
            user = request.env.user
            
            # Vérifier si l'utilisateur est membre du groupe administrateur IT
            admin_group = request.env.ref('it__park.group_it_admin', raise_if_not_found=False)
            if admin_group and user in admin_group.users:
                is_admin = True
            
            # Vérifier si l'utilisateur est un administrateur système (fallback)
            if not is_admin and user.has_group('base.group_system'):
                is_admin = True
                
            return {
                'is_admin': is_admin
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la vérification des droits d'administrateur: {e}")
            return {
                'is_admin': False,
                'error': str(e)
            }
    
    @http.route('/it_park/check_pending_tickets', type='json', auth="user")
    def check_pending_tickets(self):
        """Vérifie s'il y a des tickets en attente de traitement"""
        try:
            # Compter les tickets en attente (nouveaux et non assignés)
            TicketObj = request.env['it.ticket'].sudo()
            pending_count = TicketObj.search_count([
                ('state', '=', 'new'),
                ('tech_id', '=', False)
            ])
            
            return {
                'pending_count': pending_count,
                'status': 'success'
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la vérification des tickets en attente: {e}")
            return {
                'pending_count': 0,
                'status': 'error',
                'error': str(e)
            } 