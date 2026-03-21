# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class BaoGia(models.Model):
    """Quotation/Proposal"""
    _name = "bao_gia"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Báo giá khách hàng"
    _rec_name = "ma_bao_gia"
    _order = "ngay_tao desc"

    ma_bao_gia = fields.Char(string="Mã báo giá", required=True, index=True, default=lambda self: _('New'))
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    co_hoi_id = fields.Many2one('co_hoi_ban_hang', string="Cơ hội bán hàng", tracking=True)
    
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Sales phụ trách", required=True, tracking=True)
    
    # Thời gian
    ngay_tao = fields.Date(string="Ngày tạo", default=fields.Date.today, readonly=True)
    ngay_hieu_luc = fields.Date(string="Ngày hiệu lực", required=True, tracking=True)
    ngay_het_hieu_luc = fields.Date(string="Ngày hết hiệu lực", tracking=True, help="Báo giá hết hiệu lực sau ngày này")
    
    # Chi tiết
    chi_tiet_ids = fields.One2many('bao_gia_chi_tiet', 'bao_gia_id', string="Chi tiết báo giá")
    
    # Tính toán
    tong_tien_hang = fields.Float(string="Tổng tiền hàng", compute="_compute_totals", store=True)
    chiet_khau_phan_tram = fields.Float(string="Chiết khấu %", default=0, tracking=True)
    chiet_khau_tien = fields.Float(string="Chiết khấu (tiền)", compute="_compute_chiet_khau", store=True)
    tien_sau_chiet_khau = fields.Float(string="Tiền sau chiết khấu", compute="_compute_totals", store=True)
    thue_vat = fields.Float(string="Thuế VAT %", default=10, tracking=True)
    tien_thue_vat = fields.Float(string="Tiền thuế VAT", compute="_compute_tien_thue_vat", store=True)
    tong_tien = fields.Float(string="TỔNG TIỀN", compute="_compute_totals", store=True)
    
    # Hình thức & Điều khoản
    hinh_thuc_thanh_toan = fields.Selection([
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('tra_gop', 'Trả góp'),
        ('khac', 'Khác'),
    ], string="Hình thức thanh toán", default='chuyen_khoan', tracking=True)
    
    so_tien_coc = fields.Float(string="Tiền cọc (nếu có)")
    dieu_khoan = fields.Html(string="Điều khoản")
    
    # Ghi chú
    ghi_chu = fields.Text(string="Ghi chú")
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('pending_approval', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('sent', 'Đã gửi'),
        ('accepted', 'Khách chấp nhận'),
        ('rejected', 'Khách từ chối'),
        ('expired', 'Hết hiệu lực'),
        ('converted', 'Chuyển sang đơn hàng'),
    ], string="Trạng thái", default='draft', tracking=True)
    
    # Phê duyệt
    nguoi_duyet_id = fields.Many2one('nhan_vien', string="Người duyệt", tracking=True)
    ngay_duyet = fields.Date(string="Ngày duyệt", tracking=True)
    
    # Chuyển đơn hàng
    don_hang_id = fields.Many2one('don_hang', string="Đơn hàng", readonly=True)
    
    @api.depends('chi_tiet_ids.thanh_tien')
    def _compute_totals(self):
        for record in self:
            record.tong_tien_hang = sum(record.chi_tiet_ids.mapped('thanh_tien'))
            record.tien_sau_chiet_khau = record.tong_tien_hang - record.chiet_khau_tien
            record.tong_tien = record.tien_sau_chiet_khau + record.tien_thue_vat
    
    @api.depends('tong_tien_hang', 'chiet_khau_phan_tram')
    def _compute_chiet_khau(self):
        for record in self:
            record.chiet_khau_tien = record.tong_tien_hang * record.chiet_khau_phan_tram / 100.0
    
    @api.depends('tien_sau_chiet_khau', 'thue_vat')
    def _compute_tien_thue_vat(self):
        for record in self:
            record.tien_thue_vat = record.tien_sau_chiet_khau * record.thue_vat / 100.0
    
    @api.constrains('ngay_hieu_luc', 'ngay_het_hieu_luc')
    def _check_dates(self):
        for record in self:
            if record.ngay_het_hieu_luc and record.ngay_hieu_luc > record.ngay_het_hieu_luc:
                raise ValidationError(_("Ngày hết hiệu lực phải sau ngày hiệu lực!"))
    
    def action_submit_approval(self):
        """Nộp duyệt báo giá"""
        for record in self:
            if record.trang_thai != 'draft':
                raise ValidationError(_("Chỉ báo giá ở trạng thái Nháp mới được nộp duyệt!"))
        self.trang_thai = 'pending_approval'
    
    def action_approve(self):
        """Duyệt báo giá"""
        for record in self:
            if record.trang_thai != 'pending_approval':
                raise ValidationError(_("Chỉ báo giá Chờ duyệt mới được phê duyệt!"))
            record.trang_thai = 'approved'
            record.nguoi_duyet_id = self.env.user.nhan_vien_id
            record.ngay_duyet = fields.Date.today()
    
    def action_send(self):
        """Gửi báo giá cho khách"""
        for record in self:
            if record.trang_thai != 'approved':
                raise ValidationError(_("Chỉ báo giá đã duyệt mới được gửi!"))
        self.trang_thai = 'sent'
    
    def action_mark_accepted(self):
        """Khách chấp nhận báo giá"""
        for record in self:
            if record.trang_thai != 'sent':
                raise ValidationError(_("Chỉ báo giá Đã gửi mới có thể đánh dấu chấp nhận!"))
        self.trang_thai = 'accepted'
        # Có thể auto-create đơn hàng
    
    def action_convert_to_order(self):
        """Chuyển báo giá thành đơn hàng"""
        for record in self:
            if record.trang_thai != 'accepted':
                raise ValidationError(_("Chỉ báo giá đã chấp nhận mới được chuyển sang đơn hàng!"))

            # Tạo đơn hàng từ báo giá
            don_hang = self.env['don_hang'].create({
                'khach_hang_id': record.khach_hang_id.id,
                'bao_gia_id': record.id,
                'nhan_vien_phu_trach_id': record.nhan_vien_phu_trach_id.id,
                'ngay_dat': fields.Date.today(),
                'hinh_thuc_thanh_toan': record.hinh_thuc_thanh_toan,
                'so_tien_coc': record.so_tien_coc,
            })

            # Copy chi tiết
            for chi_tiet in record.chi_tiet_ids:
                self.env['don_hang_chi_tiet'].create({
                    'don_hang_id': don_hang.id,
                    'san_pham': chi_tiet.san_pham,
                    'mo_ta': chi_tiet.mo_ta,
                    'don_vi_tinh': chi_tiet.don_vi_tinh,
                    'so_luong': chi_tiet.so_luong,
                    'gia_ban': chi_tiet.gia_ban,
                    'thanh_tien': chi_tiet.thanh_tien,
                })

            record.don_hang_id = don_hang.id
            record.trang_thai = 'converted'
    
    def action_view_order(self):
        """View related sales order"""
        if self.don_hang_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'don_hang',
                'res_id': self.don_hang_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {}
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_bao_gia', _('New')) == _('New'):
                vals['ma_bao_gia'] = self.env['ir.sequence'].next_by_code('bao_gia') or _('New')
        return super().create(vals_list)


class BaoGiaChiTiet(models.Model):
    """Quotation Line"""
    _name = "bao_gia_chi_tiet"
    _description = "Chi tiết báo giá"
    _rec_name = "san_pham"

    bao_gia_id = fields.Many2one('bao_gia', string="Báo giá", required=True, ondelete='cascade')
    
    san_pham = fields.Char(string="Sản phẩm/Dịch vụ", required=True)
    mo_ta = fields.Text(string="Mô tả chi tiết")
    don_vi_tinh = fields.Char(string="Đơn vị tính", default="Cái")
    so_luong = fields.Float(string="Số lượng", required=True, default=1)
    gia_ban = fields.Float(string="Giá bán/đơn vị", required=True)
    
    thanh_tien = fields.Float(string="Thành tiền", compute="_compute_thanh_tien", store=True)
    
    @api.depends('so_luong', 'gia_ban')
    def _compute_thanh_tien(self):
        for record in self:
            record.thanh_tien = record.so_luong * record.gia_ban


class DonHang(models.Model):
    """Sales Order"""
    _name = "don_hang"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Đơn hàng"
    _rec_name = "ma_don_hang"
    _order = "ngay_dat desc"

    ma_don_hang = fields.Char(string="Mã đơn hàng", required=True, index=True, default=lambda self: _('New'))
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    bao_gia_id = fields.Many2one('bao_gia', string="Báo giá gốc", readonly=True)
    
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Sales", required=True, tracking=True)
    
    # Thời gian
    ngay_dat = fields.Date(string="Ngày đặt", default=fields.Date.today, tracking=True)
    ngay_giao_du_kinh = fields.Date(string="Ngày giao dự kiến", tracking=True)
    ngay_giao_thuc_te = fields.Date(string="Ngày giao thực tế", tracking=True)
    
    # Chi tiết
    chi_tiet_ids = fields.One2many('don_hang_chi_tiet', 'don_hang_id', string="Chi tiết đơn hàng")
    
    # Tính toán
    tong_tien_hang = fields.Float(string="Tổng tiền hàng", compute="_compute_totals", store=True)
    chiet_khau_phan_tram = fields.Float(string="Chiết khấu %", default=0, tracking=True)
    chiet_khau_tien = fields.Float(string="Chiết khấu", compute="_compute_chiet_khau", store=True)
    tien_sau_chiet_khau = fields.Float(string="Tiền sau chiết khấu", compute="_compute_totals", store=True)
    thue_vat = fields.Float(string="Thuế VAT %", default=10, tracking=True)
    tien_thue_vat = fields.Float(string="Tiền thuế VAT", compute="_compute_tien_thue_vat", store=True)
    tong_tien = fields.Float(string="TỔNG TIỀN", compute="_compute_totals", store=True)
    
    so_tien_coc = fields.Float(string="Tiền cọc đã nhận")
    so_tien_con_no = fields.Float(string="Tiền còn nợ", compute="_compute_con_no", store=True)
    
    # Hình thức thanh toán
    hinh_thuc_thanh_toan = fields.Selection([
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('tra_gop', 'Trả góp'),
        ('khac', 'Khác'),
    ], string="Hình thức thanh toán", default='chuyen_khoan', tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('in_delivery', 'Đang giao'),
        ('delivered', 'Đã giao'),
        ('invoiced', 'Đã phát hóa đơn'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Hủy'),
    ], string="Trạng thái", default='draft', tracking=True)
    
    ghi_chu = fields.Text(string="Ghi chú")
    
    @api.depends('chi_tiet_ids.thanh_tien')
    def _compute_totals(self):
        for record in self:
            record.tong_tien_hang = sum(record.chi_tiet_ids.mapped('thanh_tien'))
            record.tien_sau_chiet_khau = record.tong_tien_hang - record.chiet_khau_tien
            record.tong_tien = record.tien_sau_chiet_khau + record.tien_thue_vat
    
    @api.depends('tong_tien_hang', 'chiet_khau_phan_tram')
    def _compute_chiet_khau(self):
        for record in self:
            record.chiet_khau_tien = record.tong_tien_hang * record.chiet_khau_phan_tram / 100.0
    
    @api.depends('tien_sau_chiet_khau', 'thue_vat')
    def _compute_tien_thue_vat(self):
        for record in self:
            record.tien_thue_vat = record.tien_sau_chiet_khau * record.thue_vat / 100.0
    
    @api.depends('tong_tien', 'so_tien_coc')
    def _compute_con_no(self):
        for record in self:
            record.so_tien_con_no = record.tong_tien - record.so_tien_coc
    
    def action_confirm(self):
        """Xác nhận đơn hàng"""
        for record in self:
            if record.trang_thai != 'draft':
                raise ValidationError(_("Chỉ đơn hàng Nháp mới được xác nhận!"))
        self.trang_thai = 'confirmed'
    
    def action_deliver(self):
        """Giao hàng"""
        for record in self:
            if record.trang_thai != 'confirmed':
                raise ValidationError(_("Chỉ đơn hàng Đã xác nhận mới chuyển sang Đang giao!"))
            record.trang_thai = 'in_delivery'
            record.ngay_giao_thuc_te = fields.Date.today()
    
    def action_mark_delivered(self):
        """Đánh dấu đã giao"""
        for record in self:
            if record.trang_thai != 'in_delivery':
                raise ValidationError(_("Chỉ đơn hàng Đang giao mới đánh dấu Đã giao được!"))
        self.trang_thai = 'delivered'
    
    def action_invoice(self):
        """Phát hóa đơn"""
        for record in self:
            if record.trang_thai != 'delivered':
                raise ValidationError(_("Chỉ đơn hàng Đã giao mới phát hóa đơn được!"))
        self.trang_thai = 'invoiced'
    
    def action_mark_paid(self):
        """Đánh dấu đã thanh toán"""
        for record in self:
            if record.trang_thai != 'invoiced':
                raise ValidationError(_("Chỉ đơn hàng Đã phát hóa đơn mới đánh dấu thanh toán được!"))
        self.trang_thai = 'paid'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_don_hang', _('New')) == _('New'):
                vals['ma_don_hang'] = self.env['ir.sequence'].next_by_code('don_hang') or _('New')
        return super().create(vals_list)


class DonHangChiTiet(models.Model):
    """Sales Order Line"""
    _name = "don_hang_chi_tiet"
    _description = "Chi tiết đơn hàng"

    don_hang_id = fields.Many2one('don_hang', string="Đơn hàng", required=True, ondelete='cascade')
    
    san_pham = fields.Char(string="Sản phẩm/Dịch vụ", required=True)
    mo_ta = fields.Text(string="Mô tả")
    don_vi_tinh = fields.Char(string="Đơn vị tính", default="Cái")
    so_luong = fields.Float(string="Số lượng", required=True)
    gia_ban = fields.Float(string="Giá bán", required=True)
    
    thanh_tien = fields.Float(string="Thành tiền", compute="_compute_thanh_tien", store=True)
    
    @api.depends('so_luong', 'gia_ban')
    def _compute_thanh_tien(self):
        for record in self:
            record.thanh_tien = record.so_luong * record.gia_ban
