# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CongViecInherit(models.Model):
    _inherit = 'cong_viec'

    khach_hang_id = fields.Many2one('khach_hang', related='du_an_id.khach_hang_id', string='Khách hàng', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('du_an_id') and not vals.get('nguoi_phu_trach_id'):
                du_an = self.env['du_an'].browse(vals['du_an_id'])
                if du_an.nguoi_quan_ly_id:
                    vals['nguoi_phu_trach_id'] = du_an.nguoi_quan_ly_id.id
        records = super().create(vals_list)
        records._auto_sync_customer_owner_from_task()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._auto_sync_customer_owner_from_task()
        return result

    def _auto_sync_customer_owner_from_task(self):
        for record in self.filtered(lambda r: r.khach_hang_id and r.nguoi_phu_trach_id):
            if not record.khach_hang_id.nhan_vien_phu_trach_id:
                record.khach_hang_id.nhan_vien_phu_trach_id = record.nguoi_phu_trach_id.id
