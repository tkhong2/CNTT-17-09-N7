# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class KhachHangAssignOwnerWizard(models.TransientModel):
    _name = 'khach_hang_assign_owner_wizard'
    _description = 'Wizard phân công phụ trách khách hàng'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên phụ trách', required=True)
    overwrite_existing = fields.Boolean(string='Ghi đè người phụ trách hiện tại', default=False)
    selected_count = fields.Integer(string='Số khách hàng đã chọn', readonly=True, default=lambda self: len(self.env.context.get('active_ids', [])))

    def action_assign_owner(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise ValidationError(_('Vui lòng chọn khách hàng cần phân công.'))

        selected_records = self.env['khach_hang'].browse(active_ids).filtered('active')
        if not selected_records:
            raise ValidationError(_('Không có khách hàng hợp lệ để phân công.'))

        if self.overwrite_existing:
            target_records = selected_records
        else:
            target_records = selected_records.filtered(lambda rec: not rec.nhan_vien_phu_trach_id)

        if not target_records:
            raise ValidationError(_('Không có khách hàng phù hợp để cập nhật. Hãy bật tùy chọn ghi đè nếu cần.'))

        target_records.write({'nhan_vien_phu_trach_id': self.nhan_vien_id.id})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Phân công thành công'),
                'message': _('Đã cập nhật %s khách hàng.') % len(target_records),
                'type': 'success',
                'sticky': False,
            },
        }
