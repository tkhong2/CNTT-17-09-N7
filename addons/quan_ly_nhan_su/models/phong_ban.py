# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PhongBan(models.Model):
    _name = "phong_ban"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quản lý phòng ban"
    _rec_name = "ten_phong_ban"

    ma_phong_ban = fields.Char(string="Mã phòng ban", required=True, index=True)
    ten_phong_ban = fields.Char(string="Tên phòng ban", required=True, tracking=True)
    mo_ta = fields.Text(string="Mô tả")
    
    # Các mối quan hệ
    truong_phong_id = fields.Many2one('nhan_vien', string="Trưởng phòng", tracking=True)
    nhan_vien_ids = fields.One2many('nhan_vien', 'phong_ban_id', string="Nhân viên")
    
    # Thống kê
    so_luong_nhan_vien = fields.Integer(string="Số lượng nhân viên", compute="_compute_so_luong_nhan_vien", store=True)
    
    # Ràng buộc SQL
    _sql_constraints = [
        ('ma_phong_ban_unique', 'unique(ma_phong_ban)', 'Mã phòng ban phải là duy nhất!'),
        ('ten_phong_ban_unique', 'unique(ten_phong_ban)', 'Tên phòng ban phải là duy nhất!'),
    ]
    
    
    @api.depends('nhan_vien_ids')
    def _compute_so_luong_nhan_vien(self):
        for record in self:
            record.so_luong_nhan_vien = len(record.nhan_vien_ids)
