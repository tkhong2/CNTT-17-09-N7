# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import datetime

class NhanVien(models.Model):
    _name = "nhan_vien"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quản lý thông tin nhân viên"
    _rec_name = "ma_nhan_vien"

    ma_nhan_vien = fields.Char(string="Mã nhân viên", required=True, index=True)
    ho_va_ten = fields.Char(string="Họ và tên", required=True, tracking=True)
    ten = fields.Char(string="Tên", compute="_compute_ten", store=True)
    ho = fields.Char(string="Họ đệm", compute="_compute_ho", store=True)
    ngay_sinh = fields.Date(string="Ngày sinh", required=True, tracking=True)
    gioi_tinh = fields.Selection([
        ('nam', 'Nam'),
        ('nu', 'Nữ'),
        ('khac', 'Khác')
    ], string="Giới tính", default='nam', tracking=True)
    cmnd_cccd = fields.Char(string="CMND/CCCD", tracking=True)
    ngay_cap = fields.Date(string="Ngày cấp")
    noi_cap = fields.Char(string="Nơi cấp")
    dia_chi = fields.Text(string="Địa chỉ thường trú", tracking=True)
    dia_chi_hien_tai = fields.Text(string="Địa chỉ hiện tại")
    email = fields.Char(string="Email", tracking=True)
    dien_thoai = fields.Char(string="Điện thoại", tracking=True)
    hinh_anh = fields.Binary(string="Hình ảnh")
    
    # Thông tin học vấn
    trinh_do_hoc_van = fields.Selection([
        ('tieu_hoc', 'Tiểu học'),
        ('trung_hoc_co_so', 'Trung học cơ sở'),
        ('trung_hoc_pho_thong', 'Trung học phổ thông'),
        ('cao_dang', 'Cao đẳng'),
        ('dai_hoc', 'Đại học'),
        ('thac_si', 'Thạc sĩ'),
        ('tien_si', 'Tiến sĩ'),
    ], string="Trình độ học vấn", tracking=True)
    chuyen_nganh = fields.Char(string="Chuyên ngành")
    truong_tot_nghiep = fields.Char(string="Trường tốt nghiệp")
    nam_tot_nghiep = fields.Integer(string="Năm tốt nghiệp")
    
    
    # Các mối quan hệ
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", tracking=True)
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ", tracking=True)
    quan_ly_id = fields.Many2one('nhan_vien', string="Quản lý trực tiếp")
    hop_dong_ids = fields.One2many('hop_dong', 'nhan_vien_id', string="Hợp đồng")
    cham_cong_ids = fields.One2many('cham_cong', 'nhan_vien_id', string="Chấm công")
    danh_gia_ids = fields.One2many('danh_gia', 'nhan_vien_id', string="Đánh giá")
    dao_tao_ids = fields.One2many('dao_tao', 'nhan_vien_id', string="Quá trình đào tạo")
    
    # Thông tin công việc
    ngay_vao_lam = fields.Date(string="Ngày vào làm", tracking=True)
    trang_thai = fields.Selection([
        ('active', 'Đang làm việc'),
        ('probation', 'Thử việc'),
        ('leave', 'Đã nghỉ việc'),
        ('suspended', 'Tạm ngừng')
    ], string="Trạng thái", default='active', tracking=True)
    ngay_nghi_viec = fields.Date(string="Ngày nghỉ việc", tracking=True)
    ly_do_nghi_viec = fields.Text(string="Lý do nghỉ việc")
    
    # Các trường tính toán
    tuoi = fields.Integer(string="Tuổi", compute="_compute_tuoi", store=True)
    hop_dong_hien_tai_id = fields.Many2one('hop_dong', string="Hợp đồng hiện tại", 
                                          compute="_compute_hop_dong_hien_tai", store=True)
    so_nam_lam_viec = fields.Float(string="Số năm làm việc", compute="_compute_so_nam_lam_viec", store=True)
    so_ngay_phep_nam = fields.Float(string="Số ngày phép năm", compute="_compute_so_ngay_phep_nam", store=True)
    so_ngay_phep_da_nghi = fields.Float(string="Số ngày phép đã nghỉ", compute="_compute_so_ngay_phep_da_nghi")
    so_ngay_phep_con_lai = fields.Float(string="Số ngày phép còn lại", compute="_compute_so_ngay_phep_con_lai")
    
    # Thông tin ngân hàng
    so_tai_khoan = fields.Char(string="Số tài khoản")
    ten_ngan_hang = fields.Char(string="Tên ngân hàng")
    chi_nhanh = fields.Char(string="Chi nhánh")
    
    # Thông tin bảo hiểm
    so_bhxh = fields.Char(string="Số BHXH")
    ngay_tham_gia_bhxh = fields.Date(string="Ngày tham gia BHXH")
    so_bhyt = fields.Char(string="Số BHYT")
    ngay_bat_dau_bhyt = fields.Date(string="Ngày bắt đầu BHYT")
    ngay_ket_thuc_bhyt = fields.Date(string="Ngày kết thúc BHYT")

    _sql_constraints = [
        ('ma_nhan_vien_unique', 'unique(ma_nhan_vien)', 'Mã nhân viên phải là duy nhất!'),
        ('cmnd_cccd_unique', 'unique(cmnd_cccd)', 'Số CMND/CCCD không được trùng lặp!'),
    ]
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.ma_nhan_vien} - {record.ho_va_ten}"
            result.append((record.id, name))
        return result

    @api.depends('ho_va_ten')
    def _compute_ten(self):
        for record in self:
            if record.ho_va_ten:
                ten_parts = record.ho_va_ten.split()
                if len(ten_parts) > 0:
                    record.ten = ten_parts[-1]
                else:
                    record.ten = record.ho_va_ten
            else:
                record.ten = False
    
    @api.depends('ho_va_ten')
    def _compute_ho(self):
        for record in self:
            if record.ho_va_ten:
                ten_parts = record.ho_va_ten.split()
                if len(ten_parts) > 1:
                    record.ho = ' '.join(ten_parts[:-1])
                else:
                    record.ho = False
            else:
                record.ho = False
    
    @api.depends('ngay_sinh')
    def _compute_tuoi(self):
        today = fields.Date.today()
        for record in self:
            if record.ngay_sinh:
                delta = relativedelta(today, record.ngay_sinh)
                record.tuoi = delta.years
            else:
                record.tuoi = 0
    
    @api.depends('hop_dong_ids', 'hop_dong_ids.ngay_bat_dau', 'hop_dong_ids.ngay_ket_thuc')
    def _compute_hop_dong_hien_tai(self):
        today = fields.Date.today()
        for record in self:
            hop_dong_hien_tai = False
            for hop_dong in record.hop_dong_ids:
                if hop_dong.ngay_bat_dau <= today and (not hop_dong.ngay_ket_thuc or hop_dong.ngay_ket_thuc >= today):
                    hop_dong_hien_tai = hop_dong
                    break
            record.hop_dong_hien_tai_id = hop_dong_hien_tai
    
    @api.depends('ngay_vao_lam')
    def _compute_so_nam_lam_viec(self):
        today = fields.Date.today()
        for record in self:
            if record.ngay_vao_lam:
                delta = relativedelta(today, record.ngay_vao_lam)
                record.so_nam_lam_viec = delta.years + (delta.months / 12.0) + (delta.days / 365.0)
            else:
                record.so_nam_lam_viec = 0
    
    @api.depends('so_nam_lam_viec')
    def _compute_so_ngay_phep_nam(self):
        for record in self:
            # Logic tính số ngày phép theo quy định của công ty
            # Ví dụ: 12 ngày cơ bản + 1 ngày cho mỗi năm làm việc (tối đa 18 ngày)
            so_ngay_phep = 12 + int(record.so_nam_lam_viec)
            record.so_ngay_phep_nam = min(so_ngay_phep, 18)
    
    def _compute_so_ngay_phep_da_nghi(self):
        current_year = fields.Date.today().year
        for record in self:
            # Tính tổng số ngày phép đã nghỉ trong năm hiện tại
            so_ngay_da_nghi = 0
            for cham_cong in record.cham_cong_ids:
                if cham_cong.ngay_cham_cong.year == current_year and cham_cong.trang_thai == 'nghi_phep':
                    so_ngay_da_nghi += 1
            record.so_ngay_phep_da_nghi = so_ngay_da_nghi
    
    def _compute_so_ngay_phep_con_lai(self):
        for record in self:
            record.so_ngay_phep_con_lai = record.so_ngay_phep_nam - record.so_ngay_phep_da_nghi
    
    @api.constrains('ngay_sinh')
    def _check_ngay_sinh(self):
        for record in self:
            if record.ngay_sinh and record.ngay_sinh > fields.Date.today():
                raise ValidationError(_("Ngày sinh không thể trong tương lai!"))
