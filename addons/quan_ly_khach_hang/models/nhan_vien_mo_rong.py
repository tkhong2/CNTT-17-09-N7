# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NhanVienExtend(models.Model):
    _inherit = 'nhan_vien'

    user_id = fields.Many2one(
        'res.users', string='Tài khoản người dùng',
        help='Liên kết với tài khoản Odoo để áp dụng phân quyền'
    )

    # Khách hàng phụ trách
    khach_hang_phu_trach_ids = fields.One2many(
        'khach_hang', 'nhan_vien_phu_trach_id', string='Khách hàng phụ trách'
    )
    so_khach_hang_phu_trach = fields.Integer(
        string='Số khách hàng phụ trách', compute='_compute_so_khach_hang'
    )

    # Dự án quản lý
    du_an_quan_ly_ids = fields.One2many(
        'du_an', 'nguoi_quan_ly_id', string='Dự án quản lý'
    )
    so_du_an_quan_ly = fields.Integer(
        string='Số dự án quản lý', compute='_compute_so_du_an'
    )

    def _compute_so_khach_hang(self):
        for rec in self:
            rec.so_khach_hang_phu_trach = self.env['khach_hang'].search_count([
                ('nhan_vien_phu_trach_id', '=', rec.id)
            ])

    def _compute_so_du_an(self):
        for rec in self:
            rec.so_du_an_quan_ly = self.env['du_an'].search_count([
                ('nguoi_quan_ly_id', '=', rec.id)
            ])

    def action_xem_khach_hang_phu_trach(self):
        return {
            'name': 'Khách hàng phụ trách',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_phu_trach_id', '=', self.id)],
        }

    def action_xem_du_an_quan_ly(self):
        return {
            'name': 'Dự án quản lý',
            'type': 'ir.actions.act_window',
            'res_model': 'du_an',
            'view_mode': 'tree,form',
            'domain': [('nguoi_quan_ly_id', '=', self.id)],
        }
