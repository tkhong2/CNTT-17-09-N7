# -*- coding: utf-8 -*-

from odoo import fields, models


class KhachHangTransferTemplate(models.Model):
    _name = 'khach_hang_transfer_template'
    _description = 'Mẫu chuyển giao khách hàng'
    _order = 'name'

    name = fields.Char(string='Tên mẫu', required=True)
    active = fields.Boolean(string='Đang hoạt động', default=True)
    trang_thai_hop_tac = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('dang_hop_tac', 'Đang hợp tác'),
        ('tam_ngung', 'Tạm ngưng'),
        ('ngung_hop_tac', 'Ngừng hợp tác'),
    ], string='Lọc theo trạng thái')
    only_overdue = fields.Boolean(string='Chỉ khách hàng có follow-up quá hạn', default=False)
    only_silent = fields.Boolean(string='Chỉ khách hàng im lặng quá N ngày', default=False)
    silent_days = fields.Integer(string='Số ngày im lặng', default=14)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Tên mẫu chuyển giao phải là duy nhất.'),
    ]
