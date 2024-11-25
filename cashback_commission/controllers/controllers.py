# -*- coding: utf-8 -*-
# from odoo import http


# class CashbackCommission(http.Controller):
#     @http.route('/cashback_commission/cashback_commission', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cashback_commission/cashback_commission/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cashback_commission.listing', {
#             'root': '/cashback_commission/cashback_commission',
#             'objects': http.request.env['cashback_commission.cashback_commission'].search([]),
#         })

#     @http.route('/cashback_commission/cashback_commission/objects/<model("cashback_commission.cashback_commission"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cashback_commission.object', {
#             'object': obj
#         })

