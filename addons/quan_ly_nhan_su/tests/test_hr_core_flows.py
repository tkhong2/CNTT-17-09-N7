# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'custom_hr_core_flows')
class TestHrCoreFlows(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['nhan_vien'].create({
            'ma_nhan_vien': 'UT-HR-001',
            'ho_va_ten': 'UT Employee HR',
            'ngay_sinh': fields.Date.from_string('1995-01-01'),
            'trang_thai': 'active',
        })
        cls.env['hop_dong'].create({
            'ma_hop_dong': 'UT-HD-001',
            'ten_hop_dong': 'UT Contract',
            'nhan_vien_id': cls.employee.id,
            'loai_hop_dong': 'xac_dinh_thoi_han',
            'ngay_bat_dau': fields.Date.today() - timedelta(days=30),
            'ngay_ket_thuc': fields.Date.today() + timedelta(days=365),
            'luong_co_ban': 22000000,
            'phu_cap': 2000000,
            'trang_thai': 'active',
        })

    def _weekday_count(self, start_date, end_date):
        total = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:
                total += 1
            current_date += timedelta(days=1)
        return total

    def test_leave_sync_to_attendance(self):
        start_date = fields.Date.today() + timedelta(days=2)
        end_date = start_date + timedelta(days=2)

        leave = self.env['nghi_phep'].create({
            'ma_nghi_phep': 'UT-NP-001',
            'nhan_vien_id': self.employee.id,
            'loai_nghi_phep': 'phep_nam',
            'ngay_bat_dau': start_date,
            'ngay_ket_thuc': end_date,
            'ly_do': 'Unit test leave sync',
        })

        leave._sync_to_attendance()

        attendances = self.env['cham_cong'].search([
            ('nhan_vien_id', '=', self.employee.id),
            ('ngay_cham_cong', '>=', start_date),
            ('ngay_cham_cong', '<=', end_date),
        ])

        self.assertEqual(len(attendances), self._weekday_count(start_date, end_date))
        self.assertTrue(all(item.trang_thai == 'nghi_phep' for item in attendances))

    def test_payroll_calculate_from_attendance(self):
        first_day = fields.Date.today().replace(day=1)
        payroll = self.env['tinh_luong'].create({
            'ma_bang_luong': 'UT-BL-001',
            'thang_nam': first_day.strftime('%Y-%m'),
        })

        line = self.env['tinh_luong_chi_tiet'].create({
            'tinh_luong_id': payroll.id,
            'nhan_vien_id': self.employee.id,
            'luong_co_ban': 22000000,
            'phu_cap': 2000000,
        })

        for offset in range(10):
            self.env['cham_cong'].create({
                'nhan_vien_id': self.employee.id,
                'ngay_cham_cong': first_day + timedelta(days=offset),
                'trang_thai': 'di_lam',
            })

        for offset in range(10, 12):
            self.env['cham_cong'].create({
                'nhan_vien_id': self.employee.id,
                'ngay_cham_cong': first_day + timedelta(days=offset),
                'trang_thai': 'nghi_khong_luong',
            })

        line._calculate_salary()

        self.assertEqual(line.so_ngay_lam_viec, 10)
        self.assertEqual(line.so_ngay_vang_khong_luong, 2)
        self.assertAlmostEqual(line.luong_co_ban, 10000000.0, places=2)
        self.assertGreaterEqual(line.thue_thu_nhap, 0.0)
