# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CoHoiBanHang(models.Model):
    _name = "co_hoi_ban_hang"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Cơ hội bán hàng"
    _rec_name = "ma_co_hoi"
    _order = "han_chot asc, ma_co_hoi desc"

    ma_co_hoi = fields.Char(string="Mã cơ hội", required=True, index=True, default=lambda self: _('New'))
    ten_co_hoi = fields.Char(string="Tên cơ hội", required=True, tracking=True)
    mo_ta = fields.Text(string="Mô tả")
    
    # Nguồn gốc
    lead_id = fields.Many2one('lead', string="Lead", tracking=True, ondelete='set null')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", tracking=True, ondelete='set null')
    du_an_id = fields.Many2one('du_an', string="Dự án liên quan", ondelete='set null')
    
    # Bán hàng
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách", required=True, tracking=True)
    nhom_ban_hang_id = fields.Many2one('nhan_vien', string="Người quản lý", tracking=True)
    ngay_tao = fields.Date(string="Ngày tạo", default=fields.Date.today, readonly=True)
    
    # Số tiền & Dự báo
    gia_tri_co_hoi = fields.Float(string="Giá trị cơ hội", required=True, tracking=True)
    xac_suat_thang = fields.Float(string="Xác suất thắng (%)", default=0, tracking=True, help="0-100%")
    doanh_thu_du_bao = fields.Float(string="Doanh thu dự báo", compute="_compute_doanh_thu_du_bao", store=True)
    han_chot = fields.Date(string="Hạn chót", tracking=True, help="Ngày dự kiến đóng deal")
    ghi_chu_tai_chinh = fields.Text(string="Ghi chú tài chính")
    
    # Giai đoạn bán hàng
    giai_doan = fields.Selection([
        ('kham_pha', 'Khám phá'),
        ('phat_trien', 'Phát triển'),
        ('de_xuat', 'Đề xuất'),
        ('thuong_luong', 'Thương lượng'),
        ('sap_dong', 'Sắp đóng'),
        ('thang', 'Thắng'),
        ('thua', 'Thua'),
        ('huy_bo', 'Hủy bỏ'),
    ], string="Giai đoạn", required=True, default='kham_pha', tracking=True)
    
    ngay_cap_nhat_giai_doan = fields.Date(string="Ngày cập nhật giai đoạn", compute="_compute_ngay_cap_nhat_giai_doan", store=True)
    
    # Hoạt động & Theo dõi
    so_lan_lien_he = fields.Integer(string="Số lần liên hệ", default=0)
    ngay_lien_he_cuoi = fields.Date(string="Ngày liên hệ cuối")
    ngay_theo_doi_tiep = fields.Date(string="Ngày theo dõi tiếp", index=True)
    hoat_dong_ids = fields.One2many('co_hoi_hoat_dong', 'co_hoi_id', string="Hoạt động")
    
    # Timeline
    ngay_dong_thang = fields.Date(string="Ngày đóng thắng")
    thoi_gian_kinh_doanh = fields.Integer(string="Thời gian kinh doanh (ngày)", compute="_compute_thoi_gian_kinh_doanh", store=True)
    nguyen_nhan_thua = fields.Text(string="Nguyên nhân thua")
    loi_quay_lai = fields.Text(string="Lối quay lại")
    
    # Trạng thái khác
    trang_thai_khac = fields.Selection([
        ('hoat_dong', 'Hoạt động'),
        ('tam_dung', 'Tạm dừng'),
        ('khong_hoat_dong', 'Không hoạt động'),
    ], string="Trạng thái", default='hoat_dong', tracking=True)
    
    @api.depends('gia_tri_co_hoi', 'xac_suat_thang')
    def _compute_doanh_thu_du_bao(self):
        """Tính doanh thu dự báo = Giá trị × Xác suất / 100"""
        for record in self:
            if record.gia_tri_co_hoi and record.xac_suat_thang:
                record.doanh_thu_du_bao = record.gia_tri_co_hoi * record.xac_suat_thang / 100.0
            else:
                record.doanh_thu_du_bao = 0
    
    @api.depends('giai_doan')
    def _compute_ngay_cap_nhat_giai_doan(self):
        """Ngày cập nhật giai đoạn"""
        for record in self:
            record.ngay_cap_nhat_giai_doan = fields.Date.today()
    
    @api.depends('ngay_dong_thang', 'ngay_tao')
    def _compute_thoi_gian_kinh_doanh(self):
        """Tính số ngày từ tạo đến đóng"""
        for record in self:
            if record.ngay_dong_thang and record.ngay_tao:
                record.thoi_gian_kinh_doanh = (record.ngay_dong_thang - record.ngay_tao).days
            else:
                current_days = (fields.Date.today() - record.ngay_tao).days if record.ngay_tao else 0
                record.thoi_gian_kinh_doanh = current_days
    
    @api.constrains('xac_suat_thang')
    def _check_xac_suat(self):
        """Kiểm tra xác suất nằm trong 0-100"""
        for record in self:
            if not (0 <= record.xac_suat_thang <= 100):
                raise ValidationError(_("Xác suất thắng phải từ 0-100!"))
    
    def action_move_to_stage(self, giai_doan):
        """Di chuyển sang giai đoạn khác"""
        for record in self:
            if record.giai_doan in ['thang', 'thua', 'huy_bo']:
                raise ValidationError(_("Không thể đổi giai đoạn khi cơ hội đã kết thúc!"))
            record.giai_doan = giai_doan
    
    def action_move_discovery(self):
        """Di chuyển sang Khám phá"""
        self.action_move_to_stage('kham_pha')
    
    def action_move_development(self):
        """Di chuyển sang Phát triển"""
        self.action_move_to_stage('phat_trien')
    
    def action_move_proposal(self):
        """Di chuyển sang Đề xuất"""
        self.action_move_to_stage('de_xuat')
    
    def action_move_negotiation(self):
        """Di chuyển sang Thương lượng"""
        self.action_move_to_stage('thuong_luong')
    
    def action_move_closing(self):
        """Di chuyển sang Sắp đóng"""
        self.action_move_to_stage('sap_dong')
    
    def action_mark_won(self):
        """Đánh dấu đã thắng"""
        for record in self:
            if record.giai_doan not in ['sap_dong', 'thuong_luong', 'de_xuat']:
                raise ValidationError(_("Chỉ cơ hội ở giai đoạn Đề xuất/Thương lượng/Sắp đóng mới được đánh dấu Thắng!"))

            record.giai_doan = 'thang'
            record.ngay_dong_thang = fields.Date.today()
            record.xac_suat_thang = 100.0

            # Auto-create customer if not exist
            if not record.khach_hang_id and record.lead_id:
                record.lead_id.action_convert_to_customer()
                record.khach_hang_id = record.lead_id.khach_hang_id
            elif not record.khach_hang_id and record.ten_co_hoi:
                khach_hang = self.env['khach_hang'].create({
                    'ten_khach_hang': record.ten_co_hoi,
                    'nhan_vien_phu_trach_id': record.nhan_vien_phu_trach_id.id,
                })
                record.khach_hang_id = khach_hang.id
    
    def action_mark_lost(self, nguyen_nhan=""):
        """Đánh dấu thua"""
        for record in self:
            if record.giai_doan not in ['kham_pha', 'phat_trien', 'de_xuat', 'thuong_luong', 'sap_dong']:
                raise ValidationError(_("Chỉ cơ hội đang xử lý mới được đánh dấu Thua!"))
            record.giai_doan = 'thua'
            record.ngay_dong_thang = fields.Date.today()
            record.xac_suat_thang = 0.0
            if nguyen_nhan:
                record.nguyen_nhan_thua = nguyen_nhan
    
    def action_record_activity(self, loai, mo_ta=""):
        """Ghi nhận hoạt động"""
        for record in self:
            self.env['co_hoi_hoat_dong'].create({
                'co_hoi_id': record.id,
                'loai': loai,
                'mo_ta': mo_ta,
                'nguoi_thuc_hien_id': self.env.user.nhan_vien_id.id,
            })
            record.so_lan_lien_he += 1
            record.ngay_lien_he_cuoi = fields.Date.today()
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_co_hoi', _('New')) == _('New'):
                vals['ma_co_hoi'] = self.env['ir.sequence'].next_by_code('co_hoi_ban_hang') or _('New')
        return super().create(vals_list)


class CoHoiHoatDong(models.Model):
    _name = "co_hoi_hoat_dong"
    _description = "Hoạt động trên cơ hội bán hàng"
    _rec_name = "loai"
    _order = "ngay_gio desc"

    co_hoi_id = fields.Many2one('co_hoi_ban_hang', string="Cơ hội", required=True, ondelete='cascade')
    loai = fields.Selection([
        ('goi', 'Gọi'),
        ('email', 'Email'),
        ('meeting', 'Cuộc họp'),
        ('de_xuat', 'Gửi đề xuất'),
        ('cuoc_hop_video', 'Họp video'),
        ('khac', 'Khác'),
    ], string="Loại hoạt động", required=True)
    
    ngay_gio = fields.Datetime(string="Thời gian", default=fields.Datetime.now, required=True)
    nguoi_thuc_hien_id = fields.Many2one('nhan_vien', string="Người thực hiện")
    mo_ta = fields.Text(string="Mô tả")
    ket_qua = fields.Char(string="Kết quả")
