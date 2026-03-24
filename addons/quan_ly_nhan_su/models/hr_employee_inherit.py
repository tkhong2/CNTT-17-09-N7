# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployeeInherit(models.Model):
    """
    Kế thừa hr.employee (module gốc Odoo) — KHÔNG sửa file gốc.
    Mở rộng thêm các trường nghiệp vụ theo đề bài.
    """
    _inherit = 'hr.employee'

    # ── Phần chung bắt buộc (Đề bài Mức 1 - Giai đoạn 1) ──
    que_quan    = fields.Char(string='Quê quán')
    so_cccd     = fields.Char(string='Số CCCD', required=True, default='')
    ngay_cap    = fields.Date(string='Ngày cấp CCCD')
    noi_cap     = fields.Char(string='Nơi cấp CCCD')

    # ── Liên kết ngược module nội bộ ────────────────────────
    nhan_vien_custom_id = fields.Many2one(
        'nhan_vien',
        string='Hồ sơ nhân sự nội bộ',
        compute='_compute_nhan_vien_custom_id',
        compute_sudo=True,
    )
    nhan_vien_custom_count = fields.Integer(
        string='Số hồ sơ nội bộ',
        compute='_compute_nhan_vien_custom_id',
        compute_sudo=True,
    )

    # ── Gia đình & Quá trình công tác ────────────────────────
    family_ids = fields.One2many(
        'hr.family', 'employee_id',
        string='Danh sách thân nhân'
    )
    work_history_ids = fields.One2many(
        'hr.work.history', 'employee_id',
        string='Quá trình công tác'
    )

    # ── Validation (Mức 1 - bắt buộc) ───────────────────────
    @api.constrains('birthday')
    def _check_birthday(self):
        for rec in self:
            if rec.birthday and rec.birthday > fields.Date.today():
                raise ValidationError(
                    _('Ngày sinh không được lớn hơn ngày hiện tại!')
                )

    @api.constrains('so_cccd')
    def _check_so_cccd(self):
        for rec in self:
            if rec.so_cccd and not rec.so_cccd.isdigit():
                raise ValidationError(_('Số CCCD chỉ được chứa chữ số!'))
            if rec.so_cccd and len(rec.so_cccd) not in (9, 12):
                raise ValidationError(_('Số CCCD phải có 9 hoặc 12 chữ số!'))

    # ── Compute liên kết module nội bộ ───────────────────────
    @api.depends('work_email', 'name', 'mobile_phone', 'work_phone')
    def _compute_nhan_vien_custom_id(self):
        NhanVien = self.env['nhan_vien']
        for record in self:
            domain = []
            if record.work_email:
                domain = [('email', '=', record.work_email)]
            elif record.mobile_phone:
                domain = [('dien_thoai', '=', record.mobile_phone)]
            elif record.work_phone:
                domain = [('dien_thoai', '=', record.work_phone)]
            matched = NhanVien.search(domain, limit=1) if domain else False
            record.nhan_vien_custom_id    = matched
            record.nhan_vien_custom_count = 1 if matched else 0

    def action_open_nhan_vien_custom(self):
        self.ensure_one()
        action = self.env.ref('quan_ly_nhan_su.action_nhan_vien').sudo().read()[0]
        if self.nhan_vien_custom_id:
            action.update({'view_mode': 'form', 'res_id': self.nhan_vien_custom_id.id})
        else:
            action.update({
                'domain': [('email', '=', self.work_email)] if self.work_email else [],
                'context': {
                    'default_ho_va_ten':  self.name,
                    'default_email':      self.work_email,
                    'default_dien_thoai': self.mobile_phone or self.work_phone,
                },
            })
        return action
