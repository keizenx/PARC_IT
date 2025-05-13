# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
import logging
import base64
from odoo.addons.website.controllers.main import Website
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

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

class WebsiteIT(Website):

    @http.route(['/register'], type='http', auth="public", website=True)
    def register_redirect(self, **post):
        return request.redirect('/it/inscription')
        
    @http.route(['/it/inscription'], type='http', auth="public", website=True)
    def it_registration(self, **post):
        return request.render('it__park.it_registration_simple', {})

    @http.route(['/it/validate-email'], type='http', auth="public", website=True)
    def validate_email(self, **post):
        """Validation de l'adresse email du client"""
        token = post.get('token')
        partner_id = post.get('partner_id')
        
        _logger.info(f"Tentative de validation d'email - Token: {token}, Partner ID: {partner_id}")
        
        error_template = 'it__park.email_validation_error'
        success_template = 'it__park.email_validation_success'
        
        if not token or not partner_id:
            _logger.warning("Validation d'email échouée: token ou partner_id manquant")
            return request.render(error_template, {
                'error': 'Lien de validation invalide. Veuillez vérifier que vous utilisez le lien complet reçu par email.',
                'show_contact': True
            })
        
        try:
            partner_id = int(partner_id)
            partner = request.env['res.partner'].sudo().browse(partner_id)
            
            if not partner.exists():
                _logger.warning(f"Partenaire ID {partner_id} introuvable")
                return request.render(error_template, {
                    'error': 'Client introuvable. Veuillez vous réinscrire ou contacter le support.',
                    'show_contact': True
                })
            
            # Simple vérification du token et activation du compte
            if token and partner.email_validation_token and token == partner.email_validation_token:
                # Activer le compte simplement
                partner.sudo().write({
                    'email_validated': True,
                    'email_validation_token': False,
                    'email_validation_expiration': False
                })
                
                # Activer le client IT
                if partner.is_it_client_pending:
                    partner.sudo().write({
            'is_it_client': True,
                        'is_it_client_pending': False
                    })
                
                # Notifier les administrateurs (optionnel)
                try:
                    self._notify_admin_email_validated(partner)
                except Exception as e:
                    _logger.error(f"Erreur de notification (non bloquante): {str(e)}")
                
                return request.render(success_template, {
                    'partner': partner,
                    'already_validated': False
                })
            else:
                _logger.warning(f"Token invalide pour {partner.name}")
                return request.render(error_template, {
                    'error': 'Le lien de validation est invalide ou a expiré. Veuillez vous réinscrire ou contacter le support.',
                    'show_contact': True
                })
                
        except Exception as e:
            _logger.error(f"Erreur lors de la validation de l'email: {str(e)}", exc_info=True)
            return request.render(error_template, {
                'error': 'Une erreur est survenue lors de la validation. Veuillez réessayer ou contacter le support.',
                'show_contact': True
            })

    def _regenerate_validation_email(self, partner):
        """Régénère un token et renvoie l'email de validation"""
        import uuid
        import datetime
        
        token = str(uuid.uuid4())
        expiration = datetime.datetime.now() + datetime.timedelta(days=1)
        
        # Mettre à jour le token
        partner.sudo().write({
            'email_validation_token': token,
            'email_validation_expiration': expiration,
        })
        
        # Générer l'URL de validation
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        validation_url = f"{base_url}/it/validate-email?token={token}&partner_id={partner.id}"
        
        # Envoyer l'email
        mail_values = {
            'subject': 'IT Park - Nouveau lien de validation de votre email',
            'body_html': self._get_validation_email_template(partner.name, validation_url),
            'email_to': partner.email,
            'email_from': request.env.company.email or 'noreply@example.com',
            'auto_delete': True,
        }
        
        mail = request.env['mail.mail'].sudo().create(mail_values)
        mail.send(raise_exception=True)

    def _notify_admin_email_validated(self, partner):
        """Notifie les administrateurs qu'un email a été validé"""
        admin_group = request.env.ref('base.group_system')
        admin_partners = admin_group.users.mapped('partner_id')
        
        if admin_partners:
            message = f"""
                <p>Un nouveau client a validé son adresse email :</p>
                <ul>
                    <li><strong>Nom :</strong> {partner.name}</li>
                    <li><strong>Email :</strong> {partner.email}</li>
                    <li><strong>Date de validation :</strong> {fields.Datetime.now()}</li>
                </ul>
                <p>Le compte est maintenant en attente d'approbation.</p>
            """
            
            mail_values = {
                'subject': f'IT Park - Nouvelle validation email : {partner.name}',
                'body_html': message,
                'email_to': ','.join(admin_partners.mapped('email')),
                'email_from': request.env.company.email or 'noreply@example.com',
                'auto_delete': True,
            }
            
            try:
                mail = request.env['mail.mail'].sudo().create(mail_values)
                mail.send()
            except Exception as e:
                _logger.error("Erreur lors de la notification des administrateurs: %s", str(e))

    def _get_validation_email_template(self, client_name, validation_url):
        """Génère le contenu HTML de l'email de validation"""
        return f"""
        <div style="margin: 0px; padding: 0px; background-color: #f2f2f2;">
            <table style="width:100%; max-width: 600px; margin: 0 auto; background-color: white; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; font-family: Arial, sans-serif;">
                <tr>
                    <td style="padding: 30px 40px; background-color: #3f4185; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">Validation de votre compte IT Park</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 40px;">
                        <p style="margin-top: 0; font-size: 16px; color: #333333;">
                            Bonjour <strong>{client_name}</strong>,
                        </p>
                        <p style="font-size: 16px; color: #333333; line-height: 1.5;">
                            Nous vous remercions pour votre inscription à notre plateforme de gestion de parc informatique.
                            Pour finaliser votre inscription et activer votre compte, veuillez cliquer sur le bouton ci-dessous.
                            Ce lien est valable pendant 24 heures.
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{validation_url}" style="display: inline-block; padding: 14px 30px; background-color: #3f4185; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                                Valider mon adresse email
                            </a>
                        </div>
                        <p style="font-size: 14px; color: #666666;">
                            Si le bouton ne fonctionne pas, vous pouvez copier et coller le lien suivant dans votre navigateur :
                        </p>
                        <p style="font-size: 14px; color: #666666; word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
                            {validation_url}
                        </p>
                        <p style="font-size: 14px; color: #666666; margin-top: 30px;">
                            <strong>Important :</strong><br>
                            - Ce lien est valable pendant 24 heures<br>
                            - Si vous n'avez pas fait cette demande, vous pouvez ignorer cet email<br>
                            - Une fois votre email validé, votre compte sera examiné par notre équipe
                        </p>
                        <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 30px 0;">
                        <p style="font-size: 12px; color: #999999; text-align: center;">
                            Cet email a été envoyé automatiquement, merci de ne pas y répondre.<br>
                            Pour toute question, contactez notre support.
                        </p>
                    </td>
                </tr>
            </table>
        </div>
        """

    def _notify_admin_new_registration(self, partner, post):
        """Notifie les administrateurs d'une nouvelle inscription"""
        try:
            internal_users = request.env['res.users'].sudo().search([
                ('groups_id', 'in', request.env.ref('base.group_system').id)
            ])
            
            if internal_users:
                partner_url = f"/web#id={partner.id}&model=res.partner&view_type=form"
                body = f"""
                <p>Un nouveau client IT s'est inscrit :</p>
                <ul>
                    <li><strong>Nom :</strong> {partner.name}</li>
                    <li><strong>Email :</strong> {partner.email}</li>
                    <li><strong>Téléphone :</strong> {post.get('phone') or 'Non renseigné'}</li>
                </ul>
                <p><strong>Statut :</strong> Un email de validation a été envoyé au client.</p>
                <p>
                    <a href="{partner_url}" style="padding: 8px 16px; background-color: #875A7B; color: #FFF; border-radius: 5px; text-decoration: none;">
                        Consulter le profil client
                    </a>
                </p>
                """
                
                for user in internal_users:
                    request.env['mail.message'].sudo().create({
                        'subject': f"Nouvelle inscription client IT : {partner.name}",
                        'body': body,
                        'author_id': request.env.ref('base.partner_root').id,
                        'model': 'res.partner',
                        'res_id': partner.id,
                        'message_type': 'notification',
                        'partner_ids': [(4, user.partner_id.id)],
                        'notification_ids': [(0, 0, {
                            'res_partner_id': user.partner_id.id,
                            'notification_type': 'inbox'
                        })]
                    })
        except Exception as e:
            _logger.error("Erreur lors de la notification interne: %s", str(e))

    @http.route(['/it/inscription/submit'], type='http', auth="public", website=True)
    def it_registration_submit(self, **post):
        # Validation des champs requis
        _logger.info("Soumission du formulaire d'inscription IT")
        
        if not post.get('name') or not post.get('email'):
            _logger.warning("Formulaire d'inscription incomplet: nom ou email manquant")
            return request.render('it__park.it_registration_error', {
                'error_message': 'Le nom de l\'entreprise et l\'email sont obligatoires.'
            })
            
        # Validation du mot de passe
        password = post.get('password')
        confirm_password = post.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                _logger.warning("Les mots de passe ne correspondent pas")
                return request.render('it__park.it_registration_error', {
                    'error_message': 'Les mots de passe ne correspondent pas.'
                })
            
            if len(password) < 8:
                _logger.warning("Mot de passe trop court")
                return request.render('it__park.it_registration_error', {
                    'error_message': 'Le mot de passe doit contenir au moins 8 caractères.'
                })

        values = {
            'name': post.get('name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'street': post.get('street'),
            'city': post.get('city'),
            'zip': post.get('zip'),
            'is_company': True,
            'is_it_client': False,  # Ne pas activer directement
            'is_it_client_pending': True,  # Mettre en attente
            'is_it_client_approved': False,  # Par défaut, le client n'est pas approuvé
            'company_type': 'company',
            'email_validated': False,  # Email pas encore validé
        }
        
        # Recherche de la catégorie "Client IT" et l'associe au partenaire
        category_id = request.env['res.partner.category'].sudo().search([('name', '=', 'Client IT')], limit=1)
        if not category_id:
            category_id = request.env['res.partner.category'].sudo().create({'name': 'Client IT'})
        
        values['category_id'] = [(4, category_id.id)]
        
        try:
            # Vérifier si un partenaire avec cet email existe déjà
            existing_partner = request.env['res.partner'].sudo().search([('email', '=', post.get('email'))], limit=1)
            if existing_partner:
                # S'assurer que les champs requis ne sont pas vides
                _logger.info(f"Partenaire existant trouvé: {existing_partner.name}, ID: {existing_partner.id}")
                update_values = {k: v for k, v in values.items() if v is not None}
                # Conserver le nom existant si aucun nouveau nom n'est fourni
                if not update_values.get('name'):
                    update_values['name'] = existing_partner.name
                partner = existing_partner
                partner.sudo().write(update_values)
            else:
                _logger.info(f"Création d'un nouveau partenaire: {values['name']}")
                partner = request.env['res.partner'].sudo().create(values)

            # Variables par défaut pour le template de confirmation
            confirmation_values = {
                'company_name': partner.name,  # Utiliser le nom du partenaire
                'email': partner.email,
                'validation_url': None,
                'show_validation_link': False,  # Ne pas afficher le lien directement
                'email_sent': False
            }

            if partner and partner.email:  # Utiliser l'email du partenaire
                try:
                    # Vérifier si un utilisateur existe déjà
                    existing_user = request.env['res.users'].sudo().search([('login', '=', partner.email)], limit=1)
                    
                    if existing_user:
                        # Réactiver l'utilisateur s'il était archivé
                        if not existing_user.active:
                            _logger.info(f"Réactivation de l'utilisateur existant: {existing_user.login}")
                            existing_user.sudo().write({
                                'active': True,
                                'partner_id': partner.id,
                            })
                        user = existing_user
                        
                        # Mettre à jour le mot de passe si fourni
                        if password:
                            user.sudo().write({
                                'password': password
                            })
                    else:
                        # Créer un nouvel utilisateur
                        _logger.info(f"Création d'un nouvel utilisateur pour le partenaire: {partner.email}")
                        user_values = {
                            'name': partner.name,
                            'login': partner.email,
                            'email': partner.email,
                            'partner_id': partner.id,
                            'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
                            'active': True,
                        }
                        
                        # Ajouter le mot de passe si fourni
                        if password:
                            user_values['password'] = password
                            
                        user = request.env['res.users'].sudo().create(user_values)

                    # Générer un token et construire l'URL de validation
                    import uuid
                    import datetime
                    token = str(uuid.uuid4())
                    
                    # Stocker le token avec un logging explicite
                    expiration = datetime.datetime.now() + datetime.timedelta(days=1)
                    _logger.info(f"Génération du token de validation pour {partner.name}, expiration: {expiration}")
                    _logger.info(f"Token généré: {token}")
                    
                    partner.sudo().write({
                        'email_validation_token': token,
                        'email_validation_expiration': expiration,
                    })
                    
                    # Vérifier que le token a bien été sauvegardé
                    partner_refreshed = request.env['res.partner'].sudo().browse(partner.id)
                    _logger.info(f"Token sauvegardé dans la BD: {partner_refreshed.email_validation_token == token}")

                    # Créer l'URL de validation
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    validation_url = f"{base_url}/it/validate-email?token={token}&partner_id={partner.id}"
                    _logger.info(f"URL de validation générée: {validation_url}")

                    # Envoyer l'email de validation
                    try:
                        mail_values = {
                            'subject': 'IT Park - Confirmez votre adresse email',
                            'body_html': self._get_validation_email_template(partner.name, validation_url),
                            'email_to': partner.email,
                            'email_from': request.env.company.email or 'noreply@example.com',
                            'auto_delete': True,
                        }
                        
                        # Vérifier la configuration SMTP
                        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
                        if not mail_server:
                            _logger.warning("Aucun serveur SMTP n'est configuré dans le système. Tentative d'envoi sans serveur spécifique.")
                            
                        mail = request.env['mail.mail'].sudo().create(mail_values)
                        
                        # Forcer l'utilisation du serveur SMTP si trouvé
                        if mail_server:
                            mail.mail_server_id = mail_server.id
                        
                        # Envoyer avec plus de détails de logging
                        _logger.info(f"Tentative d'envoi de l'email à {partner.email}")
                        mail.send(raise_exception=True)
                        _logger.info(f"Email de validation envoyé avec succès à {partner.email}")
                        confirmation_values['email_sent'] = True
                    except Exception as e:
                        _logger.error(f"Erreur détaillée lors de l'envoi de l'email: {str(e)}")
                        confirmation_values['email_sent'] = False
                        confirmation_values['error_message'] = f"Erreur d'envoi d'email: {str(e)}"

                    # Mettre à jour l'URL dans l'objet partenaire pour référence future
                    partner.sudo().write({'email_validation_url': validation_url})
                    
                    # Envoyer une invitation Odoo officielle
                    self._send_odoo_invitation(partner, user)
                    
                    # Notifier l'administrateur
                    self._notify_admin_new_registration(partner, post)

                except Exception as e:
                    _logger.error(f"Erreur lors de la création/mise à jour de l'utilisateur: {str(e)}", exc_info=True)
                    confirmation_values['error_message'] = str(e)

            return request.render('it__park.it_registration_confirmation', confirmation_values)

        except Exception as e:
            _logger.error(f"Erreur lors de l'inscription: {str(e)}", exc_info=True)
            return request.render('it__park.it_registration_error', {
                'error_message': str(e)
        })

    def _send_odoo_invitation(self, partner, user):
        """Envoie une invitation officielle Odoo similaire à celle du système standard"""
        try:
            company = request.env.company
            IrConfigParameter = request.env['ir.config_parameter'].sudo()
            base_url = IrConfigParameter.get_param('web.base.url')
            
            # Générer un token d'invitation (valide 6 jours comme indiqué dans l'exemple)
            invitation_token = user.sudo()._create_signup_token()
            
            # URL d'invitation avec token
            signup_url = f"{base_url}/web/signup?token={invitation_token}"
            
            # Préparer l'email
            subject = f"Welcome to Odoo"
            
            # Récupérer les paramètres nécessaires
            catchall_domain = IrConfigParameter.get_param('mail.catchall.domain')
            default_from = IrConfigParameter.get_param('mail.default.from')
            
            # Construire l'adresse d'expéditeur
            if default_from:
                email_from = default_from
            elif catchall_domain:
                email_from = f"{company.name} <noreply@{catchall_domain}>"
            else:
                email_from = f"{company.name} <{company.email or 'noreply@example.com'}>"
            
            # Définir le message qui sera affiché en fonction de si un mot de passe a été défini
            if hasattr(user, 'password') and user.password:
                user_password_message = """
                <p>Vous avez défini votre propre mot de passe lors de l'inscription. Vous pouvez l'utiliser pour vous connecter à votre compte.</p>
                <p>Votre identifiant : <strong>{email}</strong></p>
                <p>Votre mot de passe : celui que vous avez défini lors de l'inscription</p>
                """
            else:
                user_password_message = """
                <p>Vous devez définir votre mot de passe en utilisant le lien ci-dessous:</p>
                """
            
            # Corps HTML du mail
            body_html = f"""
            <div style="margin: 0px; padding: 0px; background-color: #f2f2f2;">
                <table style="width: 600px; margin: 0 auto; background-color: white; border-collapse: separate;">
                    <tr>
                        <td style="padding: 20px;">
                            <p>Dear {partner.name},</p>
                            <p>You have been invited by {request.env.user.name} of {company.name} to connect on Odoo.</p>
                            {user_password_message.format(email=partner.email)}
                            <div style="margin: 16px 0px 16px 0px; text-align: center;">
                                <a href="{signup_url}" 
                                   style="padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#875A7B; text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400; text-align: center; vertical-align: middle; cursor: pointer; background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px">
                                    Accept invitation
                                </a>
                            </div>
                            <p>This link will remain valid during 6 days</p>
                            <p>Your Odoo domain is: {base_url}</p>
                            <p>Your sign in email is: {partner.email}</p>
                            <br/>
                            <p>Never heard of Odoo? It's an all-in-one business software loved by 7+ million users. It will considerably improve your experience at work and increase your productivity.</p>
                            <p>Have a look at the <a href="https://www.odoo.com/documentation/user">Odoo Tour</a> to discover the tool.</p>
                            <p>Enjoy Odoo!</p>
                            <br/>
                            <p>--<br/>
                            The {company.name} Team<br/>
                            {company.name}<br/>
                            {company.phone or ''} | {company.email or ''} | {company.website or ''}</p>
                            <p style="color: #aaaaaa;">Powered by <a href="https://www.odoo.com">Odoo</a></p>
                        </td>
                    </tr>
                </table>
            </div>
            """
            
            # Envoyer l'email
            mail_values = {
                'subject': subject,
                'body_html': body_html,
                'email_to': partner.email,
                'email_from': email_from,
                'auto_delete': True,
            }
            
            # Récupérer les serveurs de messagerie configurés dans Odoo
            mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
            
            # Si un serveur est trouvé, créer et envoyer l'email
            if mail_server:
                mail = request.env['mail.mail'].sudo().create(mail_values)
                mail.mail_server_id = mail_server.id
                mail.send(raise_exception=False)
                _logger.info(f"Email d'invitation Odoo envoyé à {partner.email}")
                return True
            else:
                # Utiliser l'email API d'Odoo qui gère les paramètres mail.* automatiquement
                template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                if template:
                    template.sudo().with_context(
                        lang=partner.lang,
                        auth_login=partner.email,
                        name=partner.name,
                        signup_url=signup_url,
                        database=request.env.cr.dbname,
                    ).send_mail(
                        user.id, 
                        force_send=True, 
                        email_values={'email_to': partner.email}
                    )
                    _logger.info(f"Email d'invitation Odoo envoyé à {partner.email} via template")
                    return True
                else:
                    # Dernier recours: utiliser le système mail standard
                    mail_values['mail_server_id'] = mail_server.id if mail_server else None
                    mail = request.env['mail.mail'].sudo().create(mail_values)
                    mail.send(raise_exception=False)
                    _logger.info(f"Email d'invitation Odoo envoyé à {partner.email} (méthode alternative)")
                    return True
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de l'email d'invitation Odoo: {str(e)}", exc_info=True)
            return False

class AuthSignupITPark(AuthSignupHome):
    
    def _prepare_signup_values(self, qcontext):
        values = super(AuthSignupITPark, self)._prepare_signup_values(qcontext)
        if qcontext.get('is_it_client'):
            values['is_it_client'] = True
            values['is_it_client_approved'] = False  # Les nouveaux comptes ne sont pas approuvés par défaut
            values['is_company'] = True
            values['company_type'] = 'company'
        return values

    @http.route()
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        
        # Ajouter le champ is_it_client au contexte
        qcontext['is_it_client'] = kw.get('is_it_client')
        
        response = super(AuthSignupITPark, self).web_auth_signup(*args, **kw)
        
        if qcontext.get('is_it_client') and qcontext.get('login'):
            # Récupérer le partenaire créé
            partner = request.env['res.partner'].sudo().search([('email', '=', qcontext.get('login'))], limit=1)
            if partner:
                # Rechercher la catégorie "Client IT"
                category_id = request.env['res.partner.category'].sudo().search([('name', '=', 'Client IT')], limit=1)
                if not category_id:
                    # Créer la catégorie si elle n'existe pas
                    category_id = request.env['res.partner.category'].sudo().create({'name': 'Client IT'})
                
                # Mettre à jour les informations du partenaire
                partner.sudo().write({
                    'is_it_client': True,
                    'is_company': True,
                    'company_type': 'company',
                    'category_id': [(4, category_id.id)],
                })
        
        return response 