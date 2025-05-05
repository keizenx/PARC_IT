from odoo import api, fields, models, _

class ITTicketResolveWizard(models.TransientModel):
    _name = 'it.ticket.resolve.wizard'
    _description = 'Assistant de résolution de ticket IT'
    
    ticket_id = fields.Many2one('it.ticket', string='Ticket', required=True)
    ticket_name = fields.Char('Titre du ticket', readonly=True)
    resolution_note = fields.Text('Notes de résolution', required=True)
    
    def action_resolve_ticket(self):
        self.ensure_one()
        
        # Mettre à jour le ticket avec les notes de résolution
        ticket = self.ticket_id
        ticket.write({
            'resolution_note': self.resolution_note,
            'state': 'resolved',
        })
        
        # Ajouter un message dans le chatter
        ticket.message_post(
            body=_("""<p>Ticket résolu</p><p><strong>Notes de résolution:</strong><br/>%s</p>""") % self.resolution_note,
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
        
        return {'type': 'ir.actions.act_window_close'} 