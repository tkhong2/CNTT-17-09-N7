# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ViTriTuyenDung(models.Model):
    """Job Position for Recruitment"""
    _name = "vi_tri_tuyen_dung"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vị trí tuyển dụng"
    _rec_name = "ten_vi_tri"
    _order = "ngay_tao desc"

    ten_vi_tri = fields.Char(string="Tên vị trí", required=True, tracking=True)
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", required=True, tracking=True)
    cap_do = fields.Selection([
        ('intern', 'Thực tập sinh'),
        ('junior', 'Junior'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('manager', 'Quản lý'),
        ('director', 'Giám đốc'),
    ], string="Cấp độ", required=True, tracking=True)
    
    mo_ta_cong_viec = fields.Html(string="Mô tả công việc")
    yeu_cau = fields.Html(string="Yêu cầu kỹ năng")
    phuc_loi = fields.Html(string="Phúc lợi")
    
    so_luong_tuyen = fields.Integer(string="Số lượng tuyển", required=True, default=1, tracking=True)
    luong_du_kien = fields.Float(string="Lương dự kiến (VND)", tracking=True)
    rang_buoc_luong = fields.Char(string="Khoảng lương", help="VD: 5-7 triệu/tháng")
    
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('open', 'Đang tuyển'),
        ('closed', 'Đã đóng'),
        ('filled', 'Đã kín'),
    ], string="Trạng thái", default='draft', tracking=True)
    
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu tuyển")
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc tuyển")
    
    ung_vien_ids = fields.One2many('ung_vien', 'vi_tri_id', string="Ứng viên")
    so_ung_vien = fields.Integer(string="Số ứng viên", compute="_compute_so_ung_vien", store=True)
    so_ung_vien_qualified = fields.Integer(string="Ứng viên qualified", compute="_compute_so_ung_vien_qualified", store=True)
    
    ngay_tao = fields.Date(string="Ngày tạo", default=fields.Date.today, readonly=True)
    created_by = fields.Many2one('nhan_vien', string="Người tạo", default=lambda self: self.env.user.nhan_vien_id, readonly=True)
    
    @api.depends('ung_vien_ids')
    def _compute_so_ung_vien(self):
        for record in self:
            record.so_ung_vien = len(record.ung_vien_ids)
    
    @api.depends('ung_vien_ids.trang_thai')
    def _compute_so_ung_vien_qualified(self):
        for record in self:
            record.so_ung_vien_qualified = len(record.ung_vien_ids.filtered(lambda x: x.trang_thai in ['qualified', 'offer']))
    
    def action_open(self):
        """Open recruitment"""
        for record in self:
            if record.trang_thai != 'draft':
                raise ValidationError(_("Chỉ vị trí ở trạng thái Nháp mới mở tuyển được!"))
            record.trang_thai = 'open'
            record.ngay_bat_dau = fields.Date.today()
    
    def action_close(self):
        """Close recruitment"""
        for record in self:
            if record.trang_thai != 'open':
                raise ValidationError(_("Chỉ vị trí đang mở mới đóng tuyển được!"))
            record.trang_thai = 'closed'
            record.ngay_ket_thuc = fields.Date.today()


class UngVien(models.Model):
    """Candidate for Recruitment"""
    _name = "ung_vien"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Ứng viên tuyển dụng"
    _rec_name = "ho_ten"
    _order = "ngay_nop_don desc"

    # Thông tin ứng viên
    ho_ten = fields.Char(string="Họ tên", required=True, tracking=True)
    email = fields.Char(string="Email", required=True)
    so_dien_thoai = fields.Char(string="Số điện thoại")
    dia_chi = fields.Text(string="Địa chỉ")
    
    # Học vấn
    bang_cap = fields.Char(string="Bằng cấp cao nhất")
    truong_hoc = fields.Char(string="Trường đại học/Cao đẳng")
    chuyen_nganh = fields.Char(string="Chuyên ngành")
    
    # Các năm kinh nghiệm
    so_nam_kinh_nghiem = fields.Float(string="Số năm kinh nghiệm", default=0)
    
    # Vị trí ứng tuyển
    vi_tri_id = fields.Many2one('vi_tri_tuyen_dung', string="Vị trí ứng tuyển", required=True, ondelete='cascade', tracking=True)
    phong_ban_id = fields.Many2one('phong_ban', related='vi_tri_id.phong_ban_id', store=True)
    
    # Nguồn ứng viên
    nguon = fields.Selection([
        ('cv_truc_tiep', 'CV trực tiếp'),
        ('linkedin', 'LinkedIn'),
        ('website', 'Website công ty'),
        ('gioi_thieu', 'Giới thiệu'),
        ('recruiter', 'Recruiter'),
        ('job_portal', 'Job portal'),
        ('khac', 'Khác'),
    ], string="Nguồn ứng viên", required=True, tracking=True)
    
    # Timeline
    ngay_nop_don = fields.Date(string="Ngày nộp đơn", default=fields.Date.today, tracking=True)
    ngay_phong_van = fields.Date(string="Ngày phỏng vấn")
    ngay_offer = fields.Date(string="Ngày gửi offer")
    ngay_accept = fields.Date(string="Ngày chấp nhận offer")
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('new', 'Mới'),
        ('screening', 'Sàng lọc CV'),
        ('phong_van', 'Phỏng vấn'),
        ('qualified', 'Đạt yêu cầu'),
        ('offer', 'Gửi offer'),
        ('accepted', 'Chấp nhận'),
        ('rejected', 'Từ chối'),
        ('hired', 'Đã tuyển'),
    ], string="Trạng thái", default='new', tracking=True)
    
    # Đánh giá
    diem_cv = fields.Float(string="Điểm CV", default=0, help="0-10")
    diem_phong_van = fields.Float(string="Điểm phỏng vấn", default=0, help="0-10")
    nhan_xet = fields.Text(string="Nhận xét")
    ly_do_tu_choi = fields.Text(string="Lý do từ chối")
    
    # Lương
    luong_thoa_thuan = fields.Float(string="Lương thỏa thuận")
    
    # CV và hồ sơ
    file_cv = fields.Binary(string="File CV")
    file_cv_name = fields.Char(string="Tên file CV")
    
    # Liên hệ
    nguoi_tuyen_dung_id = fields.Many2one('nhan_vien', string="HR tuyển dụng", tracking=True)
    nguoi_phong_van_id = fields.Many2one('nhan_vien', string="Người phỏng vấn", tracking=True)
    
    # Phỏng vấn
    phong_van_ids = fields.One2many('phong_van', 'ung_vien_id', string="Lịch phỏng vấn")
    
    # Tạo nhân viên khi tuyển
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên (khi tuyển)", readonly=True)
    
    @api.constrains('diem_cv', 'diem_phong_van')
    def _check_scores(self):
        for record in self:
            if record.diem_cv and not (0 <= record.diem_cv <= 10):
                raise ValidationError(_("Điểm CV phải từ 0-10!"))
            if record.diem_phong_van and not (0 <= record.diem_phong_van <= 10):
                raise ValidationError(_("Điểm phỏng vấn phải từ 0-10!"))
    
    def action_mark_screening(self):
        """Mark as in screening"""
        self.trang_thai = 'screening'
    
    def action_mark_interviewed(self):
        """Mark as interviewed"""
        self.trang_thai = 'phong_van'
    
    def action_mark_qualified(self):
        """Mark as qualified"""
        self.trang_thai = 'qualified'
    
    def action_send_offer(self):
        """Send offer"""
        if self.trang_thai not in ['qualified', 'phong_van']:
            raise ValidationError(_("Chỉ ứng viên qualified mới nhận offer!"))
        self.trang_thai = 'offer'
        self.ngay_offer = fields.Date.today()
    
    def action_accept_offer(self):
        """Accept offer"""
        self.trang_thai = 'accepted'
        self.ngay_accept = fields.Date.today()
    
    def action_hire(self):
        """Hire candidate - create nhan_vien"""
        if self.trang_thai != 'accepted':
            raise ValidationError(_("Chỉ ứng viên đã chấp nhận offer mới có thể tuyển!"))
        
        # Tạo nhân viên mới
        nhan_vien = self.env['nhan_vien'].create({
            'ho_va_ten': self.ho_ten,
            'email': self.email,
            'dien_thoai': self.so_dien_thoai,
            'dia_chi': self.dia_chi,
            'chuyen_nganh': self.chuyen_nganh,
            'phong_ban_id': self.phong_ban_id.id,
            'ngay_vao_lam': fields.Date.today(),
            'trang_thai': 'probation',
        })
        
        self.nhan_vien_id = nhan_vien.id
        self.trang_thai = 'hired'
    
    def action_reject(self):
        """Reject candidate"""
        if self.trang_thai == 'hired':
            raise ValidationError(_("Không thể từ chối ứng viên đã tuyển!"))
        self.trang_thai = 'rejected'


class PhongVan(models.Model):
    """Interview Schedule"""
    _name = "phong_van"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Lịch phỏng vấn"
    _rec_name = "display_name"
    _order = "ngay_phong_van asc"

    ung_vien_id = fields.Many2one('ung_vien', string="Ứng viên", required=True, ondelete='cascade', tracking=True)
    vi_tri_id = fields.Many2one('vi_tri_tuyen_dung', related='ung_vien_id.vi_tri_id', store=True)
    
    display_name = fields.Char(compute="_compute_display_name", store=True)
    
    ngay_phong_van = fields.Datetime(string="Ngày giờ phỏng vấn", required=True, tracking=True)
    dia_diem = fields.Char(string="Địa điểm/Link video")
    
    loai_phong_van = fields.Selection([
        ('screening', 'Screening'),
        ('technical', 'Technical'),
        ('culture_fit', 'Culture Fit'),
        ('final', 'Final'),
    ], string="Loại phỏng vấn", required=True, tracking=True)
    
    muc_dich = fields.Text(string="Mục đích phỏng vấn")
    
    # Người phỏng vấn
    nguoi_phong_van_ids = fields.Many2many('nhan_vien', string="Người phỏng vấn")
    
    # Kết quả
    trang_thai = fields.Selection([
        ('scheduled', 'Đã lên lịch'),
        ('done', 'Đã phỏng vấn'),
        ('cancelled', 'Hủy'),
    ], string="Trạng thái", default='scheduled', tracking=True)
    
    diem = fields.Float(string="Điểm phỏng vấn", help="0-10")
    nhan_xet = fields.Text(string="Nhận xét/Đánh giá")
    
    @api.depends('ung_vien_id', 'ngay_phong_van')
    def _compute_display_name(self):
        for record in self:
            if record.ung_vien_id and record.ngay_phong_van:
                record.display_name = f"{record.ung_vien_id.ho_ten} - {record.ngay_phong_van.strftime('%d/%m/%Y %H:%M')}"
            else:
                record.display_name = False
    
    def action_mark_done(self):
        """Mark interview as done"""
        self.trang_thai = 'done'
    
    def action_cancel(self):
        """Cancel interview"""
        self.trang_thai = 'cancelled'


class OnboardingOffboarding(models.Model):
    """Onboarding and Offboarding Checklist"""
    _name = "onboarding_offboarding"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Checklist tiếp nhận/từ biệt nhân viên"
    _rec_name = "display_name"
    _order = "ngay_start desc"

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade', tracking=True)
    ho_ten = fields.Char(related='nhan_vien_id.ho_va_ten', store=True)
    phong_ban_id = fields.Many2one('phong_ban', related='nhan_vien_id.phong_ban_id', store=True)
    
    # Loại (Onboarding hoặc Offboarding)
    loai = fields.Selection([
        ('onboarding', 'Tiếp nhận nhân viên mới'),
        ('offboarding', 'Từ biệt nhân viên'),
    ], string="Loại", required=True, tracking=True)
    
    display_name = fields.Char(compute="_compute_display_name", store=True)
    
    ngay_start = fields.Date(string="Ngày bắt đầu", default=fields.Date.today, tracking=True)
    ngay_ket_thuc_du_kinh = fields.Date(string="Ngày kết thúc dự kiến", tracking=True)
    
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành'),
    ], string="Trạng thái", default='draft', tracking=True)
    
    # Công việc cần làm
    cong_viec_ids = fields.One2many('onboarding_task', 'checklist_id', string="Công việc")
    tong_cong_viec = fields.Integer(string="Tổng công việc", compute="_compute_tong_cong_viec", store=True)
    cong_viec_hoan_thanh = fields.Integer(string="Công việc đã hoàn thành", compute="_compute_cong_viec_hoan_thanh", store=True)
    ti_le_hoan_thanh = fields.Float(string="% Hoàn thành", compute="_compute_ti_le_hoan_thanh", store=True)
    
    ghi_chu = fields.Text(string="Ghi chú")
    
    @api.depends('loai', 'nhan_vien_id')
    def _compute_display_name(self):
        for record in self:
            loai_text = 'Tiếp nhận' if record.loai == 'onboarding' else 'Từ biệt'
            if record.nhan_vien_id:
                record.display_name = f"{loai_text}: {record.nhan_vien_id.ho_va_ten}"
            else:
                record.display_name = loai_text
    
    @api.depends('cong_viec_ids')
    def _compute_tong_cong_viec(self):
        for record in self:
            record.tong_cong_viec = len(record.cong_viec_ids)
    
    @api.depends('cong_viec_ids.da_hoan_thanh')
    def _compute_cong_viec_hoan_thanh(self):
        for record in self:
            record.cong_viec_hoan_thanh = len(record.cong_viec_ids.filtered(lambda x: x.da_hoan_thanh))
    
    @api.depends('tong_cong_viec', 'cong_viec_hoan_thanh')
    def _compute_ti_le_hoan_thanh(self):
        for record in self:
            if record.tong_cong_viec > 0:
                record.ti_le_hoan_thanh = (record.cong_viec_hoan_thanh / record.tong_cong_viec) * 100
            else:
                record.ti_le_hoan_thanh = 0
    
    def action_start(self):
        """Bắt đầu tiếp nhận/từ biệt"""
        self.trang_thai = 'in_progress'
    
    def action_done(self):
        """Hoàn thành tiếp nhận/từ biệt"""
        if not all(task.da_hoan_thanh for task in self.cong_viec_ids):
            raise ValidationError(_("Phải hoàn thành tất cả công việc trước!"))
        self.trang_thai = 'done'
        self.ngay_ket_thuc_du_kinh = fields.Date.today()


class OnboardingTask(models.Model):
    """Individual Task in Onboarding/Offboarding"""
    _name = "onboarding_task"
    _description = "Công việc tiếp nhận/từ biệt"
    _rec_name = "tieu_de"
    _order = "thu_tu asc"

    checklist_id = fields.Many2one('onboarding_offboarding', string="Checklist", required=True, ondelete='cascade')
    
    thu_tu = fields.Integer(string="Thứ tự", default=1)
    tieu_de = fields.Char(string="Tiêu đề", required=True)
    mo_ta = fields.Text(string="Mô tả")
    
    phu_trach_id = fields.Many2one('nhan_vien', string="Người phụ trách")
    
    da_hoan_thanh = fields.Boolean(string="Đã hoàn thành", default=False)
    ngay_hoan_thanh = fields.Date(string="Ngày hoàn thành")
    
    ghi_chu = fields.Text(string="Ghi chú")
    
    @api.onchange('da_hoan_thanh')
    def _onchange_da_hoan_thanh(self):
        if self.da_hoan_thanh:
            self.ngay_hoan_thanh = fields.Date.today()
        else:
            self.ngay_hoan_thanh = False
