# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DuAnIssue(models.Model):
    """Issue Management"""
    _name = "du_an_issue"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quản lý vấn đề dự án"
    _rec_name = "tieu_de"
    _order = "do_uu_tien desc, ngay_phat_sinh desc"

    du_an_id = fields.Many2one('du_an', string="Dự án", required=True, ondelete='cascade', tracking=True)
    tieu_de = fields.Char(string="Tiêu đề issue", required=True, tracking=True)
    mo_ta = fields.Text(string="Mô tả vấn đề")
    
    # Phân loại
    loai_issue = fields.Selection([
        ('technical', 'Kỹ thuật'),
        ('business', 'Kinh doanh'),
        ('resource', 'Nhân sự'),
        ('external', 'Yếu tố bên ngoài'),
        ('khac', 'Khác'),
    ], string="Loại issue", required=True, tracking=True)
    
    # Mức độ ưu tiên
    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('rat_cao', 'Rất cao (Blocker)'),
    ], string="Độ ưu tiên", default='trung_binh', tracking=True)
    
    # Ảnh hưởng
    cong_viec_bi_ảnh_huong_ids = fields.Many2many('cong_viec', string="Công việc bị ảnh hưởng")
    
    # Người phụ trách
    nguoi_phat_sinh_id = fields.Many2one('nhan_vien', string="Người phát sinh issue", tracking=True)
    nguoi_xu_ly_id = fields.Many2one('nhan_vien', string="Người xử lý", tracking=True)
    
    # Timeline
    ngay_phat_sinh = fields.Date(string="Ngày phát sinh", default=fields.Date.today, tracking=True)
    ngay_deadline = fields.Date(string="Deadline xử lý", tracking=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc", tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('open', 'Mở'),
        ('in_progress', 'Đang xử lý'),
        ('pending', 'Chờ xử lý bên ngoài'),
        ('resolved', 'Đã giải quyết'),
        ('closed', 'Đóng'),
    ], string="Trạng thái", default='open', tracking=True)
    
    # Liên kết với rủi ro
    rui_ro_id = fields.Many2one('du_an_rui_ro', string="Rủi ro gây ra")
    
    # Giải pháp
    giai_phap = fields.Text(string="Giải pháp xử lý")
    ghi_chu = fields.Text(string="Ghi chú")
    
    # Xem issue có blocked task nào không
    blocked_tasks = fields.Many2many('cong_viec', compute="_compute_blocked_tasks", string="Task bị blocked")
    
    @api.depends('do_uu_tien')
    def _compute_blocked_tasks(self):
        """Lấy các task bị blocked vì issue này"""
        for record in self:
            record.blocked_tasks = record.cong_viec_bi_ảnh_huong_ids.filtered(lambda x: x.bi_chan)
    
    def action_start_resolution(self):
        """Bắt đầu giải quyết"""
        for record in self:
            if record.trang_thai != 'open':
                raise ValidationError(_("Chỉ issue ở trạng thái Mở mới bắt đầu xử lý được!"))
        self.trang_thai = 'in_progress'
    
    def action_resolve(self):
        """Đánh dấu đã giải quyết"""
        for record in self:
            if record.trang_thai != 'in_progress':
                raise ValidationError(_("Chỉ issue đang xử lý mới có thể đánh dấu giải quyết!"))
            record.trang_thai = 'resolved'
            record.ngay_ket_thuc = fields.Date.today()
    
    def action_close(self):
        """Đóng issue"""
        for record in self:
            if record.trang_thai != 'resolved':
                raise ValidationError(_("Chỉ issue đã giải quyết mới có thể đóng!"))
        self.trang_thai = 'closed'
