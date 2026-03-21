# -*- coding: utf-8 -*-

from datetime import date

from odoo import api, fields, models


class HrFamily(models.Model):
    _name = 'hr.family'
    _description = 'Than nhan nhan vien'
    _order = 'birth_date desc, id desc'

    name = fields.Char(string='Ten than nhan', required=True)
    relationship = fields.Selection([
        ('vo', 'Vo'),
        ('chong', 'Chong'),
        ('con', 'Con'),
        ('bo', 'Bo'),
        ('me', 'Me'),
        ('khac', 'Khac'),
    ], string='Moi quan he', required=True)
    birth_date = fields.Date(string='Ngay sinh')
    age = fields.Integer(string='Tuoi', compute='_compute_age_and_dependent', store=True)
    is_dependent = fields.Boolean(string='Nguoi phu thuoc', compute='_compute_age_and_dependent', store=True)
    employee_id = fields.Many2one('hr.employee', string='Nhan vien', required=True, ondelete='cascade')

    @api.depends('birth_date', 'relationship')
    def _compute_age_and_dependent(self):
        today = date.today()
        for record in self:
            age = 0
            if record.birth_date:
                age = today.year - record.birth_date.year - ((today.month, today.day) < (record.birth_date.month, record.birth_date.day))
            record.age = age
            record.is_dependent = bool(record.relationship == 'con' and age < 18)
