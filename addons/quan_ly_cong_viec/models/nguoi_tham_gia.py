# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class NguoiThamGia(models.Model):
    _name = "nguoi_tham_gia"
    _description = "Người tham gia công việc"
    _rec_name = "nhan_vien_id"
    
    cong_viec_id = fields.Many2one('cong_viec', string="Công việc", required=True, ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    vai_tro = fields.Selection([
        ('phu_trach', 'Phụ trách'),
        ('thuc_hien', 'Thực hiện'),
        ('ho_tro', 'Hỗ trợ'),
        ('kiem_tra', 'Kiểm tra'),
        ('khac', 'Khác')
    ], string="Vai trò", default='thuc_hien', required=True)
    
    # Trạng thái báo cáo
    trang_thai = fields.Selection([
        ('chua_bao_cao', '⭕ Chưa báo cáo'),
        ('dang_xu_ly', '🟡 Đang xử lý'),
        ('da_bao_cao', '✅ Đã báo cáo'),
    ], string="Trạng thái báo cáo", default='chua_bao_cao', required=True)
    
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc")
    so_gio_du_kien = fields.Float(string="Số giờ dự kiến")
    ghi_chu = fields.Text(string="Ghi chú")
    
    # Thông tin từ công việc
    du_an_id = fields.Many2one(related='cong_viec_id.du_an_id', string="Dự án", store=True, readonly=True)
    ten_cong_viec = fields.Char(related='cong_viec_id.ten_cong_viec', string="Tên công việc", store=True, readonly=True)
    
    # Thông tin từ nhân viên
    ten_nhan_vien = fields.Char(related='nhan_vien_id.ho_va_ten', string="Tên nhân viên", store=True, readonly=True)
    phong_ban_id = fields.Many2one(related='nhan_vien_id.phong_ban_id', string="Phòng ban", store=True, readonly=True)
    
    _sql_constraints = [
        ('cong_viec_nhan_vien_unique', 'unique(cong_viec_id, nhan_vien_id)', 
         'Mỗi nhân viên chỉ được thêm một lần vào công việc!'),
    ]
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau > record.ngay_ket_thuc:
                raise ValidationError(_("Ngày bắt đầu không thể sau ngày kết thúc!"))
                
    @api.constrains('cong_viec_id', 'ngay_bat_dau', 'ngay_ket_thuc')
    def _check_task_dates(self):
        for record in self:
            if record.cong_viec_id.ngay_bat_dau and record.ngay_bat_dau < record.cong_viec_id.ngay_bat_dau:
                raise ValidationError(_("Ngày bắt đầu tham gia không thể trước ngày bắt đầu công việc!"))
            
            if record.cong_viec_id.ngay_ket_thuc and record.ngay_ket_thuc and record.ngay_ket_thuc > record.cong_viec_id.ngay_ket_thuc:
                raise ValidationError(_("Ngày kết thúc tham gia không thể sau ngày kết thúc công việc!"))
                
    @api.model
    def create(self, vals):
        # Khi thêm người phụ trách, cập nhật trường nguoi_phu_trach_id của công việc
        result = super(NguoiThamGia, self).create(vals)
        if result.vai_tro == 'phu_trach':
            result.cong_viec_id.write({'nguoi_phu_trach_id': result.nhan_vien_id.id})
        return result
