from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Champs pour identifier les clients IT
    is_it_client = fields.Boolean(string="Client IT", default=False,
                                  help="Cochez cette case si ce partenaire est un client du service informatique")
    
    # Champ pour identifier les fournisseurs IT
    is_it_supplier = fields.Boolean(string="Fournisseur IT", default=False,
                                   help="Cochez cette case si ce partenaire est un fournisseur du service informatique")
    
    # Champ pour identifier les éditeurs de logiciels
    is_it_editor = fields.Boolean(string="Éditeur de logiciels", default=False,
                                 help="Cochez cette case si ce partenaire est un éditeur de logiciels")
    
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
    
    @api.depends('it_site_ids')
    def _compute_it_site_count(self):
        for partner in self:
            partner.it_site_count = len(partner.it_site_ids)
            
    @api.depends('is_it_client', 'is_it_site', 'parent_it_client_id')
    def _compute_equipment_count(self):
        for partner in self:
            domain = []
            
            if partner.is_it_client:
                # Pour un client IT parent, inclure les équipements de tous ses sites
                if partner.it_site_ids:
                    domain = ['|', ('client_id', '=', partner.id), ('client_id', 'in', partner.it_site_ids.ids)]
                else:
                    domain = [('client_id', '=', partner.id)]
            elif partner.is_it_site and partner.parent_it_client_id:
                # Pour un site IT, uniquement ses propres équipements
                domain = [('client_id', '=', partner.id)]
            else:
                partner.equipment_count = 0
                continue
                
            partner.equipment_count = self.env['it.equipment'].search_count(domain)
            
    @api.depends('is_it_client', 'is_it_site', 'parent_it_client_id')
    def _compute_license_count(self):
        for partner in self:
            domain = []
            
            if partner.is_it_client:
                # Pour un client IT parent, inclure les licences de tous ses sites
                if partner.it_site_ids:
                    domain = ['|', ('client_id', '=', partner.id), ('client_id', 'in', partner.it_site_ids.ids)]
                else:
                    domain = [('client_id', '=', partner.id)]
            elif partner.is_it_site and partner.parent_it_client_id:
                # Pour un site IT, uniquement ses propres licences
                domain = [('client_id', '=', partner.id)]
            else:
                partner.license_count = 0
                continue
                
            partner.license_count = self.env['it.license'].search_count(domain)
            
    @api.depends('is_it_client', 'is_it_site', 'parent_it_client_id')
    def _compute_incident_count(self):
        for partner in self:
            domain = []
            
            if partner.is_it_client:
                # Pour un client IT parent, inclure les incidents de tous ses sites
                if partner.it_site_ids:
                    domain = ['|', ('client_id', '=', partner.id), ('client_id', 'in', partner.it_site_ids.ids)]
                else:
                    domain = [('client_id', '=', partner.id)]
            elif partner.is_it_site and partner.parent_it_client_id:
                # Pour un site IT, uniquement ses propres incidents
                domain = [('client_id', '=', partner.id)]
            else:
                partner.incident_count = 0
                continue
                
            partner.incident_count = self.env['it.incident'].search_count(domain)
    
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
            
    def action_view_equipment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_equipment")
        
        # Définir le domaine en fonction du type de partenaire
        if self.is_it_client and self.it_site_ids:
            # Inclure les équipements des sites pour un client parent
            action['domain'] = ['|', ('client_id', '=', self.id), ('client_id', 'in', self.it_site_ids.ids)]
        elif self.is_it_site and self.parent_it_client_id:
            # Uniquement les équipements du site
            action['domain'] = [('client_id', '=', self.id)]
        else:
            action['domain'] = [('client_id', '=', self.id)]
        
        # Context pour la création d'équipements
        if self.is_it_site:
            action['context'] = {
                'default_client_id': self.id,
                'default_parent_client_id': self.parent_it_client_id.id,
            }
        else:
            action['context'] = {'default_client_id': self.id}
            
        return action
        
    def action_view_licenses(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_license")
        
        # Définir le domaine en fonction du type de partenaire
        if self.is_it_client and self.it_site_ids:
            # Inclure les licences des sites pour un client parent
            action['domain'] = ['|', ('client_id', '=', self.id), ('client_id', 'in', self.it_site_ids.ids)]
        elif self.is_it_site and self.parent_it_client_id:
            # Uniquement les licences du site
            action['domain'] = [('client_id', '=', self.id)]
        else:
            action['domain'] = [('client_id', '=', self.id)]
        
        # Context pour la création de licences
        if self.is_it_site:
            action['context'] = {
                'default_client_id': self.id,
                'default_parent_client_id': self.parent_it_client_id.id,
            }
        else:
            action['context'] = {'default_client_id': self.id}
            
        return action
        
    def action_view_incidents(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("it__park.action_it_incident")
        
        # Définir le domaine en fonction du type de partenaire
        if self.is_it_client and self.it_site_ids:
            # Inclure les incidents des sites pour un client parent
            action['domain'] = ['|', ('client_id', '=', self.id), ('client_id', 'in', self.it_site_ids.ids)]
        elif self.is_it_site and self.parent_it_client_id:
            # Uniquement les incidents du site
            action['domain'] = [('client_id', '=', self.id)]
        else:
            action['domain'] = [('client_id', '=', self.id)]
        
        # Context pour la création d'incidents
        if self.is_it_site:
            action['context'] = {
                'default_client_id': self.id,
                'default_parent_client_id': self.parent_it_client_id.id,
            }
        else:
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
        # Garantir que seuls les clients IT sont visibles (peu importe qui les a créés)
        action['domain'] = [('is_it_client', '=', True), ('is_company', '=', True), ('is_it_site', '=', False)]
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