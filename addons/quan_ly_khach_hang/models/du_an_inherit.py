# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DuAnInherit(models.Model):
    _inherit = 'du_an'

    khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('khach_hang_id') and not vals.get('nguoi_quan_ly_id'):
                khach_hang = self.env['khach_hang'].browse(vals['khach_hang_id'])
                if khach_hang.nhan_vien_phu_trach_id:
                    vals['nguoi_quan_ly_id'] = khach_hang.nhan_vien_phu_trach_id.id
        records = super().create(vals_list)
        records._auto_update_khach_hang_status()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._auto_update_khach_hang_status()
        return result

    def _auto_update_khach_hang_status(self):
        for record in self.filtered('khach_hang_id'):
            khach_hang = record.khach_hang_id
            active_projects = khach_hang.du_an_ids.filtered(lambda p: p.trang_thai in ['chuan_bi', 'dang_thuc_hien', 'tam_dung'])
            if active_projects:
                if khach_hang.trang_thai_hop_tac != 'dang_hop_tac':
                    khach_hang.trang_thai_hop_tac = 'dang_hop_tac'
            elif khach_hang.du_an_ids:
                if khach_hang.trang_thai_hop_tac in ['dang_hop_tac', 'tiem_nang']:
                    khach_hang.trang_thai_hop_tac = 'tam_ngung'
