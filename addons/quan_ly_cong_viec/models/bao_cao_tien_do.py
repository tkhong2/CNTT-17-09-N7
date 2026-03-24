# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BaoCaoTienDo(models.Model):
    _name = "bao_cao_tien_do"
    _description = "Báo cáo tiến độ công việc"
    _rec_name = "cong_viec_id"
    _order = "ngay_bao_cao desc"
    
    cong_viec_id = fields.Many2one('cong_viec', string="Công việc", required=True, ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Người báo cáo", required=True)
    
    ngay_bao_cao = fields.Date(string="Ngày báo cáo", required=True, default=fields.Date.today)
    noi_dung = fields.Text(string="Nội dung báo cáo", required=True)
    tien_do = fields.Float(string="Tiến độ (%)", required=True, 
                         help="Đánh giá phần trăm hoàn thành của công việc")
    so_gio = fields.Float(string="Số giờ làm việc", required=True)
    
    # Trạng thái báo cáo (liên kết đến người tham gia)
    trang_thai = fields.Selection([
        ('chua_bao_cao', '⭕ Chưa báo cáo'),
        ('dang_xu_ly', '🟡 Đang xử lý'),
        ('da_bao_cao', '✅ Đã báo cáo'),
    ], string="Trạng thái báo cáo", default='chua_bao_cao', help="Trạng thái sẽ được cập nhật khi lưu file đính kèm")
    
    # Vấn đề phát sinh
    van_de_phat_sinh = fields.Text(string="Vấn đề phát sinh")
    giai_phap = fields.Text(string="Giải pháp đề xuất")
    
    # Đính kèm
    file_dinh_kem = fields.Binary(string="File đính kèm")
    ten_file = fields.Char(string="Tên file")
    
    # Thông tin từ công việc
    du_an_id = fields.Many2one(related='cong_viec_id.du_an_id', string="Dự án", store=True, readonly=True)
    ten_cong_viec = fields.Char(related='cong_viec_id.ten_cong_viec', string="Tên công việc", store=True, readonly=True)
    
    @api.onchange('cong_viec_id')
    def _onchange_cong_viec_id(self):
        """Giới hạn nhân viên chỉ từ người tham gia của công việc"""
        if self.cong_viec_id:
            return {'domain': {'nhan_vien_id': [('id', 'in', self.cong_viec_id.nguoi_tham_gia_ids.mapped('nhan_vien_id').ids)]}}
    
    @api.constrains('tien_do')
    def _check_tien_do(self):
        for record in self:
            if record.tien_do < 0 or record.tien_do > 100:
                raise ValidationError(_("Tiến độ phải nằm trong khoảng từ 0 đến 100!"))
    
    @api.model
    def create(self, vals):
        # Khi tạo báo cáo tiến độ, cập nhật trạng thái công việc nếu tiến độ = 100%
        result = super(BaoCaoTienDo, self).create(vals)
        
        # Cập nhật trạng thái người tham gia thành "Đã báo cáo" chỉ khi có file đính kèm
        if result.file_dinh_kem:
            nguoi_tham_gia = self.env['nguoi_tham_gia'].search([
                ('cong_viec_id', '=', result.cong_viec_id.id),
                ('nhan_vien_id', '=', result.nhan_vien_id.id),
            ])
            if nguoi_tham_gia:
                nguoi_tham_gia.write({'trang_thai': 'da_bao_cao'})
        
        # Cập nhật trạng thái công việc nếu tiến độ = 100%
        if result.tien_do == 100:
            result.cong_viec_id.write({'trang_thai': 'hoan_thanh'})
        elif result.tien_do > 0 and result.cong_viec_id.trang_thai == 'moi':
            result.cong_viec_id.write({'trang_thai': 'dang_thuc_hien'})
        return result
