# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LichHen(models.Model):
    _name = 'lich_hen'
    _description = 'Lịch hẹn khách hàng'
    _inherits = {'khach_hang_tuong_tac': 'tuong_tac_id'}
    _order = 'ngay_lien_he desc'

    tuong_tac_id = fields.Many2one(
        'khach_hang_tuong_tac', required=True, ondelete='cascade'
    )
    dia_diem = fields.Char(string='Địa điểm')
    trang_thai_hen = fields.Selection([
        ('sap_dien_ra', 'Sắp diễn ra'),
        ('da_hoan_thanh', 'Đã hoàn thành'),
        ('huy', 'Hủy'),
    ], string='Trạng thái lịch hẹn', default='sap_dien_ra')
    cong_viec_id = fields.Many2one(
        'cong_viec', string='Công việc phát sinh',
        readonly=True, ondelete='set null'
    )

    def _tao_cong_viec(self):
        tien_do_map = {
            'sap_dien_ra': (20, 'Lịch hẹn sắp diễn ra'),
            'da_hoan_thanh': (100, 'Hoàn thành lịch hẹn'),
            'huy': (0, 'Khách hàng hủy lịch hẹn'),
        }
        for rec in self:
            if rec.cong_viec_id:
                continue
            tien_do, noi_dung = tien_do_map.get(rec.trang_thai_hen, (0, ''))
            ma_cv = self.env['ir.sequence'].next_by_code('cong_viec.sequence') or f'LH%s' % fields.Datetime.now().strftime('%d%m%H%M%S')
            cv = self.env['cong_viec'].create({
                'ma_cong_viec': ma_cv,
                'ten_cong_viec': f'Lịch hẹn KH {rec.khach_hang_id.ten_khach_hang}',
                'mo_ta': f'Hẹn gặp tại {rec.dia_diem or "chưa xác định"}',
                'ngay_bat_dau': rec.ngay_lien_he.date() if rec.ngay_lien_he else fields.Date.today(),
                'khach_hang_id': rec.khach_hang_id.id,
                'nguon_phat_sinh': 'lich_hen',
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
