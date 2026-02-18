# -*- coding: utf-8 -*-

from odoo import api, fields, models


class NhanVienInherit(models.Model):
    _inherit = 'nhan_vien'

    user_id = fields.Many2one('res.users', string='Tài khoản hệ thống', tracking=True)
    khach_hang_phu_trach_ids = fields.One2many('khach_hang', 'nhan_vien_phu_trach_id', string='Khách hàng phụ trách')
    du_an_quan_ly_ids = fields.One2many('du_an', 'nguoi_quan_ly_id', string='Dự án quản lý')

    so_khach_hang_phu_trach = fields.Integer(string='Số khách hàng phụ trách', compute='_compute_lien_ket_stats')
    so_du_an_quan_ly = fields.Integer(string='Số dự án quản lý', compute='_compute_lien_ket_stats')

    @api.depends('khach_hang_phu_trach_ids', 'du_an_quan_ly_ids')
    def _compute_lien_ket_stats(self):
        for record in self:
            record.so_khach_hang_phu_trach = len(record.khach_hang_phu_trach_ids)
            record.so_du_an_quan_ly = len(record.du_an_quan_ly_ids)

    def action_xem_khach_hang_phu_trach(self):
        self.ensure_one()
        return {
            'name': 'Khách hàng phụ trách',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_phu_trach_id', '=', self.id)],
        }

    def action_xem_du_an_quan_ly(self):
        self.ensure_one()
        return {
            'name': 'Dự án quản lý',
            'type': 'ir.actions.act_window',
            'res_model': 'du_an',
            'view_mode': 'kanban,tree,form',
            'domain': [('nguoi_quan_ly_id', '=', self.id)],
        }

    def write(self, vals):
        old_state = {record.id: record.trang_thai for record in self}
        result = super().write(vals)

        if 'trang_thai' in vals:
            for record in self:
                if old_state.get(record.id) != record.trang_thai and record.trang_thai in ['leave', 'suspended'] and record.quan_ly_id:
                    self._auto_reassign_when_employee_inactive(record)
        return result

    def _auto_reassign_when_employee_inactive(self, employee):
        replacement = employee.quan_ly_id

        khach_hang_records = self.env['khach_hang'].search([
            ('nhan_vien_phu_trach_id', '=', employee.id),
        ])
        if khach_hang_records:
            khach_hang_records.write({'nhan_vien_phu_trach_id': replacement.id})

        du_an_records = self.env['du_an'].search([
            ('nguoi_quan_ly_id', '=', employee.id),
            ('trang_thai', 'in', ['chuan_bi', 'dang_thuc_hien', 'tam_dung']),
        ])
        if du_an_records:
            du_an_records.write({'nguoi_quan_ly_id': replacement.id})

        cong_viec_records = self.env['cong_viec'].search([
            ('nguoi_phu_trach_id', '=', employee.id),
            ('trang_thai', 'in', ['moi', 'dang_thuc_hien', 'tam_dung']),
        ])
        if cong_viec_records:
            cong_viec_records.write({'nguoi_phu_trach_id': replacement.id})
