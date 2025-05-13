from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import uuid
import datetime
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Champs pour identifier les clients IT
    is_it_client = fields.Boolean(string="Client IT", default=False,
                                  help="Cochez cette case si ce partenaire est un client du service informatique")
    
    # Champ pour identifier les fournisseurs IT
    is_it_supplier = fields.Boolean(string="Fournisseur IT", default=False,
                                   help="Cochez cette case si ce partenaire est un fournisseur du service informatique")
    
    # Champs pour la validation de l'email
    email_validation_token = fields.Char(string="Token de validation email", copy=False)
    email_validation_expiration = fields.Datetime(string="Expiration du token", copy=False)
    email_validated = fields.Boolean(string="Email validé", default=False)
    email_validation_url = fields.Char(string="URL de validation email", copy=False)
    
    # Champ pour identifier les éditeurs de logiciels
    is_it_editor = fields.Boolean(string="Éditeur de logiciels", default=False,
                                 help="Cochez cette case si ce partenaire est un éditeur de logiciels")
    
    # Champ pour l'accès approuvé
    is_it_client_approved = fields.Boolean(string="Accès au parc IT approuvé", default=False,
                                        help="Si activé, le client peut accéder à son parc informatique et services associés.")
    
    # Relation avec les utilisateurs
    user_ids = fields.One2many('res.users', 'partner_id', string='Utilisateurs associés')
    
    # Gestion multi-sites
    is_it_site = fields.Boolean(string="Site IT", default=False,
                                help="Cochez cette case si ce partenaire est un site d'un client IT")
    parent_it_client_id = fields.Many2one('res.partner', string="Client IT parent", 
                                          domain=[('is_it_client', '=', True), ('is_company', '=', True)],
                                          help="Sélectionnez le client IT parent si ce partenaire est un site client")
    it_site_ids = fields.One2many('res.partner', 'parent_it_client_id', string="Sites clients",
                                 domain=[('is_it_site', '=', True)])
    it_site_count = fields.Integer(string="Nombre de sites", compute='_compute_it_site_count')
    
    # Compteurs pour les équipements, licences et incidents
    equipment_count = fields.Integer(string="Nombre d'équipements", compute='_compute_equipment_count')
    license_count = fields.Integer(string="Nombre de licences", compute='_compute_license_count')
    incident_count = fields.Integer(string="Nombre d'incidents", compute='_compute_incident_count')
    it_invoice_count = fields.Integer(string="Nombre de factures IT", compute='_compute_it_invoice_count')
    ticket_count = fields.Integer(string="Nombre de tickets", compute='_compute_ticket_count')
    
    # Champ pour suivre les demandes de prestation
    service_request_count = fields.Integer(string="Demandes de prestation", compute='_compute_service_request_count')
    
    # Nouveau champ pour gérer le statut du contrat
    is_it_contract_paid = fields.Boolean('Contrat IT payé', default=False)
    is_it_client_pending = fields.Boolean('Client IT en attente', default=False)
    
    # Champs spécifiques pour les partenaires IT
    is_it_manufacturer = fields.Boolean('Fabricant IT', default=False)
    
    # Champs pour l'accès contrôlé au parc informatique
    has_active_service_request = fields.Boolean('A une demande de prestation active', compute='_compute_service_request_status', store=True)
    has_proposal = fields.Boolean('A reçu une proposition', compute='_compute_service_request_status', store=True)
    has_accepted_proposal = fields.Boolean('A accepté une proposition', compute='_compute_service_request_status', store=True)
    active_service_request_id = fields.Many2one('it.service.request', string='Demande de prestation active', compute='_compute_service_request_status', store=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_it_client'):
                vals['is_it_client'] = False  # Désactiver temporairement le statut client IT
                vals['is_it_client_pending'] = True  # Marquer comme en attente
        return super(ResPartner, self).create(vals_list)

    def action_validate_it_contract(self):
        """Action pour valider le contrat IT après paiement"""
        self.ensure_one()
        if self.is_it_client_pending:
            self.write({
                'is_it_client': True,
                'is_it_contract_paid': True,
                'is_it_client_pending': False,
                'is_it_client_approved': True
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    @api.depends('is_it_client', 'is_it_contract_paid', 'is_it_client_pending')
    def _compute_display_it_client(self):
        """Calculer si le client doit être affiché dans la vue des clients IT"""
        for partner in self:
            partner.display_as_it_client = partner.is_it_client and partner.is_it_contract_paid

    display_as_it_client = fields.Boolean(
        'Afficher comme client IT', 
        compute='_compute_display_it_client',
        store=True
    )
    
    @api.depends('is_it_client')
    def _compute_service_request_count(self):
        for partner in self:
            partner.service_request_count = self.env['it.service.request'].search_count([
                ('partner_id', '=', partner.id)
            ])
    
    @api.depends('it_site_ids')
    def _compute_it_site_count(self):
        for partner in self:
            partner.it_site_count = len(partner.it_site_ids)
            
    @api.depends('is_it_client')
    def _compute_equipment_count(self):
        for partner in self:
            if partner.is_it_client:
                equipment = self.env['it.equipment'].search([('client_id', '=', partner.id)])
                partner.equipment_count = len(equipment)
            else:
                partner.equipment_count = 0
            
    @api.depends('is_it_client')
    def _compute_license_count(self):
        for partner in self:
            if partner.is_it_client:
                licenses = self.env['it.license'].search([('client_id', '=', partner.id)])
                partner.license_count = len(licenses)
            else:
                partner.license_count = 0
            
    @api.depends('is_it_client')
    def _compute_incident_count(self):
        for partner in self:
            if partner.is_it_client:
                incidents = self.env['it.incident'].search([('client_id', '=', partner.id)])
                partner.incident_count = len(incidents)
            else:
                partner.incident_count = 0
    
    @api.depends('is_it_client', 'is_it_site', 'parent_it_client_id')
    def _compute_it_invoice_count(self):
        for partner in self:
            domain = []
            
            if partner.is_it_client:
                # Pour un client IT parent, inclure les factures de tous ses sites
                if partner.it_site_ids:
                    domain = ['&', ('move_type', '=', 'out_invoice'), '|', ('partner_id', '=', partner.id), ('partner_id', 'in', partner.it_site_ids.ids)]
                else:
                    domain = [('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice')]
            elif partner.is_it_site and partner.parent_it_client_id:
                # Pour un site IT, uniquement ses propres factures
                domain = [('partner_id', '=', partner.id), ('move_type', '=', 'out_invoice')]
            else:
                partner.it_invoice_count = 0
                continue
                
            partner.it_invoice_count = self.env['account.move'].search_count(domain)
            
    @api.depends('is_it_client', 'is_it_site', 'parent_it_client_id')
    def _compute_ticket_count(self):
        for partner in self:
            domain = []
            
            if partner.is_it_client:
                # Pour un client IT parent, inclure les tickets de tous ses sites
                if partner.it_site_ids:
                    domain = ['|', ('client_id', '=', partner.id), ('client_id', 'in', partner.it_site_ids.ids)]
                else:
                    domain = [('client_id', '=', partner.id)]
            elif partner.is_it_site and partner.parent_it_client_id:
                # Pour un site IT, uniquement ses propres tickets
                domain = [('client_id', '=', partner.id)]
            else:
                partner.ticket_count = 0
                continue
                
            partner.ticket_count = self.env['it.ticket'].search_count(domain)
    
    def action_view_equipment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_equipment_client")
        action['domain'] = [('client_id', '=', self.id)]
        action['context'] = {'default_client_id': self.id}
        return action
        
    def action_view_licenses(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_license_client")
        action['domain'] = [('client_id', '=', self.id)]
        action['context'] = {'default_client_id': self.id}
        return action
        
    def action_view_incidents(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_incident_client")
        action['domain'] = [('client_id', '=', self.id)]
        action['context'] = {'default_client_id': self.id}
        return action
        
    def action_view_it_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_client_invoices")
        
        # Définir le domaine en fonction du type de partenaire
        if self.is_it_client and self.it_site_ids:
            # Inclure les factures des sites pour un client parent
            action['domain'] = ['&', ('move_type', '=', 'out_invoice'), '|', ('partner_id', '=', self.id), ('partner_id', 'in', self.it_site_ids.ids)]
        elif self.is_it_site and self.parent_it_client_id:
            # Uniquement les factures du site
            action['domain'] = [('partner_id', '=', self.id), ('move_type', '=', 'out_invoice')]
        else:
            action['domain'] = [('partner_id', '=', self.id), ('move_type', '=', 'out_invoice')]
        
        # Context pour la création de factures
        if self.is_it_site:
            action['context'] = {
                'default_partner_id': self.id,
                'default_move_type': 'out_invoice',
                'default_parent_partner_id': self.parent_it_client_id.id,
            }
        else:
            action['context'] = {'default_partner_id': self.id, 'default_move_type': 'out_invoice'}
            
        return action
        
    def action_view_sites(self):
        """Voir les sites de ce client IT"""
        self.ensure_one()
        
        if not self.is_it_client:
            return False
            
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_client_sites")
        action['domain'] = [('parent_it_client_id', '=', self.id), ('is_it_site', '=', True)]
        action['context'] = {
            'default_parent_it_client_id': self.id,
            'default_is_it_site': True,
            'default_is_company': True,
        }
        
        return action
        
    def action_view_contracts(self):
        """Voir les contrats associés à ce client ou site client"""
        self.ensure_one()
        
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_contract")
        
        # Définir le domaine en fonction du type de partenaire
        if self.is_it_client and self.it_site_ids:
            # Inclure les contrats des sites pour un client parent
            action['domain'] = ['|', ('partner_id', '=', self.id), ('partner_id', 'in', self.it_site_ids.ids)]
        else:
            action['domain'] = [('partner_id', '=', self.id)]
        
        # Context pour la création de contrats
        action['context'] = {
            'default_partner_id': self.id,
        }
            
        return action
        
    def action_add_equipment(self):
        """Méthode pour ajouter un équipement depuis le formulaire site client"""
        self.ensure_one()
        
        if not self.is_it_site:
            return False
            
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_equipment")
        action['views'] = [(self.env.ref('it__park.view_it_equipment_form').id, 'form')]
        action['target'] = 'new'
        action['context'] = {
            'default_client_id': self.id,
            'default_site_id': self.id,
            'default_parent_client_id': self.parent_it_client_id.id if self.parent_it_client_id else False,
        }
        
        return action

    # Ajout d'un filtre pour garantir que seuls les clients créés depuis le module it__park sont visibles
    @api.model
    def action_it_clients_only(self):
        """Action pour afficher uniquement les clients créés depuis le module it__park"""
        action = self.env.ref('it__park.action_it_clients').read()[0]
        # Garantir que tous les clients IT sont visibles (actifs + en attente)
        action['domain'] = ['|', 
                           ('is_it_client', '=', True),
                           ('is_it_client_pending', '=', True),
                           ('is_company', '=', True), 
                           ('is_it_site', '=', False)]
        action['context'] = {'default_is_it_client': True, 'default_is_company': True}
        return action
        
    @api.model
    def action_it_suppliers_only(self):
        """Action pour afficher uniquement les fournisseurs créés depuis le module it__park"""
        action = self.env.ref('it__park.action_it_suppliers').read()[0]
        # Garantir que seuls les fournisseurs créés par ce module sont visibles
        # mais permettre la création de nouveaux fournisseurs
        action['domain'] = [('is_it_supplier', '=', True), ('is_company', '=', True)]
        action['context'] = {
            'default_is_it_supplier': True, 
            'default_is_company': True, 
            'default_supplier_rank': 1,
            'create': True,
            'edit': True
        }
        return action
        
    def action_mark_as_it_supplier(self):
        """Marquer des partenaires existants comme fournisseurs IT"""
        for partner in self:
            partner.write({
                'is_it_supplier': True,
                'supplier_rank': max(partner.supplier_rank, 1)
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Fournisseurs IT'),
                'message': _('%s partenaire(s) marqué(s) comme fournisseur(s) IT.') % len(self),
                'sticky': False,
                'type': 'success'
            }
        } 

    @api.constrains('name')
    def _check_name(self):
        for partner in self:
            if not partner.name:
                raise ValidationError(_("Le nom du partenaire est obligatoire.")) 

    def action_create_user(self):
        """Créer un utilisateur pour le contact."""
        self.ensure_one()
        if not self.email:
            raise UserError(_("Une adresse email est requise pour créer un utilisateur."))
            
        if self.user_ids:
            raise UserError(_("Un utilisateur existe déjà pour ce contact."))

        # Créer l'utilisateur
        user_values = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'partner_id': self.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_portal').id
            ])]
        }
        
        user = self.env['res.users'].sudo().create(user_values)
        
        # Envoyer l'email de réinitialisation du mot de passe
        user.action_reset_password()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Succès'),
                'message': _('Un utilisateur a été créé et un email de configuration a été envoyé à %s', self.email),
                'type': 'success',
                'sticky': False,
            }
        } 

    def action_view_tickets(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_ticket")
        
        # Définir le domaine en fonction du type de partenaire
        if self.is_it_client and self.it_site_ids:
            # Inclure les tickets des sites pour un client parent
            action['domain'] = ['|', ('client_id', '=', self.id), ('client_id', 'in', self.it_site_ids.ids)]
        elif self.is_it_site and self.parent_it_client_id:
            # Uniquement les tickets du site
            action['domain'] = [('client_id', '=', self.id)]
        else:
            action['domain'] = [('client_id', '=', self.id)]
        
        # Context pour la création de tickets
        if self.is_it_site:
            action['context'] = {
                'default_client_id': self.id,
                'default_parent_client_id': self.parent_it_client_id.id,
            }
        else:
            action['context'] = {'default_client_id': self.id}
            
        return action 

    def action_approve_it_client(self):
        """Approuve le client IT"""
        self.ensure_one()
        if self.is_it_client and not self.is_it_client_approved:
            self.is_it_client_approved = True
            
            # Notification au client que son compte a été approuvé
            subject = _("Votre compte a été approuvé")
            body = _("""
                <p>Bonjour %s,</p>
                <p>Nous avons le plaisir de vous informer que votre compte a été approuvé. 
                Vous pouvez maintenant accéder à notre plateforme et soumettre une demande de prestation.</p>
                <p>Cordialement,<br/>L'équipe %s</p>
            """) % (self.name, self.env.company.name)
            
            # Envoyer une notification interne (ne nécessite pas de configuration email)
            self.message_post(body=body, subject=subject, message_type='comment', subtype_xmlid='mail.mt_comment')
            
            # Si l'utilisateur a un compte portal associé, envoyer un message à l'utilisateur
            users = self.env['res.users'].sudo().search([('partner_id', '=', self.id)])
            if users:
                for user in users:
                    user.notification_ids = [(0, 0, {
                        'res_partner_id': self.id,
                        'notification_type': 'inbox',
                        'notification_status': 'ready'
                    })]
                    
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Client approuvé"),
                    'message': _("Le client %s a été approuvé avec succès.") % self.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
    
    def action_revoke_it_client(self):
        """Révoque l'approbation du client IT"""
        self.ensure_one()
        if self.is_it_client and self.is_it_client_approved:
            self.is_it_client_approved = False
            
            # Notification au client que son compte a été révoqué
            subject = _("Accès au compte restreint")
            body = _("""
                <p>Bonjour %s,</p>
                <p>Nous vous informons que l'accès à votre compte a été temporairement restreint.
                Veuillez nous contacter pour plus d'informations.</p>
                <p>Cordialement,<br/>L'équipe %s</p>
            """) % (self.name, self.env.company.name)
            
            # Envoyer une notification interne
            self.message_post(body=body, subject=subject, message_type='comment', subtype_xmlid='mail.mt_comment')
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Approbation révoquée"),
                    'message': _("L'approbation du client %s a été révoquée.") % self.name,
                    'type': 'warning',
                    'sticky': False,
                }
            } 

    def action_force_activate_it_access(self):
        """Action pour forcer l'activation de l'accès au parc IT, à utiliser en cas de problème"""
        self.ensure_one()
        self.write({
            'is_it_client': True,
            'is_it_client_approved': True,
            'is_it_contract_paid': True,
            'is_it_client_pending': False
        })
        
        # Créer un contrat si nécessaire
        service_requests = self.env['it.service.request'].search([
            ('partner_id', '=', self.id),
            ('state', 'in', ['proposal_accepted', 'invoiced', 'paid'])
        ], limit=1)
        
        if service_requests:
            # Marquer la demande comme payée si elle ne l'est pas déjà
            if service_requests.state in ['proposal_accepted', 'invoiced']:
                service_requests.write({'state': 'paid'})
            
            # Créer un contrat si la demande n'en a pas déjà un
            if not service_requests.contract_id:
                service_requests.sudo().action_create_contract()
        
        # Message pour confirmer l'action
        message = _("Accès au parc IT forcé manuellement.")
        self.message_post(body=message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Succès'),
                'message': _("L'accès au parc IT a été activé avec succès."),
                'type': 'success',
                'sticky': False,
            }
        } 

    def generate_email_validation_token(self):
        """Génère un token unique pour la validation de l'email"""
        self.ensure_one()
        token = str(uuid.uuid4())
        # Le token expire après 24 heures
        expiration = fields.Datetime.now() + datetime.timedelta(days=1)
        self.write({
            'email_validation_token': token,
            'email_validation_expiration': expiration,
            'email_validated': False
        })
        return token

    def validate_email_token(self, token):
        """Valide le token d'email et approuve le client si valide"""
        self.ensure_one()
        if not token or not self.email_validation_token or token != self.email_validation_token:
            return False
        
        if not self.email_validation_expiration or fields.Datetime.now() > self.email_validation_expiration:
            return False
        
        self.write({
            'email_validated': True,
            'email_validation_token': False,
            'email_validation_expiration': False
        })
        
        # Marquer comme client IT approuvé si c'était en attente
        if self.is_it_client_pending:
            self.write({
                'is_it_client': True,
                'is_it_client_pending': False
            })
            
        return True

    def action_send_email_validation(self):
        """Envoie un email avec un lien de validation"""
        self.ensure_one()
        
        if not self.email:
            raise UserError(_("Le partenaire n'a pas d'adresse email définie."))
        
        # Générer un nouveau token
        token = self.generate_email_validation_token()
        
        # Générer l'URL de validation
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        validation_url = f"{base_url}/it/validate-email?token={token}&partner_id={self.id}"
        
        # Stocker l'URL de validation dans tous les cas (pour l'administrateur)
        self.write({'email_validation_url': validation_url})
        
        # Récupérer le template
        template = self.env.ref('it__park.email_template_it_registration_validation')
        if not template:
            _logger.error("Template de validation d'email non trouvé")
            return False
        
        # Vérifier la configuration de l'email
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            _logger.warning("Aucun serveur mail configuré pour l'envoi du mail de validation")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Configuration email manquante'),
                    'message': _("Impossible d'envoyer l'email de validation. URL de validation stockée pour l'administrateur."),
                    'sticky': True,
                    'type': 'warning',
                }
            }
            
        # Configurer un email d'expéditeur par défaut si nécessaire
        company = self.env.company
        email_from = company.email or "noreply@example.com"
        
        try:
            # Force l'utilisation du serveur de mail et de l'adresse d'expéditeur
            template = template.with_context(
                email_to=self.email,
                client_name=self.name,
                validation_url=validation_url,
                force_email_send=True,
                mail_server_id=mail_server.id,
                email_from=email_from
            )
            
            # Envoyer l'email en utilisant une syntaxe plus directe
            mail_id = template.send_mail(
                self.id, 
                force_send=True,
                email_values={
                    'email_from': email_from,
                    'mail_server_id': mail_server.id
                }
            )
            
            # Vérifier si l'email a été créé
            mail = self.env['mail.mail'].sudo().browse(mail_id)
            if mail.exists():
                _logger.info("Email de validation créé avec succès: ID %s, État: %s", mail_id, mail.state)
                if mail.state == 'exception':
                    _logger.warning("Email de validation en état d'exception: %s", mail.failure_reason)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Email envoyé'),
                    'message': _("Un email de validation a été envoyé à l'adresse %s.") % self.email,
                    'sticky': False,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error("Erreur lors de l'envoi du mail de validation: %s", str(e))
            # Afficher l'URL de validation directement
            validation_msg = _("""
                <p>L'envoi de l'email a échoué. Veuillez utiliser ce lien pour valider votre email:</p>
                <p><a href="%(url)s">%(url)s</a></p>
            """) % {'url': validation_url}
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erreur d\'envoi'),
                    'message': validation_msg,
                    'sticky': True,
                    'type': 'danger',
                }
            }

    def action_resend_validation_email(self):
        """Action pour renvoyer l'email de validation"""
        self.ensure_one()
        if not self.email:
            raise UserError(_("Le partenaire n'a pas d'adresse email définie."))
        
        _logger.info(f"Demande de renvoi d'email de validation pour {self.name}")
        
        # Si l'email est déjà validé, on peut le réinitialiser pour permettre une nouvelle validation
        if self.email_validated:
            self.write({'email_validated': False})
        
        # Utiliser l'action standard pour envoyer l'email de validation
        return self.action_send_email_validation()
        
    def action_force_validate_email(self):
        """Action pour forcer la validation de l'email sans envoi de lien"""
        self.ensure_one()
        _logger.info(f"Validation forcée de l'email pour {self.name}")
        
        self.write({
            'email_validated': True,
            'email_validation_token': False,
            'email_validation_expiration': False
        })
        
        # Activer le client IT si en attente
        if self.is_it_client_pending:
            self.write({
                'is_it_client': True,
                'is_it_client_pending': False
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Email validé'),
                'message': _("L'adresse email a été validée manuellement."),
                'type': 'success',
                'sticky': False,
            }
        }