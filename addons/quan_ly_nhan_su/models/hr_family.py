# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrFamily(models.Model):
    """
    Thân nhân nhân viên — One2many từ hr.employee.
    Tự động tính tuổi và đánh dấu người phụ thuộc (con < 18 tuổi).
    """
    _name        = 'hr.family'
    _description = 'Thân nhân nhân viên'
    _order       = 'birth_date desc, id desc'

    name = fields.Char(string='Họ tên thân nhân', required=True)

    relationship = fields.Selection([
        ('vo',    'Vợ'),
        ('chong', 'Chồng'),
        ('con',   'Con'),
        ('bo',    'Bố'),
        ('me',    'Mẹ'),
        ('anh_chi_em', 'Anh/Chị/Em'),
        ('khac',  'Khác'),
    ], string='Mối quan hệ', required=True)

    birth_date    = fields.Date(string='Ngày sinh')
    age           = fields.Integer(string='Tuổi', compute='_compute_age_and_dependent', store=True)
    is_dependent  = fields.Boolean(
        string='Người phụ thuộc',
        compute='_compute_age_and_dependent',
        store=True,
        help='Tự động tick nếu là Con và dưới 18 tuổi'
    )
    employee_id   = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='cascade'
    )

    # ── Logic: tự động tính tuổi & is_dependent ──────────────
    @api.depends('birth_date', 'relationship')
    def _compute_age_and_dependent(self):
        today = date.today()
        for rec in self:
            age = 0
            if rec.birth_date:
                age = (today.year - rec.birth_date.year
                       - ((today.month, today.day) < (rec.birth_date.month, rec.birth_date.day)))
            rec.age          = age
            # Con dưới 18 → tự động người phụ thuộc
            rec.is_dependent = bool(rec.relationship == 'con' and age < 18)

    @api.constrains('birth_date')
    def _check_birth_date(self):
        for rec in self:
            if rec.birth_date and rec.birth_date > date.today():
                raise ValidationError(_('Ngày sinh thân nhân không được lớn hơn ngày hiện tại!'))
