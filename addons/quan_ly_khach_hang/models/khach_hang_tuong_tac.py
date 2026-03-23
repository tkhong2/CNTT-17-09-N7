# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class KhachHangTuongTac(models.Model):
    _name = 'khach_hang_tuong_tac'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Tương tác khách hàng'
    _order = 'ngay_lien_he desc, id desc'

    khach_hang_id  = fields.Many2one('khach_hang', string='Khách hàng', required=True, ondelete='cascade', tracking=True)
    tieu_de        = fields.Char(string='Tiêu đề', required=True, tracking=True)
    loai_tuong_tac = fields.Selection([
        ('call',    'Gọi điện'),
        ('email',   'Email'),
        ('meeting', 'Họp trực tiếp'),
        ('zalo',    'Zalo/Chat'),
        ('bao_gia', 'Gửi báo giá'),
        ('lich_hen','Lịch hẹn'),
        ('other',   'Khác'),
    ], string='Loại tương tác', default='call', required=True, tracking=True)

    ngay_lien_he  = fields.Datetime(string='Thời điểm tương tác', default=fields.Datetime.now, required=True, tracking=True)
    nhan_vien_id  = fields.Many2one('nhan_vien', string='Nhân viên thực hiện', tracking=True)
    noi_dung      = fields.Text(string='Nội dung trao đổi')

    ket_qua = fields.Selection([
        ('quan_tam',        'Khách quan tâm'),
        ('hen_lai',         'Hẹn liên hệ lại'),
        ('chot_hop_dong',   'Chốt hợp đồng'),
        ('khong_tiem_nang', 'Không tiềm năng'),
    ], string='Kết quả', tracking=True)

    hen_lien_he_tiep = fields.Datetime(string='Hẹn liên hệ tiếp', index=True)
    trang_thai = fields.Selection([
        ('planned', 'Đang theo dõi'),
        ('done',    'Hoàn thành'),
        ('cancel',  'Hủy'),
    ], string='Trạng thái', default='planned', required=True, tracking=True, index=True)

    # ── Liên kết Task tự động tạo ─────────────────────────
    cong_viec_id = fields.Many2one(
        'cong_viec', string='Task liên quan',
        readonly=True, copy=False,
        help='Task được tự động tạo khi ghi nhận tương tác này'
    )

    tu_dong_tao_task = fields.Boolean(
        string='Tự động tạo Task',
        default=True,
        help='Tích để tự động tạo Task trong module Công việc khi lưu tương tác'
    )

    qua_han = fields.Boolean(string='Quá hạn follow-up', compute='_compute_qua_han', store=False)

    # ── Compute ───────────────────────────────────────────
    @api.depends('trang_thai', 'hen_lien_he_tiep')
    def _compute_qua_han(self):
        now = fields.Datetime.now()
        for r in self:
            r.qua_han = bool(r.trang_thai == 'planned' and r.hen_lien_he_tiep and r.hen_lien_he_tiep < now)

    # ── Validate ──────────────────────────────────────────
    @api.constrains('ngay_lien_he', 'hen_lien_he_tiep', 'ket_qua')
    def _check_timeline_and_followup(self):
        for r in self:
            if r.hen_lien_he_tiep and r.ngay_lien_he and r.hen_lien_he_tiep < r.ngay_lien_he:
                raise ValidationError(_('Hẹn liên hệ tiếp phải lớn hơn thời điểm tương tác.'))
            if r.ket_qua == 'hen_lai' and not r.hen_lien_he_tiep:
                raise ValidationError(_('Khi kết quả là "Hẹn liên hệ lại", vui lòng nhập "Hẹn liên hệ tiếp".'))

    # ── Create / Write ────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Tự động gán nhân viên phụ trách nếu chưa có
            if vals.get('khach_hang_id') and not vals.get('nhan_vien_id'):
                kh = self.env['khach_hang'].browse(vals['khach_hang_id'])
                if kh.nhan_vien_phu_trach_id:
                    vals['nhan_vien_id'] = kh.nhan_vien_phu_trach_id.id
        records = super().create(vals_list)
        records._sync_khach_hang_status()
        # Tự động tạo Task sau khi tạo tương tác
        for r in records:
            if r.tu_dong_tao_task and not r.cong_viec_id:
                r._auto_create_task()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_khach_hang_status()
        return res

    # ── Core: Tự động tạo Task ────────────────────────────
    def _auto_create_task(self):
        """Tạo Task trong module Công việc từ tương tác khách hàng."""
        self.ensure_one()
        DuAn = self.env['du_an']
        CongViec = self.env['cong_viec']

        kh = self.khach_hang_id
        nv = self.nhan_vien_id

        # Tìm hoặc tạo dự án "Chăm sóc KH" cho khách hàng này
        du_an = DuAn.search([
            ('khach_hang_id', '=', kh.id),
            ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
        ], limit=1)

        if not du_an:
            du_an = DuAn.create({
                'ma_du_an':       self.env['ir.sequence'].next_by_code('du_an') or 'DA-NEW',
                'ten_du_an':      f'Chăm sóc KH: {kh.ten_khach_hang}',
                'mo_ta':          f'Dự án tự động tạo để quản lý công việc chăm sóc khách hàng {kh.ten_khach_hang}',
                'ngay_bat_dau':   fields.Date.today(),
                'trang_thai':     'dang_thuc_hien',
                'khach_hang_id':  kh.id,
                'nguoi_quan_ly_id': nv.id if nv else False,
            })

        # Tên task theo loại tương tác
        LOAI_MAP = {
            'call':     'Gọi điện',
            'email':    'Email',
            'meeting':  'Họp trực tiếp',
            'zalo':     'Zalo/Chat',
            'bao_gia':  'Gửi báo giá',
            'lich_hen': 'Lịch hẹn',
            'other':    'Tương tác',
        }
        prefix = LOAI_MAP.get(self.loai_tuong_tac, 'Tương tác')

        deadline = self.hen_lien_he_tiep.date() if self.hen_lien_he_tiep else fields.Date.today() + timedelta(days=3)

        task = CongViec.create({
            'ma_cong_viec':      self.env['ir.sequence'].next_by_code('cong_viec') or 'CV-NEW',
            'ten_cong_viec':     f'[{prefix}] {self.tieu_de} — {kh.ten_khach_hang}',
            'mo_ta':             (self.noi_dung or '') + f'\n\n📌 Tạo tự động từ tương tác KH ngày {fields.Date.today()}',
            'du_an_id':          du_an.id,
            'nguoi_phu_trach_id': nv.id if nv else False,
            'ngay_bat_dau':      fields.Date.today(),
            'ngay_ket_thuc':     deadline,
            'trang_thai':        'cho_xu_ly',
            'do_uu_tien':        'trung_binh',
        })
        self.cong_viec_id = task.id

        # Ghi log lên chatter
        self.message_post(
            body=_(
                '<b>✅ Task đã được tự động tạo:</b> '
                '<a href="/web#id=%d&model=cong_viec">%s</a> '
                '(Dự án: %s, Người phụ trách: %s)'
            ) % (task.id, task.ten_cong_viec, du_an.ten_du_an, nv.ho_va_ten if nv else 'Chưa có')
        )
        return task

    # ── Button xem Task ───────────────────────────────────
    def action_xem_task(self):
        self.ensure_one()
        if not self.cong_viec_id:
            return
        return {
            'name': 'Task liên quan',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'form',
            'res_id': self.cong_viec_id.id,
        }

    def action_tao_task_thu_cong(self):
        """Tạo lại task nếu chưa có hoặc task cũ đã xóa."""
        for r in self:
            if not r.cong_viec_id or not r.cong_viec_id.exists():
                r._auto_create_task()

    # ── Sync trạng thái KH ────────────────────────────────
    def _sync_khach_hang_status(self):
        for r in self.filtered('khach_hang_id'):
            if r.ket_qua == 'chot_hop_dong':
                r.khach_hang_id.trang_thai_hop_tac = 'dang_hop_tac'
            elif r.ket_qua == 'khong_tiem_nang':
                r.khach_hang_id.trang_thai_hop_tac = 'ngung_hop_tac'
            elif r.ket_qua in ['quan_tam', 'hen_lai'] and r.khach_hang_id.trang_thai_hop_tac == 'tiem_nang':
                r.khach_hang_id.trang_thai_hop_tac = 'dang_hop_tac'

    # ── Actions ───────────────────────────────────────────
    def action_mark_done(self):
        self.write({'trang_thai': 'done'})
        # Đánh dấu Task hoàn thành nếu có
        for r in self:
            if r.cong_viec_id and r.cong_viec_id.trang_thai not in ['hoan_thanh', 'huy_bo']:
                r.cong_viec_id.write({'trang_thai': 'hoan_thanh'})

    def action_mark_cancel(self):
        self.write({'trang_thai': 'cancel'})

    def action_bulk_mark_done(self):
        self.filtered(lambda r: r.trang_thai == 'planned').write({'trang_thai': 'done'})

    def action_bulk_postpone_2_days(self):
        now = fields.Datetime.now()
        target = now + timedelta(days=2)
        for r in self.filtered(lambda r: r.trang_thai == 'planned'):
            if not r.hen_lien_he_tiep or r.hen_lien_he_tiep < now:
                r.hen_lien_he_tiep = target

    # ── Cron jobs ─────────────────────────────────────────
    @api.model
    def _cron_create_overdue_followup_activities(self):
        overdue = self.search([
            ('trang_thai', '=', 'planned'),
            ('hen_lien_he_tiep', '!=', False),
            ('hen_lien_he_tiep', '<', fields.Datetime.now()),
        ])
        if not overdue:
            return
        model_id     = self.env['ir.model']._get_id('khach_hang_tuong_tac')
        act_type     = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        act_type_id  = act_type.id if act_type else False
        act_model    = self.env['mail.activity'].sudo()
        today        = fields.Date.context_today(self)
        for r in overdue:
            user = r.nhan_vien_id.user_id or r.khach_hang_id.nhan_vien_phu_trach_id.user_id
            if not user:
                continue
            exists = act_model.search_count([
                ('res_model_id', '=', model_id), ('res_id', '=', r.id),
                ('user_id', '=', user.id), ('activity_type_id', '=', act_type_id),
            ])
            if exists:
                continue
            act_model.create({
                'res_id': r.id, 'res_model_id': model_id,
                'user_id': user.id, 'activity_type_id': act_type_id,
                'date_deadline': today,
                'summary': _('Follow-up quá hạn: %s') % r.tieu_de,
                'note': _('Khách hàng: %s\nĐến hẹn: %s') % (
                    r.khach_hang_id.ten_khach_hang, fields.Datetime.to_string(r.hen_lien_he_tiep)),
            })

    @api.model
    def _cron_escalate_critical_overdue_followups(self):
        threshold = fields.Datetime.now() - timedelta(days=2)
        critical  = self.search([
            ('trang_thai', '=', 'planned'),
            ('hen_lien_he_tiep', '!=', False),
            ('hen_lien_he_tiep', '<', threshold),
        ])
        if not critical:
            return 0
        manager_group = self.env.ref('quan_ly_khach_hang.group_khach_hang_manager', raise_if_not_found=False)
        managers = manager_group.users.filtered('active') if manager_group else self.env['res.users']
        if not managers:
            return 0
        model_id    = self.env['ir.model']._get_id('khach_hang_tuong_tac')
        act_type    = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        act_type_id = act_type.id if act_type else False
        act_model   = self.env['mail.activity'].sudo()
        today       = fields.Date.context_today(self)
        count = 0
        for r in critical:
            for manager in managers:
                exists = act_model.search_count([
                    ('res_model_id', '=', model_id), ('res_id', '=', r.id),
                    ('user_id', '=', manager.id), ('summary', 'ilike', 'Escalation'),
                ])
                if exists:
                    continue
                act_model.create({
                    'res_id': r.id, 'res_model_id': model_id,
                    'user_id': manager.id, 'activity_type_id': act_type_id,
                    'date_deadline': today,
                    'summary': _('Escalation follow-up quá hạn: %s') % r.tieu_de,
                    'note': _('Khách hàng: %s\nQuá hạn từ: %s\nNgười phụ trách: %s') % (
                        r.khach_hang_id.ten_khach_hang,
                        fields.Datetime.to_string(r.hen_lien_he_tiep),
                        r.nhan_vien_id.display_name or _('Chưa có')),
                })
                count += 1
        return count