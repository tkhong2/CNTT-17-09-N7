# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartnerInherit(models.Model):
    """
    Kế thừa res.partner — KHÔNG sửa file gốc Odoo.
    Thêm: phân hạng khách hàng (rank) và smart button Công việc.
    """
    _inherit = 'res.partner'

    # ── Phân hạng KH (Mức 1 Nâng cao - Gợi ý 1) ─────────────
    rank = fields.Selection([
        ('dong', 'Đồng'),
        ('bac',  'Bạc'),
        ('vang', 'Vàng'),
    ], string='Phân hạng khách hàng', default='dong',
       tracking=True,
       help='Đồng: KH thường | Bạc: KH trung | Vàng: KH VIP → Task tự động ưu tiên Cao')

    # ── Smart button: Công việc chăm sóc ─────────────────────
    cong_viec_cham_soc_count = fields.Integer(
        string='Công việc chăm sóc',
        compute='_compute_cong_viec_cham_soc_count',
        compute_sudo=True,
    )

    def _compute_cong_viec_cham_soc_count(self):
        CongViec = self.env['cong_viec']
        for partner in self:
            partner.cong_viec_cham_soc_count = CongViec.search_count([
                ('partner_id', '=', partner.id),
            ])

    def action_xem_cong_viec_cham_soc(self):
        self.ensure_one()
        return {
            'name': 'Công việc chăm sóc KH',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'kanban,tree,form',
            'domain':  [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
