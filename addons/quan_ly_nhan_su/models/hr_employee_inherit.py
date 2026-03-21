# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

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
    family_ids = fields.One2many('hr.family', 'employee_id', string='Danh sach than nhan')
    work_history_ids = fields.One2many('hr.work.history', 'employee_id', string='Qua trinh cong tac')

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
            record.nhan_vien_custom_id = matched
            record.nhan_vien_custom_count = 1 if matched else 0

    def action_open_nhan_vien_custom(self):
        self.ensure_one()
        action = self.env.ref('quan_ly_nhan_su.action_nhan_vien').sudo().read()[0]
        if self.nhan_vien_custom_id:
            action.update({
                'view_mode': 'form',
                'res_id': self.nhan_vien_custom_id.id,
            })
        else:
            action.update({
                'domain': [('email', '=', self.work_email)] if self.work_email else [],
                'context': {
                    'default_ho_va_ten': self.name,
                    'default_email': self.work_email,
                    'default_dien_thoai': self.mobile_phone or self.work_phone,
                },
            })
        return action
