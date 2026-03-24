# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'custom_crm_sla')
class TestCrmSla(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['khach_hang'].create({
            'ten_khach_hang': 'UT Customer SLA',
        })

    def test_sla_overdue_and_dashboard_rate(self):
        ticket = self.env['yeu_cau_ho_tro'].create({
            'ma_yeu_cau': 'UT-HT-001',
            'khach_hang_id': self.customer.id,
            'loai_yeu_cau': 'ho_tro_ky_thuat',
            'tieu_de': 'UT SLA overdue',
            'mo_ta_chi_tiet': '<p>Unit test</p>',
            'trang_thai': 'in_progress',
            'sla_gio': 1,
            'ngay_tao_datetime': fields.Datetime.now() - timedelta(hours=2),
        })

        ticket._compute_sla()
        self.assertTrue(ticket.qua_han_sla)

        dashboard = self.env['khach_hang_dashboard'].search([], limit=1)
        if not dashboard:
            dashboard = self.env['khach_hang_dashboard'].create({'ten_bang': 'UT KPI'})
        dashboard._compute_kpis()

        self.assertGreaterEqual(dashboard.ticket_qua_han_sla, 1)
        self.assertGreater(dashboard.sla_breach_rate, 0.0)

        ticket.write({'trang_thai': 'resolved'})
        ticket._compute_sla()
        self.assertFalse(ticket.qua_han_sla)
