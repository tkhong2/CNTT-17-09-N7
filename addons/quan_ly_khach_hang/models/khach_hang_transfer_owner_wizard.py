# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class KhachHangTransferOwnerWizard(models.TransientModel):
    _name = 'khach_hang_transfer_owner_wizard'
    _description = 'Wizard chuyển giao khách hàng'

    transfer_template_id = fields.Many2one('khach_hang_transfer_template', string='Mẫu chuyển giao')
    source_nhan_vien_id = fields.Many2one('nhan_vien', string='Từ nhân viên', required=True)
    target_nhan_vien_id = fields.Many2one('nhan_vien', string='Sang nhân viên', required=True)
    trang_thai_hop_tac = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('dang_hop_tac', 'Đang hợp tác'),
        ('tam_ngung', 'Tạm ngưng'),
        ('ngung_hop_tac', 'Ngừng hợp tác'),
    ], string='Lọc theo trạng thái')
    only_overdue = fields.Boolean(string='Chỉ khách hàng có follow-up quá hạn', default=False)
    only_silent = fields.Boolean(string='Chỉ khách hàng im lặng quá N ngày', default=False)
    silent_days = fields.Integer(string='Số ngày im lặng', default=14)
    save_template_name = fields.Char(string='Lưu thành mẫu mới')
    selected_count = fields.Integer(string='Số khách hàng đã chọn', readonly=True, default=lambda self: len(self.env.context.get('active_ids', [])))
    preview_count = fields.Integer(string='Số khách hàng sẽ chuyển', compute='_compute_preview_count')

    @api.onchange('transfer_template_id')
    def _onchange_transfer_template_id(self):
        template = self.transfer_template_id
        if not template:
            return
        self.trang_thai_hop_tac = template.trang_thai_hop_tac
        self.only_overdue = template.only_overdue
        self.only_silent = template.only_silent
        self.silent_days = template.silent_days or 14

    @api.depends('source_nhan_vien_id', 'trang_thai_hop_tac', 'only_overdue', 'only_silent', 'silent_days')
    def _compute_preview_count(self):
        for wizard in self:
            if not wizard.source_nhan_vien_id:
                wizard.preview_count = 0
                continue
            wizard.preview_count = self.env['khach_hang'].search_count(wizard._build_domain())

    def _build_domain(self):
        self.ensure_one()
        domain = [
            ('active', '=', True),
            ('nhan_vien_phu_trach_id', '=', self.source_nhan_vien_id.id),
        ]

        if self.trang_thai_hop_tac:
            domain.append(('trang_thai_hop_tac', '=', self.trang_thai_hop_tac))

        if self.only_overdue:
            domain += [
                ('tuong_tac_ids.trang_thai', '=', 'planned'),
                ('tuong_tac_ids.hen_lien_he_tiep', '!=', False),
                ('tuong_tac_ids.hen_lien_he_tiep', '<', fields.Datetime.now()),
            ]

        if self.only_silent:
            days = self.silent_days if self.silent_days and self.silent_days > 0 else 14
            threshold = fields.Datetime.now() - timedelta(days=days)
            domain += ['|', ('lan_tuong_tac_cuoi_index', '=', False), ('lan_tuong_tac_cuoi_index', '<', threshold)]

        active_ids = self.env.context.get('active_ids')
        if active_ids:
            domain.append(('id', 'in', active_ids))

        return domain

    def action_transfer(self):
        self.ensure_one()

        if self.source_nhan_vien_id == self.target_nhan_vien_id:
            raise ValidationError(_('Nhân viên nguồn và đích phải khác nhau.'))

        records = self.env['khach_hang'].search(self._build_domain())
        if not records:
            raise ValidationError(_('Không tìm thấy khách hàng phù hợp với điều kiện chuyển giao.'))

        records.write({'nhan_vien_phu_trach_id': self.target_nhan_vien_id.id})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Chuyển giao thành công'),
                'message': _('Đã chuyển %s khách hàng sang %s.') % (len(records), self.target_nhan_vien_id.display_name),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_save_as_template(self):
        self.ensure_one()

        template_name = (self.save_template_name or '').strip()
        if not template_name:
            raise ValidationError(_('Vui lòng nhập tên mẫu trước khi lưu.'))

        existing = self.env['khach_hang_transfer_template'].search([('name', '=', template_name)], limit=1)
        values = {
            'name': template_name,
            'trang_thai_hop_tac': self.trang_thai_hop_tac,
            'only_overdue': self.only_overdue,
            'only_silent': self.only_silent,
            'silent_days': self.silent_days if self.silent_days and self.silent_days > 0 else 14,
        }

        if existing:
            existing.write(values)
            template = existing
            message = _('Đã cập nhật mẫu chuyển giao: %s') % template.name
        else:
            template = self.env['khach_hang_transfer_template'].create(values)
            message = _('Đã tạo mẫu chuyển giao mới: %s') % template.name

        self.transfer_template_id = template

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Lưu mẫu thành công'),
                'message': message,
                'type': 'success',
                'sticky': False,
            },
        }
