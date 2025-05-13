# -*- coding: utf-8 -*-
# Modèle désactivé car hr.employee n'existe pas dans le registre
from odoo import models, fields, api
from odoo.exceptions import UserError

# Classe vide pour éviter les erreurs d'importation
class HREmployeeInherit(models.Model):
    _name = 'it.employee'
    _description = "IT Employee (remplaçant hr.employee qui n'est pas disponible)"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Champs normaux
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
    
    # Champ virtuel pour remplacer color
    color_value = fields.Integer(string='Color Index', default=0, store=True)
    
    # Ajout d'un alias 'color' qui redirige vers 'color_value'
    color = fields.Integer(related='color_value', string='Color', store=False)
    
    # Méthode pour compatibilité avec mail.thread
    def _get_thread_with_access(self, res_id, **kwargs):
        """Méthode requise pour compatibilité avec mail.thread"""
        return self.browse(res_id)
    
    # Attributs spécifiques pour le modèle
    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        return super(HREmployeeInherit, self)._name_search(name, args, operator, limit, name_get_uid)

    # Méthode pour contourner le problème du champ 'color'
    def read(self, fields=None, load='_classic_read'):
        """Override read pour gérer le champ color"""
        if fields and 'color' in fields:
            # Remplacer 'color' par 'color_value' dans les champs demandés
            fields_without_color = [f for f in fields if f != 'color']
            fields_without_color.append('color_value')
            result = super(HREmployeeInherit, self).read(fields_without_color, load)
            # Ajouter manuellement le champ 'color' dans le résultat
            for record in result:
                if 'color_value' in record:
                    record['color'] = record['color_value']
            return result
        return super(HREmployeeInherit, self).read(fields, load)
    
    # Méthode pour la sauvegarde web
    def web_save(self, values, specification=None):
        """Override web_save pour gérer le problème du champ color/color_value"""
        # Créer une copie des valeurs pour éviter de modifier l'original
        values_copy = values.copy()
        
        # Supprimer color et color_value des valeurs pour éviter les erreurs,
        # mais seulement si ce ne sont pas des champs obligatoires
        color_value = None
        if 'color' in values_copy:
            color_value = values_copy.pop('color')
        if 'color_value' in values_copy:
            color_value = values_copy.pop('color_value')
            
        # Traiter la spécification comme dans web_read
        if specification:
            specification_copy = {}
            
            # Parcourir tous les champs de la spécification
            for field_name, field_spec in specification.items():
                # Ignorer complètement les références à 'color' et 'color_value' au niveau principal
                if field_name in ['color', 'color_value']:
                    continue
                    
                # Si c'est un champ composite (comme many2many) avec des sous-champs
                if isinstance(field_spec, dict) and 'fields' in field_spec:
                    # Copier les détails du champ
                    new_field_spec = field_spec.copy()
                    # Traiter les sous-champs
                    if 'fields' in new_field_spec:
                        new_subfields = {}
                        for subfield_name, subfield_spec in new_field_spec['fields'].items():
                            # Ignorer 'color' et 'color_value' dans les sous-champs
                            if subfield_name in ['color', 'color_value']:
                                continue
                            new_subfields[subfield_name] = subfield_spec
                        new_field_spec['fields'] = new_subfields
                    specification_copy[field_name] = new_field_spec
                else:
                    specification_copy[field_name] = field_spec
                
            # Appeler la méthode parente avec les valeurs et la spécification ajustées
            result = super(HREmployeeInherit, self).web_save(values_copy, specification_copy)
            
            # Ajouter manuellement les champs color et color_value au résultat
            if isinstance(result, list):
                for record in result:
                    record['color'] = color_value or 0
                    record['color_value'] = color_value or 0
            
            return result
        else:
            # Pas de spécification, appeler la méthode parente normalement
            result = super(HREmployeeInherit, self).web_save(values_copy, specification)
            
            # Ajouter manuellement les champs color et color_value au résultat
            if isinstance(result, list):
                for record in result:
                    record['color'] = color_value or 0
                    record['color_value'] = color_value or 0
            
            return result
    
    # Méthode spécifique pour web_read
    def web_read(self, specification):
        """Override web_read pour gérer le problème du champ color"""
        if not specification:
            result = super(HREmployeeInherit, self).web_read(specification)
            for record in result:
                record['color'] = 0
                record['color_value'] = 0
            return result
            
        # Créer une copie modifiée de la spécification
        specification_copy = {}
        
        # Noter si color ou color_value ont été demandés
        color_requested = 'color' in specification or 'color_value' in specification
        
        # Parcourir tous les champs de la spécification et supprimer les références à color et color_value
        for field_name, field_spec in specification.items():
            # Ignorer complètement les références à 'color' et 'color_value' au niveau principal
            if field_name in ['color', 'color_value']:
                continue
                
            # Si c'est un champ composite (comme many2many) avec des sous-champs
            if isinstance(field_spec, dict) and 'fields' in field_spec:
                # Copier les détails du champ
                new_field_spec = field_spec.copy()
                # Traiter les sous-champs
                if 'fields' in new_field_spec:
                    new_subfields = {}
                    for subfield_name, subfield_spec in new_field_spec['fields'].items():
                        # Ignorer 'color' et 'color_value' dans les sous-champs
                        if subfield_name in ['color', 'color_value']:
                            continue
                        new_subfields[subfield_name] = subfield_spec
                    new_field_spec['fields'] = new_subfields
                specification_copy[field_name] = new_field_spec
            else:
                specification_copy[field_name] = field_spec
        
        # Appeler la méthode parente avec la spécification nettoyée
        result = super(HREmployeeInherit, self).web_read(specification_copy)
        
        # Ajouter manuellement les champs color et color_value aux résultats
        for record in result:
            # Ajouter un color et color_value par défaut au niveau principal
            if color_requested:
                record['color'] = 0
                record['color_value'] = 0
            
            # Ajouter color et color_value dans les champs many2many (comme category_ids)
            for field_name, field_value in record.items():
                if isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, dict):
                            # Ajouter color et color_value à chaque item
                            item['color'] = 0
                            item['color_value'] = 0
        
        return result
    
    # Méthode spécifique pour search_read
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override search_read pour gérer le problème du champ color"""
        if fields and 'color' in fields:
            # Remplacer 'color' par 'color_value' dans les champs demandés
            fields_without_color = [f for f in fields if f != 'color']
            fields_without_color.append('color_value')
            result = super(HREmployeeInherit, self).search_read(domain, fields_without_color, offset, limit, order)
            # Ajouter manuellement le champ 'color' dans le résultat
            for record in result:
                if 'color_value' in record:
                    record['color'] = record['color_value']
            return result
        return super(HREmployeeInherit, self).search_read(domain, fields, offset, limit, order)
        
    # Méthode spécifique pour web_search_read
    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None, **kwargs):
        """Override web_search_read pour gérer le problème du champ color"""
        # Vérifier et adapter le paramètre specification
        if specification and 'color' in specification:
            # Remplacer 'color' par 'color_value' dans la spécification
            specification['color_value'] = specification.pop('color')
            
        # Adapter le résultat pour inclure 'color'
        # Utiliser des arguments nommés pour éviter les problèmes d'arguments positionnels
        result = super(HREmployeeInherit, self).web_search_read(
            domain=domain, 
            specification=specification, 
            offset=offset, 
            limit=limit, 
            order=order, 
            count_limit=count_limit,
            **kwargs
        )
        
        # Si le résultat contient des enregistrements
        if 'records' in result:
            for record in result['records']:
                record['color'] = record.get('color_value', 0)
                
        return result

    # Vous pouvez ajouter ici les champs nécessaires pour votre application
