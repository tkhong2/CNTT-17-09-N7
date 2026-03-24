# -*- coding: utf-8 -*-

import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class HopDongKhachHang(models.Model):
    """Customer Contract"""
    _name = "hop_dong_khach_hang"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hợp đồng khách hàng"
    _rec_name = "ma_hop_dong"
    _order = "ngay_ky_ket desc"

    ma_hop_dong = fields.Char(string="Mã hợp đồng", required=True, index=True, default=lambda self: _('New'))
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    # don_hang_id removed
    
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Sales phụ trách", required=True, tracking=True)
    
    # Thông tin hợp đồng
    tieu_de = fields.Char(string="Tiêu đề", required=True, tracking=True)
    mo_ta_cong_viec = fields.Html(string="Mô tả công việc/Phạm vi cung cấp")
    
    # Thời gian
    ngay_ky_ket = fields.Date(string="Ngày ký kết", required=True, tracking=True)
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True, tracking=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc", required=True, tracking=True)
    thoi_gian_gia_han = fields.Integer(string="Thời gian gia hạn (tháng)", default=0)
    
    # Tài chính
    gia_tri_hop_dong = fields.Float(string="Giá trị hợp đồng", required=True, tracking=True)
    tien_coc_thanh_toan = fields.Float(string="Tiền cọc/Thanh toán lần 1", tracking=True)
    tien_con_lai = fields.Float(string="Tiền còn lại", compute="_compute_con_lai", store=True)
    
    # Điều khoản
    dieu_khoan = fields.Html(string="Điều khoản & Điều kiện")
    phuong_thuc_thanh_toan = fields.Selection([
        ('hang_thang', 'Hàng tháng'),
        ('hang_quy', 'Hàng quý'),
        ('hang_nam', 'Hàng năm'),
        ('mot_lan', 'Một lần'),
    ], string="Phương thức thanh toán", default='hang_thang', tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('pending_signature', 'Chờ ký kết'),
        ('signed', 'Đã ký kết'),
        ('executing', 'Đang thực hiện'),
        ('completed', 'Hoàn thành'),
        ('extended', 'Đã gia hạn'),
        ('terminated', 'Kết thúc sớm'),
    ], string="Trạng thái", default='draft', tracking=True)
    
    ngay_ky_ket_thuc_te = fields.Date(string="Ngày ký kết thực tế", tracking=True)
    
    # Nhắc nhở gia hạn
    nhac_nho_gia_han = fields.Boolean(string="Cần nhắc nhở gia hạn", compute="_check_renewal", store=True)
    
    ghi_chu = fields.Text(string="Ghi chú")
    
    @api.depends('gia_tri_hop_dong', 'tien_coc_thanh_toan')
    def _compute_con_lai(self):
        for record in self:
            record.tien_con_lai = record.gia_tri_hop_dong - record.tien_coc_thanh_toan
    
    @api.depends('ngay_ket_thuc')
    def _check_renewal(self):
        today = fields.Date.today()
        for record in self:
            if record.ngay_ket_thuc:
                days_left = (record.ngay_ket_thuc - today).days
                record.nhac_nho_gia_han = days_left <= 30 and days_left > 0
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_bat_dau > record.ngay_ket_thuc:
                raise ValidationError(_("Ngày kết thúc phải sau ngày bắt đầu!"))
    
    def action_ready_signature(self):
        """Sẵn sàng ký kết"""
        for record in self:
            if record.trang_thai != 'draft':
                raise ValidationError(_("Chỉ hợp đồng Nháp mới chuyển sang Chờ ký kết!"))
        self.trang_thai = 'pending_signature'
    
    def action_sign(self):
        """Xác nhận ký kết"""
        for record in self:
            if record.trang_thai != 'pending_signature':
                raise ValidationError(_("Chỉ hợp đồng Chờ ký kết mới xác nhận ký được!"))
            record.trang_thai = 'signed'
            record.ngay_ky_ket_thuc_te = fields.Date.today()
    
    def action_start_execution(self):
        """Bắt đầu thực hiện"""
        for record in self:
            if record.trang_thai != 'signed':
                raise ValidationError(_("Chỉ hợp đồng đã ký kết mới được thực hiện!"))
        self.trang_thai = 'executing'
    
    def action_complete(self):
        """Hoàn thành hợp đồng"""
        for record in self:
            if record.trang_thai != 'executing':
                raise ValidationError(_("Chỉ hợp đồng Đang thực hiện mới hoàn thành được!"))
        self.trang_thai = 'completed'
    
    def action_extend(self):
        """Gia hạn hợp đồng"""
        for record in self:
            if record.trang_thai not in ['executing', 'completed']:
                raise ValidationError(_("Chỉ hợp đồng đang thực hiện hoặc hoàn thành mới có thể gia hạn!"))
            # Tính ngày kết thúc mới
            so_thang = record.thoi_gian_gia_han or 12
            ngay_ket_thuc_moi = record.ngay_ket_thuc + timedelta(days=30 * so_thang)
            record.ngay_ket_thuc = ngay_ket_thuc_moi
            record.trang_thai = 'extended'
    
    def action_terminate(self):
        """Kết thúc sớm hợp đồng"""
        for record in self:
            if record.trang_thai in ['terminated', 'completed']:
                raise ValidationError(_("Không thể kết thúc sớm hợp đồng đã hoàn tất!"))
        self.trang_thai = 'terminated'
    
    def action_view_renewal_alert(self):
        """View renewal alert/reminder for contract expiration"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Renewal Alert'),
            'res_model': 'hop_dong_khach_hang',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_hop_dong', _('New')) == _('New'):
                vals['ma_hop_dong'] = self.env['ir.sequence'].next_by_code('hop_dong_khach_hang') or _('New')
        return super().create(vals_list)


    @api.model
    def _cron_tao_task_nhac_nho_het_han(self):
        """Cron: Tạo Task nhắc nhở cho nhân viên khi hợp đồng sắp hết hạn (<=30 ngày)."""
        from datetime import timedelta as td
        today    = fields.Date.today()
        deadline = today + td(days=30)

        sap_het_han = self.search([
            ('trang_thai', 'in', ['signed', 'executing', 'extended']),
            ('ngay_ket_thuc', '>=', today),
            ('ngay_ket_thuc', '<=', deadline),
            ('nhac_nho_gia_han', '=', True),
        ])

        DuAn     = self.env['du_an']
        CongViec = self.env['cong_viec']

        for hd in sap_het_han:
            kh = hd.khach_hang_id
            nv = hd.nhan_vien_phu_trach_id

            # Kiểm tra đã có task nhắc nhở chưa
            existing = CongViec.search([
                ('ten_cong_viec', 'ilike', f'[Gia hạn HĐ] {hd.ma_hop_dong}'),
                ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
            ], limit=1)
            if existing:
                continue

            du_an = DuAn.search([
                ('khach_hang_id', '=', kh.id),
                ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
            ], limit=1)
            if not du_an:
                du_an = DuAn.create({
                    'ma_du_an':        self.env['ir.sequence'].next_by_code('du_an') or 'DA-NEW',
                    'ten_du_an':       f'Chăm sóc KH: {kh.ten_khach_hang}',
                    'ngay_bat_dau':    today,
                    'trang_thai':      'dang_thuc_hien',
                    'khach_hang_id':   kh.id,
                    'nguoi_quan_ly_id': nv.id if nv else False,
                })

            days_left = (hd.ngay_ket_thuc - today).days
            # Tạo mã công việc unique
            ma_cong_viec = self.env['ir.sequence'].next_by_code('cong_viec')
            if not ma_cong_viec:
                # Nếu sequence không hoạt động, tạo mã unique bằng UUID
                ma_cong_viec = f"CV-{uuid.uuid4().hex[:8].upper()}"

            CongViec.create({
                'ma_cong_viec':       ma_cong_viec,
                'ten_cong_viec':      f'[Gia hạn HĐ] {hd.ma_hop_dong} — {kh.ten_khach_hang} (còn {days_left} ngày)',
                'mo_ta':              f'Hợp đồng <b>{hd.ma_hop_dong}</b> — {hd.tieu_de}<br/>'
                                      f'Khách hàng: {kh.ten_khach_hang}<br/>'
                                      f'Ngày kết thúc: {hd.ngay_ket_thuc}<br/>'
                                      f'Còn <b>{days_left} ngày</b>. Liên hệ khách hàng để gia hạn hoặc đóng hợp đồng.',
                'du_an_id':           du_an.id,
                'nguoi_phu_trach_id': nv.id if nv else False,
                'ngay_bat_dau':       today,
                'ngay_ket_thuc':      hd.ngay_ket_thuc,
                'trang_thai':         'cho_xu_ly',
                'do_uu_tien':         'cao',
            })

            hd.message_post(body=_(
                '⚠️ <b>Task nhắc nhở gia hạn tự động tạo</b> — còn %d ngày đến hạn hợp đồng.'
            ) % days_left)


class YeuCauHoTro(models.Model):
    """Support Request / Ticket"""
    _name = "yeu_cau_ho_tro"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Yêu cầu hỗ trợ / Ticket chăm sóc khách hàng"
    _rec_name = "ma_yeu_cau"
    _order = "ngay_tao desc"

    ma_yeu_cau = fields.Char(string="Mã yêu cầu", required=True, index=True, default=lambda self: _('New'))
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    hop_dong_id = fields.Many2one('hop_dong_khach_hang', string="Hợp đồng liên quan", tracking=True)
    
    nguoi_dal_yeu_cau = fields.Char(string="Người đặt yêu cầu", tracking=True)
    dien_thoai_lien_he = fields.Char(string="Điện thoại liên hệ")
    email_lien_he = fields.Char(string="Email liên hệ")
    
    # Chi tiết yêu cầu
    loai_yeu_cau = fields.Selection([
        ('bao_cao_loi', 'Báo cáo lỗi'),
        ('yeu_cau_thay_doi', 'Yêu cầu thay đổi'),
        ('ho_tro_ky_thuat', 'Hỗ trợ kỹ thuật'),
        ('tu_van_san_pham', 'Tư vấn sản phẩm'),
        ('khieu_nai', 'Khiếu nại'),
        ('khác', 'Khác'),
    ], string="Loại yêu cầu", required=True, tracking=True)
    
    tieu_de = fields.Char(string="Tiêu đề yêu cầu", required=True, tracking=True)
    mo_ta_chi_tiet = fields.Html(string="Mô tả chi tiết", required=True)
    
    # Ưu tiên & Độ nghiêm trọng
    uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp'),
    ], string="Độ ưu tiên", default='trung_binh', tracking=True)
    
    # Thời gian
    ngay_tao = fields.Date(string="Ngày tạo", default=fields.Date.today, readonly=True)
    ngay_tao_datetime = fields.Datetime(string="Thời điểm tạo", default=fields.Datetime.now, readonly=True)
    ngay_hen_tra_loi = fields.Date(string="Ngày hẹn trả lời", tracking=True)
    ngay_tra_loi = fields.Date(string="Ngày trả lời", tracking=True)
    ngay_giai_quyet = fields.Date(string="Ngày giải quyết", tracking=True)
    sla_gio = fields.Integer(string="SLA (giờ)", default=24, tracking=True)
    han_sla = fields.Datetime(string="Hạn SLA", compute="_compute_sla", store=True)
    qua_han_sla = fields.Boolean(string="Quá hạn SLA", compute="_compute_sla", store=True)
    thoi_gian_xu_ly_gio = fields.Float(string="Thời gian xử lý (giờ)", compute="_compute_thoi_gian_xu_ly", store=True)
    
    # Xử lý
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách", tracking=True)
    ghi_chu_ho_tro = fields.Html(string="Ghi chú hỗ trợ")
    ket_qua_giai_quyet = fields.Html(string="Kết quả giải quyết")
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('new', 'Mới'),
        ('assigned', 'Đã gán'),
        ('in_progress', 'Đang xử lý'),
        ('waiting_customer', 'Chờ phản hồi khách'),
        ('resolved', 'Đã giải quyết'),
        ('closed', 'Đóng'),
    ], string="Trạng thái", default='new', tracking=True)
    
    # Mức độ hài lòng
    danh_gia_kham_pha = fields.Selection([
        ('1', '1 - Rất không hài lòng'),
        ('2', '2 - Không hài lòng'),
        ('3', '3 - Bình thường'),
        ('4', '4 - Hài lòng'),
        ('5', '5 - Rất hài lòng'),
    ], string="Đánh giá hài lòng", tracking=True)
    
    phan_hoi_them = fields.Text(string="Phản hồi thêm")

    @api.depends('ngay_tao_datetime', 'sla_gio', 'trang_thai')
    def _compute_sla(self):
        now_dt = fields.Datetime.now()
        for record in self:
            if record.ngay_tao_datetime and record.sla_gio:
                han_sla = record.ngay_tao_datetime + timedelta(hours=record.sla_gio)
                record.han_sla = han_sla
                record.qua_han_sla = record.trang_thai not in ['resolved', 'closed'] and now_dt > han_sla
            else:
                record.han_sla = False
                record.qua_han_sla = False

    @api.depends('ngay_tao_datetime', 'ngay_giai_quyet', 'trang_thai')
    def _compute_thoi_gian_xu_ly(self):
        now_dt = fields.Datetime.now()
        for record in self:
            if not record.ngay_tao_datetime:
                record.thoi_gian_xu_ly_gio = 0.0
                continue

            if record.trang_thai in ['resolved', 'closed'] and record.ngay_giai_quyet:
                moc_ket_thuc = fields.Datetime.to_datetime(record.ngay_giai_quyet)
            else:
                moc_ket_thuc = now_dt

            record.thoi_gian_xu_ly_gio = max((moc_ket_thuc - record.ngay_tao_datetime).total_seconds() / 3600.0, 0.0)
    
    @api.onchange('loai_yeu_cau')
    def _onchange_loai_yeu_cau(self):
        if self.loai_yeu_cau == 'bao_cao_loi':
            self.uu_tien = 'cao'
        elif self.loai_yeu_cau == 'khieu_nai':
            self.uu_tien = 'khan_cap'

    @api.onchange('uu_tien')
    def _onchange_uu_tien(self):
        sla_by_priority = {
            'thap': 72,
            'trung_binh': 48,
            'cao': 24,
            'khan_cap': 8,
        }
        if self.uu_tien:
            self.sla_gio = sla_by_priority.get(self.uu_tien, 24)
    
    def action_assign(self):
        """Gán yêu cầu cho nhân viên"""
        for record in self:
            if record.trang_thai != 'new':
                raise ValidationError(_("Chỉ yêu cầu Mới mới được gán xử lý!"))
            if not record.nhan_vien_phu_trach_id:
                raise ValidationError(_("Vui lòng chọn nhân viên phụ trách!"))
            record.trang_thai = 'assigned'
    
    def action_start_process(self):
        """Bắt đầu xử lý"""
        for record in self:
            if record.trang_thai != 'assigned':
                raise ValidationError(_("Chỉ yêu cầu Đã gán mới bắt đầu xử lý được!"))
        self.trang_thai = 'in_progress'
    
    def action_wait_customer(self):
        """Chờ phản hồi khách"""
        for record in self:
            if record.trang_thai != 'in_progress':
                raise ValidationError(_("Chỉ yêu cầu Đang xử lý mới chuyển sang Chờ phản hồi khách được!"))
        self.trang_thai = 'waiting_customer'
    
    def action_resolve(self):
        """Đánh dấu đã giải quyết"""
        for record in self:
            if record.trang_thai not in ['waiting_customer', 'in_progress']:
                raise ValidationError(_("Chỉ yêu cầu Đang xử lý/Chờ phản hồi mới được giải quyết!"))
            record.trang_thai = 'resolved'
            if not record.ngay_tra_loi:
                record.ngay_tra_loi = fields.Date.today()
            record.ngay_giai_quyet = fields.Date.today()
    
    def action_close(self):
        """Đóng yêu cầu"""
        for record in self:
            if record.trang_thai != 'resolved':
                raise ValidationError(_("Chỉ yêu cầu đã giải quyết mới có thể đóng!"))
        self.trang_thai = 'closed'
    
    @api.model_create_multi
    def create(self, vals_list):
        sla_by_priority = {
            'thap': 72,
            'trung_binh': 48,
            'cao': 24,
            'khan_cap': 8,
        }
        for vals in vals_list:
            if vals.get('ma_yeu_cau', _('New')) == _('New'):
                vals['ma_yeu_cau'] = self.env['ir.sequence'].next_by_code('yeu_cau_ho_tro') or _('New')
            if not vals.get('sla_gio'):
                priority = vals.get('uu_tien', 'trung_binh')
                vals['sla_gio'] = sla_by_priority.get(priority, 48)
        return super().create(vals_list)


class HoatDongSales(models.Model):
    """Sales Activities / Follow-up Log"""
    _name = "hoat_dong_sales"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hoạt động Sales / Nhật ký follow-up"
    _rec_name = "tieu_de"
    _order = "ngay_tao desc"

    # Liên kết
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    co_hoi_id = fields.Many2one('co_hoi_ban_hang', string="Cơ hội bán hàng", tracking=True)
    bao_gia_id = fields.Many2one('bao_gia', string="Báo giá", tracking=True)
    # don_hang_id removed
    
    nhan_vien_thuc_hien_id = fields.Many2one('nhan_vien', string="Nhân viên thực hiện", default=lambda self: self.env.user.nhan_vien_id, tracking=True)
    
    # Chi tiết
    tieu_de = fields.Char(string="Tiêu đề hoạt động", required=True, tracking=True)
    loai_hoat_dong = fields.Selection([
        ('goi_dien', 'Gọi điện'),
        ('gap_truc_tiep', 'Gặp trực tiếp'),
        ('email', 'Email'),
        ('hop_truc_tuyen', 'Họp trực tuyến'),
        ('sms_tin_nhan', 'SMS/Tin nhắn'),
        ('demo_san_pham', 'Demo sản phẩm'),
        ('dieu_hanh_hop_dong', 'Điều hành hợp đồng'),
        ('bao_cao_tien_do', 'Báo cáo tiến độ'),
        ('khac', 'Khác'),
    ], string="Loại hoạt động", required=True, tracking=True)
    
    mo_ta_hoat_dong = fields.Html(string="Mô tả hoạt động")
    ket_qua = fields.Html(string="Kết quả / Kết luận")
    
    # Thời gian
    ngay_tao = fields.Date(string="Ngày tạo", default=fields.Date.today, readonly=True)
    gio_tao = fields.Float(string="Giờ tạo", default=lambda self: fields.Datetime.now().hour)
    ngay_hop_len = fields.Date(string="Ngày hẹn tiếp theo", tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('planned', 'Kế hoạch'),
        ('completed', 'Hoàn thành'),
        ('rescheduled', 'Lần lại'),
        ('cancelled', 'Hủy'),
    ], string="Trạng thái", default='planned', tracking=True)
    
    # Nhen cấp
    muc_do_quan_tro_ng = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
    ], string="Mức độ quan trọng", default='trung_binh', tracking=True)
    
    # Input/Output
    dau_vao = fields.Html(string="Đầu vào (câu hỏi, chủ đề)")
    dau_ra = fields.Html(string="Đầu ra (quyết định, hành động)")
    
    # Đánh giá sau hoạt động
    danh_gia_khach = fields.Selection([
        ('rat_tich_cuc', 'Rất tích cực'),
        ('tich_cuc', 'Tích cực'),
        ('trung_lap', 'Trung lập'),
        ('tieu_cuc', 'Tiêu cực'),
    ], string="Đánh giá khách hàng", tracking=True)
    
    ghi_chu = fields.Text(string="Ghi chú")
    
    def action_complete(self):
        """Đánh dấu hoàn thành"""
        for record in self:
            if record.trang_thai != 'planned':
                raise ValidationError(_("Chỉ hoạt động ở trạng thái Kế hoạch mới hoàn thành được!"))
        self.trang_thai = 'completed'
    
    def action_reschedule(self):
        """Sắp xếp lại"""
        for record in self:
            if record.trang_thai != 'planned':
                raise ValidationError(_("Chỉ hoạt động ở trạng thái Kế hoạch mới lập lịch lại được!"))
        if not self.ngay_hop_len:
            raise ValidationError(_("Vui lòng chọn ngày hẹn tiếp theo!"))
        self.trang_thai = 'rescheduled'
    
    def action_cancel(self):
        """Hủy hoạt động"""
        for record in self:
            if record.trang_thai == 'completed':
                raise ValidationError(_("Không thể hủy hoạt động đã hoàn thành!"))
        self.trang_thai = 'cancelled'