# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
import json


class ITDashboard(models.Model):
    _name = 'it.dashboard'
    _description = 'Tableau de bord du parc IT'
    
    # Champs pour la sélection de la date
    date_from = fields.Date(string='Date de début', required=True, 
                           default=lambda self: fields.Date.context_today(self) - timedelta(days=30))
    date_to = fields.Date(string='Date de fin', required=True,
                         default=lambda self: fields.Date.context_today(self))
    
    # KPIs Équipements
    total_equipment = fields.Integer(string='Équipements totaux', compute='_compute_equipment_kpi')
    active_equipment = fields.Integer(string='Équipements actifs', compute='_compute_equipment_kpi')
    maintenance_equipment = fields.Integer(string='Équipements en maintenance', compute='_compute_equipment_kpi')
    eol_equipment = fields.Integer(string='Équipements en fin de vie', compute='_compute_equipment_kpi')
    
    # KPIs Incidents
    new_incidents = fields.Integer(string='Nouveaux incidents', compute='_compute_incident_kpi')
    in_progress_incidents = fields.Integer(string='Incidents en cours', compute='_compute_incident_kpi')
    resolved_incidents = fields.Integer(string='Incidents résolus', compute='_compute_incident_kpi')
    avg_resolution_time = fields.Float(string='Temps moyen de résolution (heures)', compute='_compute_incident_kpi')
    
    # KPIs Licences
    total_licenses = fields.Integer(string='Licences totales', compute='_compute_license_kpi')
    active_licenses = fields.Integer(string='Licences actives', compute='_compute_license_kpi')
    expiring_soon_licenses = fields.Integer(string='Licences expirant bientôt', compute='_compute_license_kpi')
    expired_licenses = fields.Integer(string='Licences expirées', compute='_compute_license_kpi')
    
    # Graphiques
    incident_by_category_graph = fields.Text(string='Graphique des incidents par catégorie', 
                                           compute='_compute_incident_by_category')
    incident_evolution_graph = fields.Text(string='Graphique d\'évolution des incidents',
                                         compute='_compute_incident_evolution')
    
    # Ajout d'un champ pour assurer la persistance
    name = fields.Char(string='Nom', default='Dashboard')
    
    @api.depends('date_from', 'date_to')
    def _compute_equipment_kpi(self):
        for record in self:
            # Nombre total d'équipements
            record.total_equipment = self.env['it.equipment'].search_count([])
            
            # Équipements actifs
            record.active_equipment = self.env['it.equipment'].search_count([
                ('state', '=', 'installed')
            ])
            
            # Équipements en maintenance
            record.maintenance_equipment = self.env['it.equipment'].search_count([
                ('state', '=', 'maintenance')
            ])
            
            # Équipements en fin de vie
            record.eol_equipment = self.env['it.equipment'].search_count([
                ('state', '=', 'end_of_life')
            ])
    
    @api.depends('date_from', 'date_to')
    def _compute_incident_kpi(self):
        for record in self:
            domain = [
                ('create_date', '>=', record.date_from),
                ('create_date', '<=', record.date_to)
            ]
            
            # Nouveaux incidents
            record.new_incidents = self.env['it.incident'].search_count(
                domain + [('state', '=', 'new')]
            )
            
            # Incidents en cours
            record.in_progress_incidents = self.env['it.incident'].search_count(
                domain + [('state', '=', 'in_progress')]
            )
            
            # Incidents résolus
            resolved_domain = domain + [('state', '=', 'resolved')]
            record.resolved_incidents = self.env['it.incident'].search_count(resolved_domain)
            
            # Temps moyen de résolution
            resolved_incidents = self.env['it.incident'].search(resolved_domain)
            if resolved_incidents:
                total_hours = 0
                count = 0
                for incident in resolved_incidents:
                    if incident.date_resolved and incident.create_date:
                        resolution_time = (incident.date_resolved - incident.create_date).total_seconds() / 3600
                        total_hours += resolution_time
                        count += 1
                record.avg_resolution_time = total_hours / count if count else 0
            else:
                record.avg_resolution_time = 0
    
    @api.depends('date_from', 'date_to')
    def _compute_license_kpi(self):
        for record in self:
            today = fields.Date.context_today(self)
            
            # Total des licences
            record.total_licenses = self.env['it.license'].search_count([])
            
            # Licences actives
            record.active_licenses = self.env['it.license'].search_count([
                ('state', '=', 'active'),
                ('end_date', '>=', today)
            ])
            
            # Licences expirant bientôt (dans les 30 jours)
            expiry_date = today + timedelta(days=30)
            record.expiring_soon_licenses = self.env['it.license'].search_count([
                ('state', '=', 'active'),
                ('end_date', '>=', today),
                ('end_date', '<=', expiry_date)
            ])
            
            # Licences expirées
            record.expired_licenses = self.env['it.license'].search_count([
                ('end_date', '<', today)
            ])
    
    @api.depends('date_from', 'date_to')
    def _compute_incident_by_category(self):
        for record in self:
            # Récupérer les types d'incidents avec leurs nombres
            domain = [
                ('create_date', '>=', record.date_from),
                ('create_date', '<=', record.date_to)
            ]
            
            incident_types = self.env['it.incident.type'].search([])
            data = []
            
            for incident_type in incident_types:
                count = self.env['it.incident'].search_count(
                    domain + [('type_id', '=', incident_type.id)]
                )
                if count > 0:
                    data.append({
                        'label': incident_type.name,
                        'value': count,
                        'color': self._get_random_color(incident_type.id)
                    })
            
            record.incident_by_category_graph = json.dumps(data)
    
    @api.depends('date_from', 'date_to')
    def _compute_incident_evolution(self):
        for record in self:
            # Préparation de l'intervalle de dates
            current_date = record.date_from
            date_end = record.date_to
            delta = (date_end - current_date).days + 1
            
            # Si la période est trop longue, regrouper par semaine
            if delta > 30:
                # Regroupement par semaine
                data = self._get_weekly_incident_data(record.date_from, record.date_to)
            else:
                # Données quotidiennes
                data = []
                while current_date <= date_end:
                    next_date = current_date + timedelta(days=1)
                    count = self.env['it.incident'].search_count([
                        ('create_date', '>=', current_date),
                        ('create_date', '<', next_date)
                    ])
                    
                    data.append({
                        'date': current_date.strftime('%d/%m/%Y'),
                        'value': count
                    })
                    
                    current_date = next_date
            
            record.incident_evolution_graph = json.dumps(data)
    
    def _get_weekly_incident_data(self, date_from, date_to):
        """Regroupe les incidents par semaine sur la période donnée"""
        # Début de la semaine (lundi)
        start_week = date_from - timedelta(days=date_from.weekday())
        end_date = date_to
        
        data = []
        while start_week <= end_date:
            end_week = min(start_week + timedelta(days=6), end_date)
            next_week = start_week + timedelta(days=7)
            
            count = self.env['it.incident'].search_count([
                ('create_date', '>=', start_week),
                ('create_date', '<=', end_week)
            ])
            
            data.append({
                'date': f'Semaine du {start_week.strftime("%d/%m/%Y")}',
                'value': count
            })
            
            start_week = next_week
            
        return data
    
    def _get_random_color(self, seed):
        """Génère une couleur aléatoire basée sur une graine"""
        import random
        random.seed(seed)
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return f'rgb({r}, {g}, {b})'
    
    def action_refresh_data(self):
        """Rafraîchit les données du tableau de bord"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        } 