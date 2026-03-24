# -*- coding: utf-8 -*-

from odoo import _, fields, models


class NhanVienInheritCongViec(models.Model):
    _inherit = 'nhan_vien'

    cong_viec_thuc_hien_ids = fields.One2many('cong_viec', 'nguoi_phu_trach_id', string='Cong viec thuc hien')
    so_cong_viec_thuc_hien = fields.Integer(string='So cong viec thuc hien', compute='_compute_so_cong_viec_thuc_hien')

    def _compute_so_cong_viec_thuc_hien(self):
        for record in self:
            record.so_cong_viec_thuc_hien = len(record.cong_viec_thuc_hien_ids)

    def action_xem_cong_viec_thuc_hien(self):
        self.ensure_one()
        return {
            'name': _('Cong viec nhan vien thuc hien'),
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'kanban,tree,form',
            'domain': [('nguoi_phu_trach_id', '=', self.id)],
        }
