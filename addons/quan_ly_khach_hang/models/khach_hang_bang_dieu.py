# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api


class KhachHangDashboard(models.Model):
    _name = 'khach_hang_dashboard'
    _description = 'Dashboard KPI Khách hàng'

    ten_bang = fields.Char(string='Tên bảng', default='Dashboard KPI Khách hàng')

    tong_khach_hang = fields.Integer(string='Tổng khách hàng', compute='_compute_kpi')
    khach_hang_moi_7_ngay = fields.Integer(string='KH mới 7 ngày', compute='_compute_kpi')
    khach_hang_dang_hop_tac = fields.Integer(string='Đang hợp tác', compute='_compute_kpi')
    khach_hang_chua_phan_cong = fields.Integer(string='Chưa phân công', compute='_compute_kpi')
    khach_hang_im_lang_14_ngay = fields.Integer(string='Im lặng >14 ngày', compute='_compute_kpi')
    khach_hang_trung_lien_he = fields.Integer(string='Trùng liên hệ', compute='_compute_kpi')
    de_xuat_gop_cho_duyet = fields.Integer(string='Đề xuất gộp', compute='_compute_kpi')
    tong_tuong_tac = fields.Integer(string='Tổng tương tác', compute='_compute_kpi')
    tuong_tac_chot_hop_dong = fields.Integer(string='Tương tác chốt HĐ', compute='_compute_kpi')
    followup_qua_han = fields.Integer(string='Follow-up quá hạn', compute='_compute_kpi')
    ty_le_chot = fields.Float(string='Tỷ lệ chốt (%)', compute='_compute_kpi', digits=(5, 2))

    @api.depends()
    def _compute_kpi(self):
        KhachHang = self.env['khach_hang']
        TuongTac = self.env['khach_hang_tuong_tac']
        MergeSuggestion = self.env['khach_hang_merge_suggestion'] if 'khach_hang_merge_suggestion' in self.env else None
        today = fields.Date.today()
        seven_days_ago = today - timedelta(days=7)
        fourteen_days_ago = today - timedelta(days=14)

        for rec in self:
            rec.tong_khach_hang = KhachHang.search_count([])
            rec.khach_hang_moi_7_ngay = KhachHang.search_count([('create_date', '>=', seven_days_ago)])
            rec.khach_hang_dang_hop_tac = KhachHang.search_count([('trang_thai_hop_tac', '=', 'dang_hop_tac')])
            rec.khach_hang_chua_phan_cong = KhachHang.search_count([('nhan_vien_phu_trach_id', '=', False)])
            rec.khach_hang_im_lang_14_ngay = KhachHang.search_count([
                '|',
                ('lan_tuong_tac_cuoi_index', '=', False),
                ('lan_tuong_tac_cuoi_index', '<', fourteen_days_ago),
            ])
            rec.khach_hang_trung_lien_he = 0  # simplified
            rec.de_xuat_gop_cho_duyet = MergeSuggestion.search_count([('state', '=', 'draft')]) if MergeSuggestion else 0
            rec.tong_tuong_tac = TuongTac.search_count([])
            rec.tuong_tac_chot_hop_dong = TuongTac.search_count([('ket_qua', '=', 'chot_hop_dong')])
            rec.followup_qua_han = TuongTac.search_count([
                ('trang_thai', '=', 'planned'),
                ('hen_lien_he_tiep', '<', today),
            ])
            rec.ty_le_chot = (rec.tuong_tac_chot_hop_dong / rec.tong_tuong_tac * 100) if rec.tong_tuong_tac else 0.0

    def action_chay_nhanh_theo_mau(self):
        pass

    def action_tu_dong_phan_cong(self):
        kh_chua_phan_cong = self.env['khach_hang'].search([('nhan_vien_phu_trach_id', '=', False)])
        nhan_vien = self.env['nhan_vien'].search([], limit=1)
        if nhan_vien:
            kh_chua_phan_cong.write({'nhan_vien_phu_trach_id': nhan_vien.id})

    def action_gui_bao_cao_ngay(self):
        pass

    def action_gui_canh_bao_backlog(self):
        pass

    def action_xem_de_xuat_gop(self):
        return {
            'name': 'Đề xuất gộp khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_merge_suggestion',
            'view_mode': 'tree,form',
            'domain': [('state', '=', 'draft')],
        }

    def action_xem_khach_hang_chua_phan_cong(self):
        return {
            'name': 'Khách hàng chưa phân công',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_phu_trach_id', '=', False)],
        }

    def action_xem_khach_hang_im_lang(self):
        today = fields.Date.today()
        fourteen_days_ago = today - timedelta(days=14)
        return {
            'name': 'Khách hàng im lặng >14 ngày',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': ['|', ('lan_tuong_tac_cuoi_index', '=', False), ('lan_tuong_tac_cuoi_index', '<', fourteen_days_ago)],
        }

    def action_xem_khach_hang_trung_lien_he(self):
        return {
            'name': 'Khách hàng trùng liên hệ',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
        }

    def action_xem_khach_hang_moi(self):
        return {
            'name': 'Khách hàng mới 7 ngày',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('create_date', '>=', fields.Date.today() - timedelta(days=7))],
        }

    def action_xem_khach_hang_dang_hop_tac(self):
        return {
            'name': 'Khách hàng đang hợp tác',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('trang_thai_hop_tac', '=', 'dang_hop_tac')],
        }

    def action_xem_tuong_tac_chot(self):
        return {
            'name': 'Tương tác chốt hợp đồng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [('ket_qua', '=', 'chot_hop_dong')],
        }

    def action_xem_followup_qua_han(self):
        return {
            'name': 'Follow-up quá hạn',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [('trang_thai', '=', 'planned'), ('hen_lien_he_tiep', '<', fields.Date.today())],
        }
