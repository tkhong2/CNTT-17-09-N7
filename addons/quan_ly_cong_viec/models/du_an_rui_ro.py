# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DuAnRuiRo(models.Model):
    """Risk Management"""
    _name = "du_an_rui_ro"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quản lý rủi ro dự án"
    _rec_name = "ten_rui_ro"
    _order = "diem_rui_ro desc, du_an_id"

    du_an_id = fields.Many2one('du_an', string="Dự án", required=True, ondelete='cascade', tracking=True)
    ten_rui_ro = fields.Char(string="Tên rủi ro", required=True, tracking=True)
    mo_ta = fields.Text(string="Mô tả rủi ro")
    
    # Đánh giá rủi ro
    kha_nang_xay_ra = fields.Selection([
        ('thap', 'Thấp (< 25%)'),
        ('trung_binh', 'Trung bình (25-50%)'),
        ('cao', 'Cao (50-75%)'),
        ('rat_cao', 'Rất cao (> 75%)'),
    ], string="Khả năng xảy ra", required=True, tracking=True)
    
    muc_anh_huong = fields.Selection([
        ('toi_thieu', 'Tối thiểu'),
        ('nhe', 'Nhẹ'),
        ('trung_binh', 'Trung bình'),
        ('nang', 'Nặng'),
        ('rat_nang', 'Rất nặng'),
    ], string="Mức ảnh hưởng", required=True, tracking=True)
    
    diem_rui_ro = fields.Float(string="Điểm rủi ro", compute="_compute_diem_rui_ro", store=True, help="Tính tự động từ khả năng × ảnh hưởng")
    
    # Phương án xử lý
    phuong_an = fields.Text(string="Phương án xử lý/Giảm thiểu")
    nguoi_phu_trach_id = fields.Many2one('nhan_vien', string="Người phụ trách", tracking=True)
    ngay_deadline = fields.Date(string="Deadline xử lý", tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('identified', 'Xác định'),
        ('monitoring', 'Đang theo dõi'),
        ('active', 'Rủi ro xảy ra'),
        ('resolved', 'Đã giải quyết'),
    ], string="Trạng thái", default='identified', tracking=True)
    
    # Nếu xảy ra
    issue_id = fields.Many2one('du_an_issue', string="Issue liên quan", ondelete='set null')
    
    ghi_chu = fields.Text(string="Ghi chú")
    
    @api.depends('kha_nang_xay_ra', 'muc_anh_huong')
    def _compute_diem_rui_ro(self):
        """Tính điểm rủi ro"""
        kha_nang_map = {'thap': 1, 'trung_binh': 2, 'cao': 3, 'rat_cao': 4}
        anh_huong_map = {'toi_thieu': 1, 'nhe': 2, 'trung_binh': 3, 'nang': 4, 'rat_nang': 5}
        
        for record in self:
            kha_nang_val = kha_nang_map.get(record.kha_nang_xay_ra, 0)
            anh_huong_val = anh_huong_map.get(record.muc_anh_huong, 0)
            record.diem_rui_ro = kha_nang_val * anh_huong_val
    
    def action_monitoring(self):
        """Bắt đầu theo dõi rủi ro"""
        for record in self:
            if record.trang_thai != 'identified':
                raise ValidationError(_("Chỉ rủi ro ở trạng thái Xác định mới chuyển sang Đang theo dõi!"))
        self.trang_thai = 'monitoring'
    
    def action_active(self):
        """Xác nhận rủi ro đã xảy ra"""
        for record in self:
            if record.trang_thai != 'monitoring':
                raise ValidationError(_("Chỉ rủi ro Đang theo dõi mới có thể kích hoạt!"))
            record.trang_thai = 'active'
            # Có thể auto-create issue
            if not record.issue_id:
                issue = self.env['du_an_issue'].create({
                    'du_an_id': record.du_an_id.id,
                    'tieu_de': f"[RỦI RO] {record.ten_rui_ro}",
                    'mo_ta': record.mo_ta,
                    'rui_ro_id': record.id,
                    'do_uu_tien': 'cao',
                    'trang_thai': 'open',
                })
                record.issue_id = issue.id
    
    def action_resolve(self):
        """Giải quyết rủi ro"""
        for record in self:
            if record.trang_thai != 'active':
                raise ValidationError(_("Chỉ rủi ro đã kích hoạt mới có thể đánh dấu giải quyết!"))
        self.trang_thai = 'resolved'
