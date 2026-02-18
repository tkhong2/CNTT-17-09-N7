# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class KhachHangTuongTac(models.Model):
    _name = 'khach_hang_tuong_tac'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Tương tác khách hàng'
    _order = 'ngay_lien_he desc, id desc'

    khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng', required=True, ondelete='cascade', tracking=True)
    tieu_de = fields.Char(string='Tiêu đề', required=True, tracking=True)
    loai_tuong_tac = fields.Selection([
        ('call', 'Gọi điện'),
        ('email', 'Email'),
        ('meeting', 'Họp trực tiếp'),
        ('zalo', 'Zalo/Chat'),
        ('other', 'Khác'),
    ], string='Loại tương tác', default='call', required=True, tracking=True)

    ngay_lien_he = fields.Datetime(string='Thời điểm tương tác', default=fields.Datetime.now, required=True, tracking=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên thực hiện', tracking=True)
    noi_dung = fields.Text(string='Nội dung trao đổi')

    ket_qua = fields.Selection([
        ('quan_tam', 'Khách quan tâm'),
        ('hen_lai', 'Hẹn liên hệ lại'),
        ('chot_hop_dong', 'Chốt hợp đồng'),
        ('khong_tiem_nang', 'Không tiềm năng'),
    ], string='Kết quả', tracking=True)

    hen_lien_he_tiep = fields.Datetime(string='Hẹn liên hệ tiếp', index=True)
    trang_thai = fields.Selection([
        ('planned', 'Đang theo dõi'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Hủy'),
    ], string='Trạng thái', default='planned', required=True, tracking=True, index=True)

    qua_han = fields.Boolean(string='Quá hạn follow-up', compute='_compute_qua_han', store=False)

    @api.depends('trang_thai', 'hen_lien_he_tiep')
    def _compute_qua_han(self):
        now = fields.Datetime.now()
        for record in self:
            record.qua_han = bool(record.trang_thai == 'planned' and record.hen_lien_he_tiep and record.hen_lien_he_tiep < now)

    @api.constrains('ngay_lien_he', 'hen_lien_he_tiep', 'ket_qua')
    def _check_timeline_and_followup(self):
        for record in self:
            if record.hen_lien_he_tiep and record.ngay_lien_he and record.hen_lien_he_tiep < record.ngay_lien_he:
                raise ValidationError(_('Hẹn liên hệ tiếp phải lớn hơn hoặc bằng thời điểm tương tác.'))
            if record.ket_qua == 'hen_lai' and not record.hen_lien_he_tiep:
                raise ValidationError(_('Khi kết quả là "Hẹn liên hệ lại", bạn cần nhập "Hẹn liên hệ tiếp".'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('khach_hang_id') and not vals.get('nhan_vien_id'):
                kh = self.env['khach_hang'].browse(vals['khach_hang_id'])
                if kh.nhan_vien_phu_trach_id:
                    vals['nhan_vien_id'] = kh.nhan_vien_phu_trach_id.id
        records = super().create(vals_list)
        records._sync_khach_hang_status()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_khach_hang_status()
        return res

    def _sync_khach_hang_status(self):
        for record in self.filtered('khach_hang_id'):
            if record.ket_qua == 'chot_hop_dong':
                record.khach_hang_id.trang_thai_hop_tac = 'dang_hop_tac'
            elif record.ket_qua == 'khong_tiem_nang':
                record.khach_hang_id.trang_thai_hop_tac = 'ngung_hop_tac'
            elif record.ket_qua in ['quan_tam', 'hen_lai'] and record.khach_hang_id.trang_thai_hop_tac == 'tiem_nang':
                record.khach_hang_id.trang_thai_hop_tac = 'dang_hop_tac'

    def action_mark_done(self):
        self.write({'trang_thai': 'done'})

    def action_mark_cancel(self):
        self.write({'trang_thai': 'cancel'})

    def action_bulk_mark_done(self):
        planned_records = self.filtered(lambda rec: rec.trang_thai == 'planned')
        if planned_records:
            planned_records.write({'trang_thai': 'done'})

    def action_bulk_postpone_2_days(self):
        now = fields.Datetime.now()
        target_time = now + timedelta(days=2)
        for record in self.filtered(lambda rec: rec.trang_thai == 'planned'):
            if not record.hen_lien_he_tiep or record.hen_lien_he_tiep < now:
                record.hen_lien_he_tiep = target_time

    @api.model
    def _cron_create_overdue_followup_activities(self):
        overdue_records = self.search([
            ('trang_thai', '=', 'planned'),
            ('hen_lien_he_tiep', '!=', False),
            ('hen_lien_he_tiep', '<', fields.Datetime.now()),
        ])
        if not overdue_records:
            return

        model_id = self.env['ir.model']._get_id('khach_hang_tuong_tac')
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        activity_type_id = activity_type.id if activity_type else False
        activity_model = self.env['mail.activity'].sudo()
        today = fields.Date.context_today(self)

        for record in overdue_records:
            user = record.nhan_vien_id.user_id or record.khach_hang_id.nhan_vien_phu_trach_id.user_id
            if not user:
                continue

            existing = activity_model.search_count([
                ('res_model_id', '=', model_id),
                ('res_id', '=', record.id),
                ('user_id', '=', user.id),
                ('activity_type_id', '=', activity_type_id),
            ])
            if existing:
                continue

            activity_model.create({
                'res_id': record.id,
                'res_model_id': model_id,
                'user_id': user.id,
                'activity_type_id': activity_type_id,
                'date_deadline': today,
                'summary': _('Follow-up quá hạn: %s') % record.tieu_de,
                'note': _('Khách hàng: %s\nĐến hẹn: %s') % (
                    record.khach_hang_id.ten_khach_hang,
                    fields.Datetime.to_string(record.hen_lien_he_tiep),
                ),
            })

    @api.model
    def _cron_escalate_critical_overdue_followups(self):
        escalation_threshold = fields.Datetime.now() - timedelta(days=2)
        critical_records = self.search([
            ('trang_thai', '=', 'planned'),
            ('hen_lien_he_tiep', '!=', False),
            ('hen_lien_he_tiep', '<', escalation_threshold),
        ])
        if not critical_records:
            return 0

        manager_group = self.env.ref('quan_ly_khach_hang.group_khach_hang_manager', raise_if_not_found=False)
        managers = manager_group.users.filtered(lambda user: user.active) if manager_group else self.env['res.users']
        if not managers:
            return 0

        model_id = self.env['ir.model']._get_id('khach_hang_tuong_tac')
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        activity_type_id = activity_type.id if activity_type else False
        activity_model = self.env['mail.activity'].sudo()
        today = fields.Date.context_today(self)

        created_count = 0
        for record in critical_records:
            for manager in managers:
                exists = activity_model.search_count([
                    ('res_model_id', '=', model_id),
                    ('res_id', '=', record.id),
                    ('user_id', '=', manager.id),
                    ('activity_type_id', '=', activity_type_id),
                    ('summary', 'ilike', 'Escalation follow-up quá hạn'),
                ])
                if exists:
                    continue

                activity_model.create({
                    'res_id': record.id,
                    'res_model_id': model_id,
                    'user_id': manager.id,
                    'activity_type_id': activity_type_id,
                    'date_deadline': today,
                    'summary': _('Escalation follow-up quá hạn: %s') % record.tieu_de,
                    'note': _('Khách hàng: %s\nQuá hạn từ: %s\nNgười phụ trách hiện tại: %s') % (
                        record.khach_hang_id.ten_khach_hang,
                        fields.Datetime.to_string(record.hen_lien_he_tiep),
                        record.nhan_vien_id.display_name or _('Chưa có'),
                    ),
                })
                created_count += 1

        return created_count
