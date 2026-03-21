# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CongViecExtend(models.Model):
    _inherit = 'cong_viec'

    khach_hang_id = fields.Many2one(
        'khach_hang', string='Khách hàng', ondelete='set null', index=True
    )
    contact_person_id = fields.Many2one(
        'khach_hang',
        string='Người liên hệ',
        domain="[('parent_khach_hang_id', '=', khach_hang_id)] if khach_hang_id else [('id', '=', -1)]",
        ondelete='set null'
    )
    nguon_phat_sinh = fields.Selection([
        ('goi_dien', 'Từ gọi điện'),
        ('lich_hen', 'Từ lịch hẹn'),
        ('bao_gia', 'Từ báo giá'),
        ('thu_cong', 'Thủ công'),
    ], string='Nguồn phát sinh', default='thu_cong')

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang_id(self):
        """
        Giai đoạn 1 - Bước 3: Logic tự động hóa nhập liệu
        Khi chọn khách hàng, tự động điền thông tin liên hệ vào mô tả
        và cập nhật độ ưu tiên nếu khách hàng VIP (Giai đoạn 2 - Gợi ý 1)
        """
        if self.khach_hang_id:
            kh = self.khach_hang_id
            # Điền thông tin khách hàng vào mô tả nếu chưa có
            contact_info_lines = []
            contact_info_lines.append(f"Khách hàng: {kh.ten_khach_hang}")
            if kh.dien_thoai:
                contact_info_lines.append(f"Điện thoại: {kh.dien_thoai}")
            if kh.email:
                contact_info_lines.append(f"Email: {kh.email}")
            if kh.nguoi_lien_he:
                contact_info_lines.append(f"Người liên hệ: {kh.nguoi_lien_he}")
            
            if contact_info_lines and not self.mo_ta:
                self.mo_ta = "\n".join(contact_info_lines)
            
            # Giai đoạn 2 - Gợi ý 1: Phân hạng khách hàng tự động
            # Nếu khách hàng VIP (Vàng), tự động set độ ưu tiên cao
            if kh.rank == 'vang':
                self.do_uu_tien = 'rat_cao'
            elif kh.rank == 'bac':
                self.do_uu_tien = 'cao'
            else:
                self.do_uu_tien = 'trung_binh'
