from odoo import models, fields, api, _
from datetime import datetime

class ItIncidentResolveWizard(models.TransientModel):
    _name = 'it.incident.resolve.wizard'
    _description = "Assistant de résolution d'incident"
    
    incident_id = fields.Many2one('it.incident', string="Incident", required=True)
    incident_name = fields.Char(string="Titre de l'incident", readonly=True)
    resolution_note = fields.Text(string="Notes de résolution", required=True, 
                               help="Veuillez décrire comment l'incident a été résolu")
    resolution_time = fields.Float(string="Temps de résolution (heures)", required=True, default=1.0)
    
    def action_resolve(self):
        """Résoudre l'incident avec les informations fournies"""
        self.ensure_one()
        resolution_date = fields.Datetime.now()
        
        # Mettre à jour l'incident
        self.incident_id.write({
            'state': 'resolved',
            'resolution_date': resolution_date,
            'resolution_note': self.resolution_note,
            'resolution_time': self.resolution_time
        })
        
        # Ajouter un message dans le chatter
        self.incident_id.message_post(
            body=_(f"Incident résolu. Temps de résolution: {self.resolution_time} heures<br/>Notes: {self.resolution_note}"),
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )
        
        return {'type': 'ir.actions.act_window_close'} 