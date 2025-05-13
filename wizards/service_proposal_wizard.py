# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64

class ITServiceProposalWizard(models.TransientModel):
    _name = 'it.service.proposal.wizard'
    _description = 'Assistant d\'envoi de proposition commerciale'

    service_request_id = fields.Many2one('it.service.request', string='Demande de service', required=True)
    proposal_file = fields.Binary(string='Fichier de proposition', required=True)
    proposal_filename = fields.Char(string='Nom du fichier')
    note = fields.Text(string='Note pour le client')

    def action_send_proposal(self):
        """
        Envoie la proposition commerciale au client
        """
        self.ensure_one()
        
        if not self.proposal_file:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erreur'),
                    'message': _('Veuillez fournir un fichier pour la proposition commerciale.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
        
        # Créer une pièce jointe avec le fichier de proposition
        attachment_vals = {
            'name': self.proposal_filename or 'Proposition commerciale.pdf',
            'datas': self.proposal_file,
            'res_model': 'it.service.request',
            'res_id': self.service_request_id.id,
        }
        attachment = self.env['ir.attachment'].create(attachment_vals)
        
        # Mettre à jour la demande de service
        self.service_request_id.set_proposal_sent(attachment.id)
        
        # Ajouter la note dans le chatter si fournie
        if self.note:
            self.service_request_id.message_post(body=self.note)
        
        # Rafraîchir la vue
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        } 