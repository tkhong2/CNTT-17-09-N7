# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class KhachHangMergeSuggestion(models.Model):
    _name = 'khach_hang_merge_suggestion'
    _description = 'Đề xuất gộp khách hàng'
    _order = 'create_date desc, id desc'

    primary_khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng chính', required=True, ondelete='cascade')
    duplicate_khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng trùng', required=True, ondelete='cascade')
    reason = fields.Selection([
        ('same_email', 'Trùng email'),
        ('same_phone', 'Trùng điện thoại'),
    ], string='Lý do', required=True)
    match_value = fields.Char(string='Giá trị trùng')
    state = fields.Selection([
        ('draft', 'Chờ xử lý'),
        ('applied', 'Đã áp dụng'),
        ('rejected', 'Đã bỏ qua'),
    ], string='Trạng thái', default='draft', required=True)

    _sql_constraints = [
        ('pair_unique', 'unique(primary_khach_hang_id, duplicate_khach_hang_id)', 'Cặp đề xuất gộp đã tồn tại.'),
    ]

    def action_apply(self):
        for record in self:
            if record.state != 'draft':
                continue
            if not record.primary_khach_hang_id.active or not record.duplicate_khach_hang_id.active:
                raise ValidationError(_('Một trong hai khách hàng không còn hoạt động, không thể áp dụng đề xuất.'))
            if record.primary_khach_hang_id == record.duplicate_khach_hang_id:
                raise ValidationError(_('Khách hàng chính và khách hàng trùng không được trùng nhau.'))

            merged = record.primary_khach_hang_id._merge_duplicate_records(record.duplicate_khach_hang_id)
            if merged:
                record.state = 'applied'

    def action_reject(self):
        self.filtered(lambda rec: rec.state == 'draft').write({'state': 'rejected'})
