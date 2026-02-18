# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class DanhGia(models.Model):
    _name = "danh_gia"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Đánh giá nhân viên"
    _rec_name = "display_name"
    
    display_name = fields.Char(string="Tên hiển thị", compute="_compute_display_name", store=True)
    
    # Các mối quan hệ
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, tracking=True)
    nguoi_danh_gia_id = fields.Many2one('nhan_vien', string="Người đánh giá", required=True, tracking=True)
    
    # Thông tin đánh giá
    loai_danh_gia = fields.Selection([
        ('dinh_ky', 'Đánh giá định kỳ'),
        ('tang_luong', 'Đánh giá tăng lương'),
        ('thu_viec', 'Đánh giá thử việc'),
        ('khac', 'Khác')
    ], string="Loại đánh giá", required=True, tracking=True)
    thoi_gian = fields.Date(string="Thời gian đánh giá", required=True, default=fields.Date.today, tracking=True)
    
    # Tiêu chí đánh giá (thang điểm 1-5)
    ky_nang_chuyen_mon = fields.Selection([
        ('1', 'Kém'), ('2', 'Yếu'), ('3', 'Trung bình'), ('4', 'Khá'), ('5', 'Tốt')
    ], string="Kỹ năng chuyên môn", default='3', tracking=True)
    tinh_than_lam_viec = fields.Selection([
        ('1', 'Kém'), ('2', 'Yếu'), ('3', 'Trung bình'), ('4', 'Khá'), ('5', 'Tốt')
    ], string="Tinh thần làm việc", default='3', tracking=True)
    kha_nang_giao_tiep = fields.Selection([
        ('1', 'Kém'), ('2', 'Yếu'), ('3', 'Trung bình'), ('4', 'Khá'), ('5', 'Tốt')
    ], string="Khả năng giao tiếp", default='3', tracking=True)
    kha_nang_lam_viec_nhom = fields.Selection([
        ('1', 'Kém'), ('2', 'Yếu'), ('3', 'Trung bình'), ('4', 'Khá'), ('5', 'Tốt')
    ], string="Khả năng làm việc nhóm", default='3', tracking=True)
    
    # Trường tính toán tổng hợp
    diem_trung_binh = fields.Float(string="Điểm trung bình (Thang điểm 5)", compute="_compute_diem_trung_binh", store=True)
    
    # Ghi chú và kết luận
    nhan_xet = fields.Text(string="Nhận xét")
    ket_luan = fields.Selection([
        ('dat', 'Đạt'),
        ('khong_dat', 'Không đạt'),
        ('can_cai_thien', 'Cần cải thiện')
    ], string="Kết luận", tracking=True)
    
    @api.depends('nhan_vien_id', 'thoi_gian', 'loai_danh_gia')
    def _compute_display_name(self):
        for record in self:
            if record.nhan_vien_id and record.thoi_gian and record.loai_danh_gia:
                record.display_name = f"{record.nhan_vien_id.ho_va_ten} - {dict(record._fields['loai_danh_gia'].selection).get(record.loai_danh_gia)} - {record.thoi_gian}"
            else:
                record.display_name = False
    
    @api.depends('ky_nang_chuyen_mon', 'tinh_than_lam_viec', 'kha_nang_giao_tiep', 'kha_nang_lam_viec_nhom')
    def _compute_diem_trung_binh(self):
        for record in self:
            diem = []
            if record.ky_nang_chuyen_mon:
                diem.append(int(record.ky_nang_chuyen_mon))
            if record.tinh_than_lam_viec:
                diem.append(int(record.tinh_than_lam_viec))
            if record.kha_nang_giao_tiep:
                diem.append(int(record.kha_nang_giao_tiep))
            if record.kha_nang_lam_viec_nhom:
                diem.append(int(record.kha_nang_lam_viec_nhom))
            
            if diem:
                record.diem_trung_binh = sum(diem) / len(diem)
            else:
                record.diem_trung_binh = 0
