# -*- coding: utf-8 -*-

from datetime import timedelta
import uuid
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BaoGia(models.Model):
    _name = 'bao_gia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Báo giá khách hàng'
    _order = 'ngay_tao desc'
    _rec_name = 'ma_bao_gia'

    ma_bao_gia              = fields.Char(string='Mã báo giá', required=True, index=True, default=lambda self: _('New'))
    khach_hang_id           = fields.Many2one('khach_hang', string='Khách hàng', required=True, tracking=True, ondelete='cascade')
    co_hoi_id               = fields.Many2one('co_hoi_ban_hang', string='Cơ hội bán hàng', tracking=True)
    nhan_vien_phu_trach_id  = fields.Many2one('nhan_vien', string='Sales phụ trách', required=True, tracking=True)
    ngay_tao                = fields.Date(string='Ngày tạo', default=fields.Date.today, readonly=True)
    ngay_hieu_luc           = fields.Date(string='Ngày hiệu lực', required=True, tracking=True)
    ngay_het_hieu_luc       = fields.Date(string='Ngày hết hiệu lực', tracking=True)
    chi_tiet_ids            = fields.One2many('bao_gia_chi_tiet', 'bao_gia_id', string='Chi tiết báo giá')
    tong_tien_hang          = fields.Float(string='Tổng tiền hàng', compute='_compute_totals', store=True)
    chiet_khau_phan_tram    = fields.Float(string='Chiết khấu %', default=0, tracking=True)
    chiet_khau_tien         = fields.Float(string='Chiết khấu (tiền)', compute='_compute_chiet_khau', store=True)
    tien_sau_chiet_khau     = fields.Float(string='Tiền sau chiết khấu', compute='_compute_totals', store=True)
    thue_vat                = fields.Float(string='Thuế VAT %', default=10, tracking=True)
    tien_thue_vat           = fields.Float(string='Tiền thuế VAT', compute='_compute_tien_thue_vat', store=True)
    tong_tien               = fields.Float(string='TỔNG TIỀN', compute='_compute_totals', store=True)
    hinh_thuc_thanh_toan    = fields.Selection([
        ('cash', 'Tiền mặt'), ('bank_transfer', 'Chuyển khoản'),
        ('installment', 'Trả góp'), ('other', 'Khác'),
    ], string='Hình thức thanh toán', default='bank_transfer')
    so_tien_coc             = fields.Float(string='Tiền cọc (nếu có)')
    dieu_khoan              = fields.Html(string='Điều khoản')
    ghi_chu                 = fields.Text(string='Ghi chú')
    trang_thai              = fields.Selection([
        ('draft',           'Nháp'),
        ('pending_approval','Chờ duyệt'),
        ('approved',        'Đã duyệt'),
        ('sent',            'Đã gửi'),
        ('accepted',        'Được chấp nhận'),
        ('rejected',        'Bị từ chối'),
        ('expired',         'Hết hiệu lực'),
    ], string='Trạng thái', default='draft', required=True, tracking=True)
    nguoi_duyet_id          = fields.Many2one('nhan_vien', string='Người duyệt', tracking=True)
    ngay_duyet              = fields.Date(string='Ngày duyệt', tracking=True)
    # don_hang_id = fields.Many2one('don_hang', string='Đơn hàng', readonly=True)  # Removed

    # ── Task theo dõi báo giá (tự động tạo khi accepted) ──
    cong_viec_theo_doi_id   = fields.Many2one('cong_viec', string='Task theo dõi HĐ', readonly=True, copy=False)

    # ── Compute ────────────────────────────────────────────
    @api.depends('chi_tiet_ids.thanh_tien', 'chiet_khau_phan_tram', 'thue_vat')
    def _compute_totals(self):
        for r in self:
            tong = sum(r.chi_tiet_ids.mapped('thanh_tien'))
            r.tong_tien_hang = tong
            ck = tong * r.chiet_khau_phan_tram / 100
            sau_ck = tong - ck
            thue   = sau_ck * r.thue_vat / 100
            r.tien_sau_chiet_khau = sau_ck
            r.tong_tien           = sau_ck + thue

    @api.depends('tong_tien_hang', 'chiet_khau_phan_tram')
    def _compute_chiet_khau(self):
        for r in self:
            r.chiet_khau_tien = r.tong_tien_hang * r.chiet_khau_phan_tram / 100

    @api.depends('tien_sau_chiet_khau', 'thue_vat')
    def _compute_tien_thue_vat(self):
        for r in self:
            r.tien_thue_vat = r.tien_sau_chiet_khau * r.thue_vat / 100

    # ── Actions ────────────────────────────────────────────
    def action_submit_approval(self):
        for r in self:
            if r.trang_thai != 'draft':
                raise ValidationError(_('Chỉ báo giá Nháp mới gửi duyệt được!'))
            r.trang_thai = 'pending_approval'

    def action_approve(self):
        for r in self:
            if r.trang_thai != 'pending_approval':
                raise ValidationError(_('Chỉ báo giá Chờ duyệt mới được phê duyệt!'))
            r.trang_thai   = 'approved'
            r.nguoi_duyet_id = self.env.user.nhan_vien_id
            r.ngay_duyet   = fields.Date.today()

    def action_send(self):
        for r in self:
            if r.trang_thai != 'approved':
                raise ValidationError(_('Chỉ báo giá đã duyệt mới được gửi!'))
        self.trang_thai = 'sent'

    def action_mark_accepted(self):
        """Khách chấp nhận báo giá → tự động tạo Task 'Theo dõi hợp đồng'."""
        for r in self:
            if r.trang_thai != 'sent':
                raise ValidationError(_('Chỉ báo giá Đã gửi mới có thể đánh dấu chấp nhận!'))
            r.trang_thai = 'accepted'
            # ── AUTO-CREATE TASK theo dõi hợp đồng ──────────
            if not r.cong_viec_theo_doi_id:
                r._create_task_theo_doi_hop_dong()

    def _create_task_theo_doi_hop_dong(self):
        """Tạo Task 'Theo dõi hợp đồng' khi báo giá được chấp nhận."""
        self.ensure_one()
        DuAn     = self.env['du_an']
        CongViec = self.env['cong_viec']
        kh       = self.khach_hang_id
        nv       = self.nhan_vien_phu_trach_id

        du_an = DuAn.search([
            ('khach_hang_id', '=', kh.id),
            ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
        ], limit=1)
        if not du_an:
            du_an = DuAn.create({
                'ma_du_an':        self.env['ir.sequence'].next_by_code('du_an') or 'DA-NEW',
                'ten_du_an':       f'Chăm sóc KH: {kh.ten_khach_hang}',
                'ngay_bat_dau':    fields.Date.today(),
                'trang_thai':      'dang_thuc_hien',
                'khach_hang_id':   kh.id,
                'nguoi_quan_ly_id': nv.id if nv else False,
            })

        # Tạo mã công việc unique
        ma_cong_viec = self.env['ir.sequence'].next_by_code('cong_viec')
        if not ma_cong_viec:
            # Nếu sequence không hoạt động, tạo mã unique bằng UUID
            ma_cong_viec = f"CV-{uuid.uuid4().hex[:8].upper()}"

        task = CongViec.create({
            'ma_cong_viec':       ma_cong_viec,
            'ten_cong_viec':      f'[Theo dõi HĐ] Báo giá {self.ma_bao_gia} — {kh.ten_khach_hang}',
            'mo_ta':              f'Báo giá {self.ma_bao_gia} đã được chấp nhận. '
                                  f'Tổng giá trị: {self.tong_tien:,.0f} VNĐ. '
                                  f'Cần theo dõi để chuyển thành hợp đồng.',
            'du_an_id':           du_an.id,
            'nguoi_phu_trach_id': nv.id if nv else False,
            'ngay_bat_dau':       fields.Date.today(),
            'ngay_ket_thuc':      fields.Date.today() + timedelta(days=7),
            'trang_thai':         'cho_xu_ly',
            'do_uu_tien':         'cao',
        })
        self.cong_viec_theo_doi_id = task.id
        self.message_post(body=_(
            '<b>✅ Task tự động tạo:</b> <a href="/web#id=%d&model=cong_viec">%s</a>'
        ) % (task.id, task.ten_cong_viec))

    def action_convert_to_order(self):
        for r in self:
            if r.trang_thai != 'accepted':
                raise ValidationError(_('Chỉ báo giá đã chấp nhận mới chuyển được!'))
                    # don_hang = self.env['don_hang'].create({
        #                 'khach_hang_id':          r.khach_hang_id.id,
        #                 'bao_gia_id':             r.id,
        #                 'nhan_vien_phu_trach_id': r.nhan_vien_phu_trach_id.id,
        #                 'ngay_dat':               fields.Date.today(),
        #                 'hinh_thuc_thanh_toan':   r.hinh_thuc_thanh_toan,
        #             })
        #             r.don_hang_id = don_hang.id
        # 
        #     def action_view_order(self):
        #         self.ensure_one()
        #         # if not self.don_hang_id:
        
        #             return
        #         return {
        #             'name': 'Đơn hàng', 'type': 'ir.actions.act_window',
        #             'res_model': 'don_hang', 'view_mode': 'form', 'res_id': self.don_hang_id.id,
        #         }
        # 


class BaoGiaChiTiet(models.Model):
    _name = 'bao_gia_chi_tiet'
    _description = 'Chi tiết báo giá'

    bao_gia_id   = fields.Many2one('bao_gia', string='Báo giá', required=True, ondelete='cascade')
    ten_san_pham = fields.Char(string='Tên sản phẩm/Dịch vụ', required=True)
    mo_ta        = fields.Text(string='Mô tả')
    don_vi       = fields.Char(string='Đơn vị', default='Cái')
    so_luong     = fields.Float(string='Số lượng', default=1)
    don_gia      = fields.Float(string='Đơn giá')
    thanh_tien   = fields.Float(string='Thành tiền', compute='_compute_thanh_tien', store=True)

    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for r in self:
            r.thanh_tien = r.so_luong * r.don_gia