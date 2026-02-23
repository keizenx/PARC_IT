# -*- coding: utf-8 -*-
# from odoo import http


# class ItPark(http.Controller):
#     @http.route('/PARC_IT/it__park', auth='public', csrf=True)
#     def index(self, **kwargs):
#         return "Hello, world"

#     @http.route('/PARC_IT/it__park/objects', auth='public', csrf=True)
#     def list(self, **kwargs):
#         return http.request.render('PARC_IT.listing', {
#             'root': '/PARC_IT/it__park',
#             'objects': http.request.env['PARC_IT.it__park'].search([]),
#         })

#     @http.route('/PARC_IT/it__park/objects/<model("PARC_IT.it__park", csrf=True):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('PARC_IT.object', {
#             'object': obj
#         })

