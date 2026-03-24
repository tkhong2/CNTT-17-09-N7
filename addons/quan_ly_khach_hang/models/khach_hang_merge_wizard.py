# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class KhachHangMergeWizard(models.TransientModel):
    _name = 'khach_hang_merge_wizard'
    _description = 'Wizard gộp khách hàng'

    primary_khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng chính', required=True)
    duplicate_khach_hang_ids = fields.Many2many('khach_hang', string='Khách hàng cần gộp', required=True)

    def action_merge(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids or len(active_ids) < 2:
            raise ValidationError(_('Vui lòng chọn ít nhất 2 khách hàng trong danh sách để gộp.'))

        selected_records = self.env['khach_hang'].browse(active_ids).filtered('active')
        if self.primary_khach_hang_id not in selected_records:
            raise ValidationError(_('Khách hàng chính phải nằm trong danh sách đã chọn.'))

        duplicates = self.duplicate_khach_hang_ids.filtered(lambda rec: rec in selected_records and rec.id != self.primary_khach_hang_id.id)
        if not duplicates:
            raise ValidationError(_('Vui lòng chọn ít nhất 1 khách hàng cần gộp.'))

        primary_email = self.primary_khach_hang_id.email_normalized
        primary_phone = self.primary_khach_hang_id.phone_normalized
        if not primary_email and not primary_phone:
            raise ValidationError(_('Khách hàng chính phải có email hoặc số điện thoại để đối chiếu gộp.'))

        invalid_duplicates = duplicates.filtered(
            lambda rec: not (
                (primary_email and rec.email_normalized and rec.email_normalized == primary_email)
                or (primary_phone and rec.phone_normalized and rec.phone_normalized == primary_phone)
            )
        )
        if invalid_duplicates:
            raise ValidationError(
                _('Chỉ được gộp các khách hàng có cùng email hoặc cùng số điện thoại với khách hàng chính. Bản ghi không hợp lệ: %s')
                % ', '.join(invalid_duplicates.mapped('ten_khach_hang'))
            )

        merged_count = self.primary_khach_hang_id._merge_duplicate_records(duplicates)
        self.primary_khach_hang_id.message_post(body=_('Đã gộp hàng loạt %s khách hàng bằng wizard.') % merged_count)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'res_id': self.primary_khach_hang_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
