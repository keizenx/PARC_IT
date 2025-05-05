# -*- coding: utf-8 -*-
# from odoo import http


# class ItPark(http.Controller):
#     @http.route('/it__park/it__park', auth='public', csrf=True)
#     def index(self, **kwargs):
#         return "Hello, world"

#     @http.route('/it__park/it__park/objects', auth='public', csrf=True)
#     def list(self, **kwargs):
#         return http.request.render('it__park.listing', {
#             'root': '/it__park/it__park',
#             'objects': http.request.env['it__park.it__park'].search([]),
#         })

#     @http.route('/it__park/it__park/objects/<model("it__park.it__park", csrf=True):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('it__park.object', {
#             'object': obj
#         })

