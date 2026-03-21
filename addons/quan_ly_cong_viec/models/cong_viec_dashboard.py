# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CongViecDashboard(models.Model):
    _name = 'cong_viec_dashboard'
    _description = 'Dashboard KPI Công việc'
    _rec_name = 'ten_bang'

    ten_bang = fields.Char(string='Tên bảng', required=True, default='Dashboard KPI Công việc')

    tong_cong_viec_active = fields.Integer(string='Công việc đang mở', compute='_compute_kpis')
    tong_cong_viec_bi_chan = fields.Integer(string='Công việc bị chặn', compute='_compute_kpis')
    blocked_task_ratio = fields.Float(string='Blocked task ratio (%)', compute='_compute_kpis')

    @api.depends('ten_bang')
    def _compute_kpis(self):
        CongViec = self.env['cong_viec']
        active_domain = [('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])]

        for record in self:
            total_active = CongViec.search_count(active_domain)
            blocked_active = CongViec.search_count(active_domain + [('bi_chan', '=', True)])
            record.tong_cong_viec_active = total_active
            record.tong_cong_viec_bi_chan = blocked_active
            record.blocked_task_ratio = (blocked_active / total_active) if total_active else 0.0

    def action_xem_cong_viec_bi_chan(self):
        self.ensure_one()
        return {
            'name': 'Công việc bị chặn',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'kanban,tree,form',
            'domain': [
                ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
                ('bi_chan', '=', True),
            ],
        }
