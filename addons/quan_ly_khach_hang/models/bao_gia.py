# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BaoGia(models.Model):
    _name = 'bao_gia'
    _description = 'Báo giá khách hàng'
    _inherits = {'khach_hang_tuong_tac': 'tuong_tac_id'}
    _order = 'ngay_lien_he desc'

    tuong_tac_id = fields.Many2one(
        'khach_hang_tuong_tac', required=True, ondelete='cascade'
    )
    tong_tien = fields.Float(string='Tổng tiền (VNĐ)', digits=(16, 0))
    trang_thai_bao_gia = fields.Selection([
        ('da_gui', 'Đã gửi'),
        ('dong_y', 'Đồng ý'),
        ('tu_choi', 'Từ chối'),
    ], string='Trạng thái báo giá')
    cong_viec_id = fields.Many2one(
        'cong_viec', string='Công việc phát sinh',
        readonly=True, ondelete='set null'
    )

    def _tao_cong_viec(self):
        tien_do_map = {
            'da_gui': (50, 'Đã gửi báo giá cho khách hàng'),
            'dong_y': (100, 'Khách hàng đồng ý báo giá'),
            'tu_choi': (0, 'Khách hàng từ chối báo giá'),
        }
        for rec in self:
            if rec.cong_viec_id:
                continue
            tien_do, noi_dung = tien_do_map.get(rec.trang_thai_bao_gia, (0, 'Khởi tạo báo giá'))
            ma_cv = self.env['ir.sequence'].next_by_code('cong_viec.sequence') or f'BG%s' % fields.Datetime.now().strftime('%d%m%H%M%S')
            cv = self.env['cong_viec'].create({
                'ma_cong_viec': ma_cv,
                'ten_cong_viec': f'Báo giá KH {rec.khach_hang_id.ten_khach_hang}',
                'mo_ta': 'Tạo từ tương tác báo giá',
                'ngay_bat_dau': rec.ngay_lien_he.date() if rec.ngay_lien_he else fields.Date.today(),
                'khach_hang_id': rec.khach_hang_id.id,
                'nguon_phat_sinh': 'bao_gia',
            })
            rec.cong_viec_id = cv.id
            if rec.nhan_vien_id:
                self.env['bao_cao_tien_do'].create({
                    'cong_viec_id': cv.id,
                    'nhan_vien_id': rec.nhan_vien_id.id,
                    'tien_do': tien_do,
                    'noi_dung': noi_dung,
                    'ngay_bao_cao': fields.Date.today(),
                    'so_gio': 0.0,
                })

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._tao_cong_viec()
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'trang_thai_bao_gia' in vals:
            tien_do_map = {
                'da_gui': (50, 'Đã gửi báo giá cho khách hàng'),
                'dong_y': (100, 'Khách hàng đồng ý báo giá'),
                'tu_choi': (0, 'Khách hàng từ chối báo giá'),
            }
            for rec in self:
                tien_do, noi_dung = tien_do_map.get(rec.trang_thai_bao_gia, (0, ''))
                if rec.cong_viec_id and rec.nhan_vien_id and noi_dung:
                    self.env['bao_cao_tien_do'].create({
                        'cong_viec_id': rec.cong_viec_id.id,
                        'nhan_vien_id': rec.nhan_vien_id.id,
                        'tien_do': tien_do,
                        'noi_dung': noi_dung,
                        'ngay_bao_cao': fields.Date.today(),
                        'so_gio': 0.0,
                    })
        return res

    def unlink(self):
        for rec in self:
            if rec.cong_viec_id:
                rec.cong_viec_id.unlink()
        return super().unlink()
