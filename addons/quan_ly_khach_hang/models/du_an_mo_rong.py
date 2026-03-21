# -*- coding: utf-8 -*-
from odoo import models, fields


class DuAnExtend(models.Model):
    _inherit = 'du_an'

    khach_hang_id = fields.Many2one(
        'khach_hang', string='Khách hàng', ondelete='set null', index=True
    )
