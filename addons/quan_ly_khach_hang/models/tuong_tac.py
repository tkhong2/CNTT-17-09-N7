# -*- coding: utf-8 -*-
from odoo import models, fields, api


class KhachHangTuongTac(models.Model):
    _name = 'khach_hang_tuong_tac'
    _description = 'Tương tác khách hàng'
    _order = 'ngay_lien_he desc'

    khach_hang_id = fields.Many2one(
        'khach_hang', string='Khách hàng', required=True, ondelete='cascade'
    )
    nhan_vien_id = fields.Many2one(
        'nhan_vien', string='Nhân viên phụ trách'
    )
    tieu_de = fields.Char(string='Tiêu đề', required=True)
    loai_tuong_tac = fields.Selection([
        ('goi_dien', 'Gọi điện'),
        ('gap_mat', 'Gặp mặt'),
        ('email', 'Email'),
        ('khac', 'Khác'),
    ], string='Loại tương tác', default='goi_dien')
    ngay_lien_he = fields.Datetime(
        string='Ngày liên hệ', default=fields.Datetime.now, required=True
    )
    ket_qua = fields.Selection([
        ('chot_hop_dong', 'Chốt hợp đồng'),
        ('hen_gap_lai', 'Hẹn gặp lại'),
        ('can_theo_doi', 'Cần theo dõi'),
        ('khong_quan_tam', 'Không quan tâm'),
    ], string='Kết quả')
    hen_lien_he_tiep = fields.Date(string='Hẹn liên hệ tiếp')
    noi_dung = fields.Text(string='Nội dung')
    trang_thai = fields.Selection([
        ('planned', 'Đang theo dõi'),
        ('done', 'Đã hoàn thành'),
        ('cancel', 'Đã hủy'),
    ], string='Trạng thái', default='planned')
    qua_han = fields.Boolean(
        string='Quá hạn', compute='_compute_qua_han', store=True
    )

    @api.depends('trang_thai', 'hen_lien_he_tiep')
    def _compute_qua_han(self):
        today = fields.Date.today()
        for rec in self:
            rec.qua_han = (
                rec.trang_thai == 'planned'
                and bool(rec.hen_lien_he_tiep)
                and rec.hen_lien_he_tiep < today
            )

    def action_mark_done(self):
        self.write({'trang_thai': 'done'})

    def action_mark_cancel(self):
        self.write({'trang_thai': 'cancel'})

    def action_bulk_mark_done(self):
        self.filtered(lambda r: r.trang_thai == 'planned').write({'trang_thai': 'done'})

    def action_bulk_postpone_2_days(self):
        from datetime import timedelta
        today = fields.Date.today()
        for rec in self.filtered(lambda r: r.trang_thai == 'planned'):
            base = rec.hen_lien_he_tiep or today
            rec.hen_lien_he_tiep = base + timedelta(days=2)
