# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    rank = fields.Selection(
        [('dong', 'Dong'), ('bac', 'Bac'), ('vang', 'Vang')],
        string='Phan hang khach hang',
        default='dong',
    )

    cong_viec_cham_soc_count = fields.Integer(
        string='Cong viec cham soc',
        compute='_compute_cong_viec_cham_soc_count',
        compute_sudo=True,
    )

    @api.depends('email', 'phone')
    def _compute_cong_viec_cham_soc_count(self):
        CongViec = self.env['cong_viec']
        for partner in self:
            partner.cong_viec_cham_soc_count = CongViec.search_count([
                ('partner_id', '=', partner.id),
            ])

    def action_xem_cong_viec_cham_soc(self):
        self.ensure_one()
        return {
            'name': 'Cong viec cham soc',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'kanban,tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
            },
        }
