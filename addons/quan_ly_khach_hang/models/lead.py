# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class Lead(models.Model):
    _name = "lead"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Lead bán hàng"
    _rec_name = "ma_lead"
    _order = "ngay_tao desc"

    ma_lead = fields.Char(string="Mã lead", required=True, index=True, default=lambda self: _('New'))
    ten_lead = fields.Char(string="Tên lead/Công ty", required=True, tracking=True)
    nguoi_lien_he = fields.Char(string="Người liên hệ", tracking=True)
    email = fields.Char(string="Email")
    so_dien_thoai = fields.Char(string="Điện thoại")
    dia_chi = fields.Text(string="Địa chỉ")
    mo_ta = fields.Text(string="Ghi chú")
    
    # Phân loại
    nguon_lead = fields.Selection([
        ('website', 'Website'),
        ('phone', 'Gọi điện'),
        ('email', 'Email'),
        ('referral', 'Giới thiệu'),
        ('event', 'Sự kiện/Triển lãm'),
        ('social_media', 'Mạng xã hội'),
        ('partnership', 'Đối tác'),
        ('other', 'Khác'),
    ], string="Nguồn lead", required=True, tracking=True)
    
    loai_khach_hang = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('cong_ty_nho', 'Công ty nhỏ'),
        ('cong_ty_trung_binh', 'Công ty trung bình'),
        ('doanh_nghiep_lon', 'Doanh nghiệp lớn'),
    ], string="Loại khách hàng", tracking=True)
    
    nganh_cong_nghiep = fields.Char(string="Ngành công nghiệp")
    quy_mo = fields.Selection([
        ('10', '< 10 nhân viên'),
        ('50', '10-50 nhân viên'),
        ('100', '50-100 nhân viên'),
        ('1000', '> 100 nhân viên'),
    ], string="Quy mô")
    
    # Gán trách nhiệm
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách", tracking=True)
    ngay_gan = fields.Date(string="Ngày gán", default=fields.Date.today)
    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('rat_cao', 'Rất cao'),
    ], string="Độ ưu tiên", default='trung_binh', tracking=True)
    
    # Trạng thái & Điểm số
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_tiep_can', 'Đang tiếp cận'),
        ('quan_tam', 'Quan tâm'),
        ('chua_san_sang', 'Chưa sẵn sàng'),
        ('san_sang', 'Sẵn sàng'),
        ('chuyen_khach', 'Chuyển khách'),
        ('vo_kien_cu', 'Vô kiến cự'),
    ], string="Trạng thái", default='moi', tracking=True)
    
    diem_danh_gia = fields.Float(string="Điểm đánh giá", default=0, compute="_compute_diem_danh_gia", store=True, help="0-100")
    
    # Tương tác
    ngay_lien_he_cuoi = fields.Date(string="Ngày liên hệ cuối")
    so_lan_lien_he = fields.Integer(string="Số lần liên hệ", default=0)
    ngay_theo_doi_tiep = fields.Date(string="Ngày theo dõi tiếp", index=True)
    
    # Timeline
    ngay_tao = fields.Date(string="Ngày tạo", default=fields.Date.today, readonly=True)
    ngay_sua = fields.Date(string="Ngày sửa", compute="_compute_ngay_sua", store=True)
    ngay_chuyen_khach = fields.Date(string="Ngày chuyển khách")
    thoi_gian_chuyen_doi = fields.Integer(string="Thời gian chuyển đổi (ngày)", compute="_compute_thoi_gian_chuyen_doi", store=True)
    
    # Quan hệ
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", tracking=True)
    co_hoi_ids = fields.One2many('co_hoi_ban_hang', 'lead_id', string="Cơ hội bán hàng")
    hoat_dong_ids = fields.One2many('lead_hoat_dong', 'lead_id', string="Hoạt động")
    
    # Dự toán
    ngan_sach_uoc_tinh = fields.Float(string="Ngân sách ước tính")
    tiem_nang_doanh_thu = fields.Float(string="Tiềm năng doanh thu", compute="_compute_tiem_nang_doanh_thu", store=True)
    
    @api.depends('hoat_dong_ids')
    def _compute_diem_danh_gia(self):
        """Tính điểm dựa trên hoạt động"""
        for record in self:
            # Simplified scoring: based on number of activities and recent contact
            score = 0
            if record.hoat_dong_ids:
                score += min(len(record.hoat_dong_ids) * 10, 40)  # Max 40 points for activities
            
            if record.ngay_lien_he_cuoi:
                days_since_contact = (fields.Date.today() - record.ngay_lien_he_cuoi).days
                if days_since_contact <= 7:
                    score += 30
                elif days_since_contact <= 30:
                    score += 20
                elif days_since_contact <= 90:
                    score += 10
            
            if record.trang_thai in ['quan_tam', 'san_sang']:
                score += 20
            
            record.diem_danh_gia = min(score, 100)
    
    @api.depends('create_date')
    def _compute_ngay_sua(self):
        """Ngày sửa gần nhất"""
        for record in self:
            record.ngay_sua = fields.Date.today()
    
    @api.depends('ngay_chuyen_khach', 'ngay_tao')
    def _compute_thoi_gian_chuyen_doi(self):
        """Tính số ngày từ tạo đến chuyển khách"""
        for record in self:
            if record.ngay_chuyen_khach and record.ngay_tao:
                record.thoi_gian_chuyen_doi = (record.ngay_chuyen_khach - record.ngay_tao).days
            else:
                record.thoi_gian_chuyen_doi = 0
    
    @api.depends('ngan_sach_uoc_tinh')
    def _compute_tiem_nang_doanh_thu(self):
        """Tiềm năng doanh thu từ ngân sách ước tính"""
        for record in self:
            record.tiem_nang_doanh_thu = record.ngan_sach_uoc_tinh or 0
    
    def action_contact(self):
        """Đánh dấu đang tiếp cận"""
        for record in self:
            if record.trang_thai != 'moi':
                raise ValidationError(_("Chỉ lead Mới mới chuyển sang Đang tiếp cận được!"))
            record.trang_thai = 'dang_tiep_can'
            record.ngay_lien_he_cuoi = fields.Date.today()
            record.so_lan_lien_he += 1
    
    def action_mark_interested(self):
        """Đánh dấu khách quan tâm"""
        for record in self:
            if record.trang_thai not in ['moi', 'dang_tiep_can']:
                raise ValidationError(_("Chỉ lead Mới/Đang tiếp cận mới chuyển sang Quan tâm được!"))
            record.trang_thai = 'quan_tam'
            record.ngay_lien_he_cuoi = fields.Date.today()
            record.so_lan_lien_he += 1
    
    def action_mark_unqualified(self):
        """Đánh dấu chưa sẵn sàng (cần nuôi dưỡng)"""
        for record in self:
            if record.trang_thai == 'chuyen_khach':
                raise ValidationError(_("Không thể chuyển lead đã thành khách hàng về trạng thái Chưa sẵn sàng!"))
            record.trang_thai = 'chua_san_sang'
            record.ngay_theo_doi_tiep = fields.Date.today() + timedelta(days=30)
    
    def action_mark_qualified(self):
        """Đánh dấu sẵn sàng chuyển đổi"""
        for record in self:
            if record.trang_thai not in ['quan_tam', 'chua_san_sang', 'dang_tiep_can']:
                raise ValidationError(_("Chỉ lead Quan tâm/Chưa sẵn sàng/Đang tiếp cận mới chuyển Sẵn sàng được!"))
            record.trang_thai = 'san_sang'
    
    def action_convert_to_customer(self):
        """Chuyển lead thành khách hàng"""
        for record in self:
            if record.trang_thai not in ['san_sang', 'moi']:
                raise ValidationError(_("Chỉ lead sẵn sàng mới có thể chuyển thành khách hàng!"))
            
            # Tạo khách hàng mới hoặc liên kết với khách hàng hiện có
            if not record.khach_hang_id:
                khach_hang = self.env['khach_hang'].create({
                    'ten_khach_hang': record.ten_lead,
                    'nguoi_lien_he': record.nguoi_lien_he,
                    'email': record.email,
                    'dien_thoai': record.so_dien_thoai,
                    'dia_chi': record.dia_chi,
                    'nhan_vien_phu_trach_id': record.nhan_vien_phu_trach_id.id,
                    'trang_thai_hop_tac': 'dang_hop_tac',
                })
                record.khach_hang_id = khach_hang.id
            
            record.trang_thai = 'chuyen_khach'
            record.ngay_chuyen_khach = fields.Date.today()
    
    def action_mark_dead(self):
        """Đánh dấu lead vô kiến cự"""
        for record in self:
            if record.trang_thai == 'chuyen_khach':
                raise ValidationError(_("Không thể đánh dấu vô kiến cự cho lead đã chuyển khách!"))
            record.trang_thai = 'vo_kien_cu'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_lead', _('New')) == _('New'):
                vals['ma_lead'] = self.env['ir.sequence'].next_by_code('lead') or _('New')
        return super().create(vals_list)


class LeadHoatDong(models.Model):
    _name = "lead_hoat_dong"
    _description = "Hoạt động trên lead"
    _rec_name = "tieu_de"
    _order = "ngay_gio desc"

    lead_id = fields.Many2one('lead', string="Lead", required=True, ondelete='cascade')
    loai_hoat_dong = fields.Selection([
        ('goi', 'Gọi'),
        ('email', 'Email'),
        ('cuoc_hop', 'Cuộc họp'),
        ('note', 'Ghi chú'),
        ('document', 'Gửi tài liệu'),
    ], string="Loại hoạt động", required=True)
    
    ngay_gio = fields.Datetime(string="Thời gian", default=fields.Datetime.now, required=True)
    nguoi_thuc_hien_id = fields.Many2one('nhan_vien', string="Người thực hiện")
    tieu_de = fields.Char(string="Tiêu đề")
    noi_dung = fields.Text(string="Nội dung")
    ket_qua = fields.Char(string="Kết quả")
