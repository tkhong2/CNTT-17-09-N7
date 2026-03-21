# -*- coding: utf-8 -*-
from odoo import models, fields, api


class GoiDien(models.Model):
    _name = 'goi_dien'
    _description = 'Gọi điện khách hàng'
    _inherits = {'khach_hang_tuong_tac': 'tuong_tac_id'}
    _order = 'ngay_lien_he desc'

    tuong_tac_id = fields.Many2one(
        'khach_hang_tuong_tac', required=True, ondelete='cascade'
    )
    thoi_luong_phut = fields.Integer(string='Thời lượng gọi (phút)')
    trang_thai_goi = fields.Selection([
        ('khong_nghe', 'Không nghe máy'),
        ('hen_goi_lai', 'Hẹn gọi lại'),
        ('da_goi', 'Đã gọi'),
    ], string='Kết quả cuộc gọi')
    cong_viec_id = fields.Many2one(
        'cong_viec', string='Công việc phát sinh',
        readonly=True, ondelete='set null'
    )

    def _tao_cong_viec(self):
        for rec in self:
            if rec.cong_viec_id:
                continue
            tien_do_map = {
                'khong_nghe': (30, 'Gọi điện nhưng khách không nghe máy'),
                'hen_goi_lai': (50, 'Khách hàng hẹn gọi lại'),
                'da_goi': (100, 'Hoàn thành gọi điện khách hàng'),
            }
            tien_do, noi_dung = tien_do_map.get(rec.trang_thai_goi, (0, 'Khởi tạo gọi điện'))
            ma_cv = self.env['ir.sequence'].next_by_code('cong_viec.sequence') or f'GD%s' % fields.Datetime.now().strftime('%d%m%H%M%S')
            cv = self.env['cong_viec'].create({
                'ma_cong_viec': ma_cv,
                'ten_cong_viec': f'Gọi điện KH {rec.khach_hang_id.ten_khach_hang}',
                'mo_ta': noi_dung,
                'ngay_bat_dau': rec.ngay_lien_he.date() if rec.ngay_lien_he else fields.Date.today(),
                'khach_hang_id': rec.khach_hang_id.id,
                'nguon_phat_sinh': 'goi_dien',
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
        if 'trang_thai_goi' in vals:
            tien_do_map = {
                'khong_nghe': (30, 'Gọi điện nhưng khách không nghe máy'),
                'hen_goi_lai': (50, 'Khách hàng hẹn gọi lại'),
                'da_goi': (100, 'Hoàn thành gọi điện khách hàng'),
            }
            for rec in self:
                tien_do, noi_dung = tien_do_map.get(rec.trang_thai_goi, (0, ''))
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
