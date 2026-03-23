# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrWorkHistory(models.Model):
    """
    Quá trình công tác của nhân viên.
    Constraint: date_end > date_start.
    Sorting: _order = date_start desc (việc gần nhất lên đầu).
    """
    _name        = 'hr.work.history'
    _description = 'Quá trình công tác'
    _order       = 'date_start desc, id desc'

    company_name = fields.Char(string='Tên công ty/tổ chức', required=True)
    position     = fields.Char(string='Chức danh / Vị trí',  required=True)
    date_start   = fields.Date(string='Ngày bắt đầu',        required=True)
    date_end     = fields.Date(string='Ngày kết thúc',
                               help='Để trống nếu đây là công việc hiện tại')
    mo_ta        = fields.Text(string='Mô tả công việc')
    employee_id  = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='cascade'
    )

    @api.constrains('date_start', 'date_end')
    def _check_date_range(self):
        for rec in self:
            if rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(
                    _('Ngày kết thúc không được nhỏ hơn ngày bắt đầu!')
                )
