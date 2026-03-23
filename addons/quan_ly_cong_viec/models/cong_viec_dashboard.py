# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CongViecDashboard(models.Model):
    _name = 'cong_viec_dashboard'
    _description = 'Dashboard KPI Công việc'
    _rec_name = 'ten_bang'

    ten_bang = fields.Char(string='Tên bảng', required=True, default='Dashboard KPI Công việc')

    tong_cong_viec_active = fields.Integer(string='Công việc đang mở', compute='_compute_kpis')
    tong_cong_viec_qua_han = fields.Integer(string='Công việc quá hạn', compute='_compute_kpis')
    tong_cong_viec_hoan_thanh = fields.Integer(string='Công việc hoàn thành', compute='_compute_kpis')
    blocked_task_ratio = fields.Float(string='Tỷ lệ quá hạn (%)', compute='_compute_kpis')

    @api.depends('ten_bang')
    def _compute_kpis(self):
        CongViec = self.env['cong_viec']
        active_domain = [('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])]
        today = fields.Date.today()

        for record in self:
            total_active = CongViec.search_count(active_domain)
            overdue = CongViec.search_count(active_domain + [('ngay_ket_thuc', '<', today), ('ngay_ket_thuc', '!=', False)])
            done = CongViec.search_count([('trang_thai', '=', 'hoan_thanh')])
            record.tong_cong_viec_active = total_active
            record.tong_cong_viec_qua_han = overdue
            record.tong_cong_viec_hoan_thanh = done
            record.blocked_task_ratio = (overdue / total_active * 100) if total_active else 0.0

    def action_xem_cong_viec_qua_han(self):
        self.ensure_one()
        return {
            'name': 'Công việc quá hạn',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'kanban,tree,form',
            'domain': [
                ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
                ('ngay_ket_thuc', '<', fields.Date.today()),
                ('ngay_ket_thuc', '!=', False),
            ],
        }