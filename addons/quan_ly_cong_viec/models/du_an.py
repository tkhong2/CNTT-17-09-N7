# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DuAn(models.Model):
    _name = "du_an"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Dự án"
    _rec_name = "ten_du_an"
    _order = "ngay_bat_dau desc, ten_du_an"
    
    ma_du_an = fields.Char(string="Mã dự án", required=True, index=True)
    ten_du_an = fields.Char(string="Tên dự án", required=True)
    mo_ta = fields.Text(string="Mô tả")
    
    # Thời gian
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc")
    
    # Quan hệ
    nguoi_quan_ly_id = fields.Many2one('nhan_vien', string="Người quản lý dự án")
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('chuan_bi', 'Chuẩn bị'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('tam_dung', 'Tạm dừng'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy_bo', 'Hủy bỏ')
    ], string="Trạng thái", default='chuan_bi', tracking=True)
    
    # Thông tin tài chính
    ngan_sach = fields.Float(string="Ngân sách (VND)", tracking=True)
    chi_phi_thuc_te = fields.Float(string="Chi phí thực tế", compute="_compute_chi_phi_thuc_te", store=True)
    
    # Thống kê
    so_luong_cong_viec = fields.Integer(string="Số lượng công việc", compute="_compute_so_luong_cong_viec", store=True)
    ti_le_hoan_thanh = fields.Float(string="Tỉ lệ hoàn thành (%)", compute="_compute_ti_le_hoan_thanh", store=True)
    
    # Các trường quan hệ tham chiếu ngược
    cong_viec_ids = fields.One2many('cong_viec', 'du_an_id', string="Danh sách công việc")
    nguon_luc_ids = fields.One2many('phan_bo_nguon_luc', 'du_an_id', string="Nguồn lực phân bổ")
    
    _sql_constraints = [
        ('ma_du_an_unique', 'unique(ma_du_an)', 'Mã dự án phải là duy nhất!'),
    ]
    
    @api.depends('cong_viec_ids')
    def _compute_so_luong_cong_viec(self):
        for record in self:
            record.so_luong_cong_viec = len(record.cong_viec_ids)
    
    @api.depends('cong_viec_ids', 'cong_viec_ids.trang_thai')
    def _compute_ti_le_hoan_thanh(self):
        for record in self:
            tong_cong_viec = len(record.cong_viec_ids)
            if tong_cong_viec > 0:
                cong_viec_hoan_thanh = len(record.cong_viec_ids.filtered(lambda x: x.trang_thai == 'hoan_thanh'))
                record.ti_le_hoan_thanh = (cong_viec_hoan_thanh / tong_cong_viec) * 100
            else:
                record.ti_le_hoan_thanh = 0
    
    @api.depends('nguon_luc_ids', 'nguon_luc_ids.chi_phi')
    def _compute_chi_phi_thuc_te(self):
        for record in self:
            record.chi_phi_thuc_te = sum(record.nguon_luc_ids.mapped('chi_phi'))
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau > record.ngay_ket_thuc:
                raise ValidationError(_("Ngày bắt đầu không thể sau ngày kết thúc!"))

    @api.model
    def _cron_sync_project_status(self):
        projects = self.search([('trang_thai', 'not in', ['huy_bo'])])
        for project in projects:
            tasks = project.cong_viec_ids.filtered(lambda task: task.trang_thai != 'huy_bo')
            if not tasks:
                continue

            if all(task.trang_thai == 'hoan_thanh' for task in tasks):
                if project.trang_thai != 'hoan_thanh':
                    project.write({'trang_thai': 'hoan_thanh'})
                continue

            if project.trang_thai in ['chuan_bi', 'hoan_thanh']:
                has_started_tasks = any(task.trang_thai in ['dang_thuc_hien', 'tam_dung', 'moi'] for task in tasks)
                if has_started_tasks:
                    project.write({'trang_thai': 'dang_thuc_hien'})
