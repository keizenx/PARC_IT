# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import random
import string

_logger = logging.getLogger(__name__)

class ITPortalUserWizard(models.TransientModel):
    _name = 'it.portal.user.wizard'
    _description = 'Assistant de création d\'utilisateur du portail IT'
    
    name = fields.Char('Nom', required=True)
    email = fields.Char('Email', required=True)
    phone = fields.Char('Téléphone')
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    existing_partner_id = fields.Many2one('res.partner', string='Contact existant', 
                                          domain=[('is_it_client', '=', True)])
    create_new_contact = fields.Boolean('Créer un nouveau contact', default=True)
    is_company = fields.Boolean('Est une entreprise', default=False)
    company_name = fields.Char('Nom de l\'entreprise')
    
    send_invitation = fields.Boolean('Envoyer invitation par email', default=True)
    auto_generate_password = fields.Boolean('Générer mot de passe automatiquement', default=True)
    password = fields.Char('Mot de passe', help="Laissez vide pour générer automatiquement")
    
    # Accès utilisateur
    access_tickets = fields.Boolean('Accès aux tickets', default=True)
    access_equipment = fields.Boolean('Accès aux équipements', default=True)
    access_contracts = fields.Boolean('Accès aux contrats', default=True)
    
    @api.onchange('existing_partner_id')
    def _onchange_existing_partner(self):
        if self.existing_partner_id:
            self.create_new_contact = False
            self.name = self.existing_partner_id.name
            self.email = self.existing_partner_id.email
            self.phone = self.existing_partner_id.phone
            self.is_company = self.existing_partner_id.is_company
            if self.existing_partner_id.parent_id:
                self.company_name = self.existing_partner_id.parent_id.name
    
    def _generate_password(self, length=10):
        """Génère un mot de passe aléatoire avec lettres, chiffres et caractères spéciaux"""
        chars = string.ascii_letters + string.digits + '!@#$%^&*()'
        return ''.join(random.choice(chars) for _ in range(length))
    
    def create_portal_user(self):
        self.ensure_one()
        
        if not self.email:
            raise ValidationError(_("L'email est obligatoire pour créer un utilisateur du portail."))
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = self.env['res.users'].sudo().search([('login', '=', self.email)], limit=1)
        if existing_user:
            raise ValidationError(_("Un utilisateur avec cette adresse email existe déjà."))
        
        partner = None
        
        # Utiliser un partenaire existant ou en créer un nouveau
        if self.create_new_contact:
            partner_vals = {
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'is_it_client': True,
                'is_company': self.is_company,
            }
            
            if self.is_company:
                partner = self.env['res.partner'].sudo().create(partner_vals)
            else:
                # Si ce n'est pas une entreprise mais qu'un nom d'entreprise est fourni
                if self.company_name:
                    company_partner = self.env['res.partner'].sudo().search([
                        ('name', '=', self.company_name),
                        ('is_company', '=', True)
                    ], limit=1)
                    
                    if not company_partner:
                        company_partner = self.env['res.partner'].sudo().create({
                            'name': self.company_name,
                            'is_company': True,
                            'is_it_client': True,
                        })
                    
                    partner_vals['parent_id'] = company_partner.id
                
                partner = self.env['res.partner'].sudo().create(partner_vals)
        else:
            partner = self.existing_partner_id
        
        # Générer ou utiliser le mot de passe fourni
        password = self.password
        if self.auto_generate_password or not password:
            password = self._generate_password()
        
        # Créer l'utilisateur du portail
        portal_group = self.env.ref('base.group_portal')
        
        user_vals = {
            'name': partner.name,
            'login': self.email,
            'password': password,
            'partner_id': partner.id,
            'groups_id': [(6, 0, [portal_group.id])],
            'company_id': self.company_id.id,
            'company_ids': [(6, 0, [self.company_id.id])],
        }
        
        user = self.env['res.users'].sudo().create(user_vals)
        
        # Envoyer l'invitation par email si demandé
        if self.send_invitation:
            template = self.env.ref('portal.mail_template_data_portal_welcome', raise_if_not_found=False)
            if template:
                template.sudo().with_context(
                    dbname=self._cr.dbname,
                    portal_url=partner.with_context(signup_valid=True)._get_signup_url_for_action()[partner.id],
                    portal_password=password,
                ).send_mail(user.id, force_send=True)
                
                # Marquer que l'invitation a été envoyée
                partner.signup_prepare()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Utilisateur créé'),
            'res_model': 'res.users',
            'res_id': user.id,
            'view_mode': 'form',
            'target': 'current',
        } 