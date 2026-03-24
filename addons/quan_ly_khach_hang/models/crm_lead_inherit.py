# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    lead_noi_bo_id = fields.Many2one(
        'lead',
        string='Lead noi bo',
        compute='_compute_lead_noi_bo_id',
        compute_sudo=True,
    )
    lead_noi_bo_count = fields.Integer(
        string='So lead noi bo',
        compute='_compute_lead_noi_bo_id',
        compute_sudo=True,
    )
    lead_noi_bo_diem = fields.Float(
        string='Diem lead noi bo',
        compute='_compute_lead_noi_bo_id',
        compute_sudo=True,
    )
    lead_noi_bo_trang_thai = fields.Selection(
        [
            ('moi', 'Moi'),
            ('dang_tiep_can', 'Dang tiep can'),
            ('quan_tam', 'Quan tam'),
            ('chua_san_sang', 'Chua san sang'),
            ('san_sang', 'San sang'),
            ('chuyen_khach', 'Chuyen khach'),
            ('vo_kien_cu', 'Vo kien cu'),
        ],
        string='Trang thai lead noi bo',
        compute='_compute_lead_noi_bo_id',
        compute_sudo=True,
    )
    cong_viec_cham_soc_count = fields.Integer(
        string='So cong viec cham soc',
        compute='_compute_cong_viec_cham_soc',
        compute_sudo=True,
    )
    has_cong_viec_cham_soc = fields.Boolean(
        string='Co cong viec cham soc',
        compute='_compute_cong_viec_cham_soc',
        search='_search_has_cong_viec_cham_soc',
        compute_sudo=True,
    )

    @api.depends('email_from', 'phone', 'mobile', 'partner_name', 'contact_name')
    def _compute_lead_noi_bo_id(self):
        LeadNoiBo = self.env['lead']
        for record in self:
            domain = []
            if record.email_from:
                domain = [('email', '=', record.email_from)]
            elif record.phone:
                domain = [('so_dien_thoai', '=', record.phone)]
            elif record.mobile:
                domain = [('so_dien_thoai', '=', record.mobile)]
            elif record.partner_name:
                domain = [('ten_lead', 'ilike', record.partner_name)]
            elif record.contact_name:
                domain = [('nguoi_lien_he', 'ilike', record.contact_name)]

            linked = LeadNoiBo.search(domain, limit=1) if domain else False
            record.lead_noi_bo_id = linked
            record.lead_noi_bo_count = 1 if linked else 0
            record.lead_noi_bo_diem = linked.diem_danh_gia if linked else 0.0
            record.lead_noi_bo_trang_thai = linked.trang_thai if linked else False

    @api.depends('partner_id')
    def _compute_cong_viec_cham_soc(self):
        CongViec = self.env['cong_viec']
        for record in self:
            if record.partner_id:
                task_count = CongViec.search_count([('partner_id', '=', record.partner_id.id)])
            else:
                task_count = 0
            record.cong_viec_cham_soc_count = task_count
            record.has_cong_viec_cham_soc = bool(task_count)

    def _search_has_cong_viec_cham_soc(self, operator, value):
        partner_ids = self.env['cong_viec'].sudo().search([('partner_id', '!=', False)]).mapped('partner_id').ids
        if operator in ('=', '==') and bool(value):
            return [('partner_id', 'in', partner_ids)]
        if operator in ('=', '==') and not bool(value):
            return ['|', ('partner_id', '=', False), ('partner_id', 'not in', partner_ids)]
        if operator == '!=' and bool(value):
            return ['|', ('partner_id', '=', False), ('partner_id', 'not in', partner_ids)]
        return [('partner_id', 'in', partner_ids)]

    def action_open_cong_viec_cham_soc(self):
        self.ensure_one()
        return {
            'name': 'Cong viec cham soc',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'kanban,tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
        }

    def action_open_lead_noi_bo(self):
        self.ensure_one()
        action = self.env.ref('quan_ly_khach_hang.lead_action').sudo().read()[0]
        if self.lead_noi_bo_id:
            action.update({
                'view_mode': 'form',
                'res_id': self.lead_noi_bo_id.id,
            })
        else:
            domain = []
            if self.email_from:
                domain = [('email', '=', self.email_from)]
            action.update({
                'domain': domain,
                'context': {
                    'default_ten_lead': self.partner_name or self.contact_name or self.name,
                    'default_email': self.email_from,
                    'default_so_dien_thoai': self.phone or self.mobile,
                },
            })
        return action
