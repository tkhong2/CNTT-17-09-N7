# -*- coding: utf-8 -*-
from odoo import models, fields, api


class KhachHangMergeWizard(models.TransientModel):
    _name = 'khach_hang_merge_wizard'
    _description = 'Wizard gộp khách hàng'

    primary_khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng giữ lại', required=True)
    duplicate_khach_hang_ids = fields.Many2many(
        'khach_hang', string='Khách hàng cần gộp',
        relation='merge_wizard_khach_hang_rel'
    )

    def action_merge(self):
        for dup in self.duplicate_khach_hang_ids:
            # Chuyển tương tác
            self.env['khach_hang_tuong_tac'].search([('khach_hang_id', '=', dup.id)]).write(
                {'khach_hang_id': self.primary_khach_hang_id.id}
            )
            dup.active = False
        return {'type': 'ir.actions.act_window_close'}


class KhachHangAssignOwnerWizard(models.TransientModel):
    _name = 'khach_hang_assign_owner_wizard'
    _description = 'Wizard phân công nhân viên phụ trách'

    selected_count = fields.Integer(string='Số khách hàng đã chọn', readonly=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên phụ trách', required=True)
    overwrite_existing = fields.Boolean(string='Ghi đè phân công hiện tại', default=False)

    def action_assign_owner(self):
        active_ids = self.env.context.get('active_ids', [])
        domain = [('id', 'in', active_ids)]
        if not self.overwrite_existing:
            domain.append(('nhan_vien_phu_trach_id', '=', False))
        self.env['khach_hang'].search(domain).write({'nhan_vien_phu_trach_id': self.nhan_vien_id.id})
        return {'type': 'ir.actions.act_window_close'}


class KhachHangTransferOwnerWizard(models.TransientModel):
    _name = 'khach_hang_transfer_owner_wizard'
    _description = 'Wizard chuyển giao khách hàng'

    transfer_template_id = fields.Many2one('khach_hang_transfer_template', string='Mẫu thao tác')
    save_template_name = fields.Char(string='Lưu thành mẫu')
    selected_count = fields.Integer(string='Số khách hàng', readonly=True, compute='_compute_preview_count')
    source_nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên nguồn')
    target_nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên đích', required=True)
    trang_thai_hop_tac = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('dang_hop_tac', 'Đang hợp tác'),
        ('tam_ngung', 'Tạm ngưng'),
        ('ngung_hop_tac', 'Ngưng hợp tác'),
    ], string='Lọc trạng thái hợp tác')
    only_overdue = fields.Boolean(string='Chỉ quá hạn')
    only_silent = fields.Boolean(string='Chỉ im lặng')
    silent_days = fields.Integer(string='Số ngày im lặng', default=14)
    preview_count = fields.Integer(string='Số KH sẽ chuyển', compute='_compute_preview_count')

    @api.depends('source_nhan_vien_id', 'trang_thai_hop_tac', 'only_overdue', 'only_silent', 'silent_days')
    def _compute_preview_count(self):
        for rec in self:
            rec.preview_count = len(rec._get_target_khach_hang())
            rec.selected_count = rec.preview_count

    def _get_target_khach_hang(self):
        domain = []
        if self.source_nhan_vien_id:
            domain.append(('nhan_vien_phu_trach_id', '=', self.source_nhan_vien_id.id))
        if self.trang_thai_hop_tac:
            domain.append(('trang_thai_hop_tac', '=', self.trang_thai_hop_tac))
        if self.only_silent and self.silent_days:
            from datetime import timedelta
            cutoff = fields.Date.today() - timedelta(days=self.silent_days)
            domain += ['|', ('lan_tuong_tac_cuoi_index', '=', False), ('lan_tuong_tac_cuoi_index', '<', cutoff)]
        return self.env['khach_hang'].search(domain)

    def action_save_as_template(self):
        if self.save_template_name:
            self.env['khach_hang_transfer_template'].create({
                'name': self.save_template_name,
                'trang_thai_hop_tac': self.trang_thai_hop_tac,
                'only_overdue': self.only_overdue,
                'only_silent': self.only_silent,
                'silent_days': self.silent_days,
            })

    def action_transfer(self):
        self._get_target_khach_hang().write({'nhan_vien_phu_trach_id': self.target_nhan_vien_id.id})
        return {'type': 'ir.actions.act_window_close'}


class KhachHangTransferTemplate(models.Model):
    _name = 'khach_hang_transfer_template'
    _description = 'Mẫu chuyển giao khách hàng'

    name = fields.Char(string='Tên mẫu', required=True)
    active = fields.Boolean(string='Đang dùng', default=True)
    trang_thai_hop_tac = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('dang_hop_tac', 'Đang hợp tác'),
        ('tam_ngung', 'Tạm ngưng'),
        ('ngung_hop_tac', 'Ngưng hợp tác'),
    ], string='Lọc trạng thái hợp tác')
    only_overdue = fields.Boolean(string='Chỉ quá hạn')
    only_silent = fields.Boolean(string='Chỉ im lặng')
    silent_days = fields.Integer(string='Số ngày im lặng', default=14)


class KhachHangMergeSuggestion(models.Model):
    _name = 'khach_hang_merge_suggestion'
    _description = 'Đề xuất gộp khách hàng'

    primary_khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng chính', required=True)
    duplicate_khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng trùng', required=True)
    reason = fields.Char(string='Lý do đề xuất')
    match_value = fields.Char(string='Giá trị trùng')
    state = fields.Selection([
        ('draft', 'Chờ duyệt'),
        ('applied', 'Đã áp dụng'),
        ('rejected', 'Đã bỏ qua'),
    ], string='Trạng thái', default='draft')

    def action_apply(self):
        for rec in self:
            dup = rec.duplicate_khach_hang_id
            self.env['khach_hang_tuong_tac'].search([('khach_hang_id', '=', dup.id)]).write(
                {'khach_hang_id': rec.primary_khach_hang_id.id}
            )
            dup.active = False
            rec.state = 'applied'

    def action_reject(self):
        self.write({'state': 'rejected'})
