# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên liên kết',
        compute='_compute_nhan_vien_id',
        compute_sudo=True,
    )

    @api.depends('email', 'login')
    def _compute_nhan_vien_id(self):
        NhanVien = self.env['nhan_vien']
        for user in self:
            employee = False
            if user.email:
                employee = NhanVien.search([('email', '=', user.email)], limit=1)
            if not employee and user.login:
                employee = NhanVien.search([('email', '=', user.login)], limit=1)
            user.nhan_vien_id = employee
