# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ChucVu(models.Model):
    _name = "chuc_vu"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quản lý chức vụ"
    _rec_name = "ten_chuc_vu"

    ma_chuc_vu = fields.Char(string="Mã chức vụ", required=True, index=True)
    ten_chuc_vu = fields.Char(string="Tên chức vụ", required=True, tracking=True)
    mo_ta = fields.Text(string="Mô tả")
    muc_luong_co_ban = fields.Float(string="Mức lương cơ bản", default=0.0)
    
    # Các mối quan hệ
    nhan_vien_ids = fields.One2many('nhan_vien', 'chuc_vu_id', string="Nhân viên")
    
    # Ràng buộc SQL
    _sql_constraints = [
        ('ma_chuc_vu_unique', 'unique(ma_chuc_vu)', 'Mã chức vụ phải là duy nhất!'),
        ('ten_chuc_vu_unique', 'unique(ten_chuc_vu)', 'Tên chức vụ phải là duy nhất!'),
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_chuc_vu', _('New')) == _('New'):
            vals['ma_chuc_vu'] = self.env['ir.sequence'].next_by_code('chuc_vu') or _('New')
        return super(ChucVu, self).create(vals)
