# -*- coding: utf-8 -*-
# Modèle désactivé car hr.employee n'existe pas dans le registre
from odoo import models, fields, api

# Classe vide pour éviter les erreurs d'importation
class HREmployeeInherit(models.Model):
    _name = 'it.employee'
    _description = "IT Employee (remplaçant hr.employee qui n'est pas disponible)"
    
    name = fields.Char(string='Nom', required=True)
    notes = fields.Text(string='Notes')
    it_technician = fields.Boolean(string='Technicien IT', default=False)
    is_it_technician = fields.Boolean(string='Est technicien IT', default=False)
    user_id = fields.Many2one('res.users', string='Utilisateur associé')
    department_id = fields.Many2one('res.partner', string='Département')
    job_title = fields.Char(string='Fonction')
    work_phone = fields.Char(string='Téléphone professionnel')
    mobile_phone = fields.Char(string='Téléphone portable')
    work_email = fields.Char(string='Email professionnel')
    company_id = fields.Many2one('res.company', string='Société')
    category_ids = fields.Many2many('ir.module.category', string='Compétences')
    color = fields.Integer(string='Couleur', default=0)
    
    # Vous pouvez ajouter ici les champs nécessaires pour votre application
