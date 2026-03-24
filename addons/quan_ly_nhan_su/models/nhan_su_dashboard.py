# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date


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

    # Dữ liệu cho biểu đồ — JSON string để JS đọc
    chart_luong_labels = fields.Char(string='Chart Labels', compute='_compute_kpis')
    chart_luong_data   = fields.Char(string='Chart Data',   compute='_compute_kpis')
    chart_pb_labels    = fields.Char(string='Phòng ban Labels', compute='_compute_kpis')
    chart_pb_data      = fields.Char(string='Phòng ban Data',   compute='_compute_kpis')

    @api.depends('ten_bang')
    def _compute_kpis(self):
        NhanVien  = self.env['nhan_vien']
        BangLuong = self.env['tinh_luong']
        PhongBan  = self.env['phong_ban']
        approved  = ['da_duyet', 'da_thanh_toan']

        for record in self:
            # ── KPI cơ bản ──────────────────────────────────────
            record.tong_nhan_vien_active    = NhanVien.search_count([('trang_thai', '=', 'active')])
            record.tong_bang_luong_da_duyet = BangLuong.search_count([('trang_thai', 'in', approved)])

            payrolls = BangLuong.search(
                [('trang_thai', 'in', approved), ('thang_nam', '!=', False)],
                order='thang_nam desc', limit=2
            )
            cur  = payrolls[0].tong_thuc_linh if payrolls else 0.0
            prev = payrolls[1].tong_thuc_linh if len(payrolls) > 1 else 0.0
            var  = cur - prev

            record.luong_thang_hien_tai  = cur
            record.luong_thang_truoc     = prev
            record.payroll_variance      = var
            record.payroll_variance_rate = (var / prev) if prev else 0.0

            # ── Biểu đồ lương 12 tháng (dữ liệu thật) ──────────
            all_payrolls = BangLuong.search(
                [('trang_thai', 'in', approved), ('thang_nam', '!=', False)],
                order='thang_nam asc', limit=12
            )
            if all_payrolls:
                labels = [p.thang_nam for p in all_payrolls]
                data   = [round(p.tong_thuc_linh / 1_000_000, 2) for p in all_payrolls]
            else:
                # Placeholder khi chưa có dữ liệu
                today = date.today()
                labels = []
                data   = []
                for i in range(6, -1, -1):
                    m = (today.month - i - 1) % 12 + 1
                    y = today.year - ((today.month - i - 1) // 12 + 1 if today.month - i <= 0 else 0)
                    labels.append(f'{y}-{m:02d}')
                    data.append(0)

            record.chart_luong_labels = ','.join(str(l) for l in labels)
            record.chart_luong_data   = ','.join(str(d) for d in data)

            # ── Biểu đồ cơ cấu phòng ban (dữ liệu thật) ────────
            phong_bans = PhongBan.search([])
            pb_labels = []
            pb_data   = []
            for pb in phong_bans:
                cnt = NhanVien.search_count([
                    ('phong_ban_id', '=', pb.id),
                    ('trang_thai', '=', 'active'),
                ])
                if cnt > 0:
                    pb_labels.append(pb.ten_phong_ban)
                    pb_data.append(cnt)

            if not pb_data:
                pb_labels = ['Chưa có dữ liệu']
                pb_data   = [1]

            record.chart_pb_labels = '|'.join(pb_labels)
            record.chart_pb_data   = ','.join(str(x) for x in pb_data)

    def action_xem_bang_luong_da_duyet(self):
        self.ensure_one()
        return {
            'name': 'Bảng lương đã duyệt',
            'type': 'ir.actions.act_window',
            'res_model': 'tinh_luong',
            'view_mode': 'tree,form',
            'domain': [('trang_thai', 'in', ['da_duyet', 'da_thanh_toan'])],
        }
