# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrWorkHistory(models.Model):
    _name = 'hr.work.history'
    _description = 'Qua trinh cong tac'
    _order = 'date_start desc, id desc'

    company_name = fields.Char(string='Ten cong ty', required=True)
    position = fields.Char(string='Chuc danh', required=True)
    date_start = fields.Date(string='Ngay bat dau', required=True)
    date_end = fields.Date(string='Ngay ket thuc')
    employee_id = fields.Many2one('hr.employee', string='Nhan vien', required=True, ondelete='cascade')

    @api.constrains('date_start', 'date_end')
    def _check_date_range(self):
        for record in self:
            if record.date_end and record.date_end < record.date_start:
                raise ValidationError(_('Ngay ket thuc khong duoc nho hon ngay bat dau!'))
