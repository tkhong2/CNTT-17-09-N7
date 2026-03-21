# -*- coding: utf-8 -*-

from odoo import api, fields, models


class NhanSuDashboard(models.Model):
    _name = 'nhan_su_dashboard'
    _description = 'Dashboard KPI Nhân sự'
    _rec_name = 'ten_bang'

    ten_bang = fields.Char(string='Tên bảng', required=True, default='Dashboard KPI Nhân sự')

    tong_nhan_vien_active = fields.Integer(string='Nhân viên đang làm việc', compute='_compute_kpis')
    tong_bang_luong_da_duyet = fields.Integer(string='Bảng lương đã duyệt', compute='_compute_kpis')
    luong_thang_hien_tai = fields.Float(string='Tổng lương tháng hiện tại', compute='_compute_kpis')
    luong_thang_truoc = fields.Float(string='Tổng lương tháng trước', compute='_compute_kpis')
    payroll_variance = fields.Float(string='Payroll variance', compute='_compute_kpis')
    payroll_variance_rate = fields.Float(string='Payroll variance (%)', compute='_compute_kpis')

    @api.depends('ten_bang')
    def _compute_kpis(self):
        NhanVien = self.env['nhan_vien']
        BangLuong = self.env['tinh_luong']
        approved_states = ['da_duyet', 'da_thanh_toan']

        for record in self:
            record.tong_nhan_vien_active = NhanVien.search_count([('trang_thai', '=', 'active')])
            record.tong_bang_luong_da_duyet = BangLuong.search_count([('trang_thai', 'in', approved_states)])

            payrolls = BangLuong.search([
                ('trang_thai', 'in', approved_states),
                ('thang_nam', '!=', False),
            ], order='thang_nam desc', limit=2)

            current_total = payrolls[0].tong_thuc_linh if payrolls else 0.0
            previous_total = payrolls[1].tong_thuc_linh if len(payrolls) > 1 else 0.0
            variance = current_total - previous_total

            record.luong_thang_hien_tai = current_total
            record.luong_thang_truoc = previous_total
            record.payroll_variance = variance
            record.payroll_variance_rate = (variance / previous_total) if previous_total else 0.0

    def action_xem_bang_luong_da_duyet(self):
        self.ensure_one()
        return {
            'name': 'Bảng lương đã duyệt',
            'type': 'ir.actions.act_window',
            'res_model': 'tinh_luong',
            'view_mode': 'tree,form',
            'domain': [('trang_thai', 'in', ['da_duyet', 'da_thanh_toan'])],
        }
