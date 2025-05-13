# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request

class ITApiController(http.Controller):
    @http.route('/api/it_park/contract_paid', type='json', auth="public", csrf=False)
    def contract_paid(self, contract_reference=None, **kw):
        if not contract_reference:
            return {'error': 'Contract reference is required'}
        
        contract = request.env['it.contract'].sudo().search([('name', '=', contract_reference)], limit=1)
        if not contract:
            return {'error': 'Contract not found'}
        
        # Activer le contrat et les accès du client
        contract.sudo().write({'state': 'active'})
        contract.partner_id.sudo().write({'is_it_client_approved': True})
        
        # Activer la demande de service associée
        service_request = request.env['it.service.request'].sudo().search([
            ('contract_id', '=', contract.id)
        ], limit=1)
        if service_request:
            service_request.sudo().action_activate()
        
        return {'success': True, 'message': 'Contract activated successfully'} 