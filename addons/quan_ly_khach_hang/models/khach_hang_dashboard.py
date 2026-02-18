# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models, _


class KhachHangDashboard(models.Model):
    _name = 'khach_hang_dashboard'
    _description = 'Dashboard KPI Khách hàng'
    _rec_name = 'ten_bang'

    ten_bang = fields.Char(string='Tên bảng', required=True, default='Dashboard KPI')

    tong_khach_hang = fields.Integer(string='Tổng khách hàng', compute='_compute_kpis')
    khach_hang_moi_7_ngay = fields.Integer(string='Khách hàng mới (7 ngày)', compute='_compute_kpis')
    khach_hang_dang_hop_tac = fields.Integer(string='Khách hàng đang hợp tác', compute='_compute_kpis')
    khach_hang_chua_phan_cong = fields.Integer(string='Khách hàng chưa phân công', compute='_compute_kpis')
    khach_hang_im_lang_14_ngay = fields.Integer(string='Khách hàng im lặng >14 ngày', compute='_compute_kpis')
    khach_hang_trung_lien_he = fields.Integer(string='Khách hàng trùng liên hệ', compute='_compute_kpis')
    de_xuat_gop_cho_duyet = fields.Integer(string='Đề xuất gộp chờ duyệt', compute='_compute_kpis')
    tong_tuong_tac = fields.Integer(string='Tổng tương tác', compute='_compute_kpis')
    tuong_tac_chot_hop_dong = fields.Integer(string='Tương tác chốt hợp đồng', compute='_compute_kpis')
    followup_qua_han = fields.Integer(string='Follow-up quá hạn', compute='_compute_kpis')
    ty_le_chot = fields.Float(string='Tỷ lệ chốt (%)', compute='_compute_kpis')

    @api.model
    def _get_duplicate_customer_ids(self):
        self.env.cr.execute("""
            SELECT kh.id
              FROM khach_hang kh
             WHERE kh.active = TRUE
               AND (
                    (kh.email_normalized IS NOT NULL AND kh.email_normalized != '' AND EXISTS (
                        SELECT 1 FROM khach_hang kh2
                         WHERE kh2.id != kh.id
                           AND kh2.active = TRUE
                           AND kh2.email_normalized = kh.email_normalized
                    ))
                 OR (kh.phone_normalized IS NOT NULL AND kh.phone_normalized != '' AND EXISTS (
                        SELECT 1 FROM khach_hang kh3
                         WHERE kh3.id != kh.id
                           AND kh3.active = TRUE
                           AND kh3.phone_normalized = kh.phone_normalized
                    ))
               )
        """)
        return [row[0] for row in self.env.cr.fetchall()]

    @api.depends('ten_bang')
    def _compute_kpis(self):
        KhachHang = self.env['khach_hang']
        TuongTac = self.env['khach_hang_tuong_tac']

        now = fields.Datetime.now()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)
        duplicate_ids = self._get_duplicate_customer_ids()
        suggestion_model = self.env['khach_hang_merge_suggestion']

        for record in self:
            record.tong_khach_hang = KhachHang.search_count([])
            record.khach_hang_moi_7_ngay = KhachHang.search_count([('create_date', '>=', seven_days_ago)])
            record.khach_hang_dang_hop_tac = KhachHang.search_count([('trang_thai_hop_tac', '=', 'dang_hop_tac')])
            record.khach_hang_chua_phan_cong = KhachHang.search_count([('nhan_vien_phu_trach_id', '=', False)])
            record.khach_hang_im_lang_14_ngay = KhachHang.search_count([
                '|',
                ('lan_tuong_tac_cuoi_index', '=', False),
                ('lan_tuong_tac_cuoi_index', '<', fourteen_days_ago),
            ])
            record.khach_hang_trung_lien_he = len(duplicate_ids)
            record.de_xuat_gop_cho_duyet = suggestion_model.search_count([('state', '=', 'draft')])

            record.tong_tuong_tac = TuongTac.search_count([])
            record.tuong_tac_chot_hop_dong = TuongTac.search_count([('ket_qua', '=', 'chot_hop_dong')])
            record.followup_qua_han = TuongTac.search_count([
                ('trang_thai', '=', 'planned'),
                ('hen_lien_he_tiep', '!=', False),
                ('hen_lien_he_tiep', '<', now),
            ])

            if record.tong_tuong_tac:
                record.ty_le_chot = (record.tuong_tac_chot_hop_dong / record.tong_tuong_tac) * 100.0
            else:
                record.ty_le_chot = 0.0

    def action_xem_khach_hang_chua_phan_cong(self):
        self.ensure_one()
        return {
            'name': 'Khách hàng chưa phân công',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_phu_trach_id', '=', False)],
        }

    def action_xem_khach_hang_im_lang(self):
        self.ensure_one()
        from_date = fields.Datetime.now() - timedelta(days=14)
        return {
            'name': 'Khách hàng im lặng >14 ngày',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': ['|', ('lan_tuong_tac_cuoi_index', '=', False), ('lan_tuong_tac_cuoi_index', '<', from_date)],
        }

    def action_xem_khach_hang_trung_lien_he(self):
        self.ensure_one()
        duplicate_ids = self._get_duplicate_customer_ids()
        return {
            'name': 'Khách hàng trùng liên hệ',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', duplicate_ids or [0])],
        }

    def action_xem_khach_hang_moi(self):
        self.ensure_one()
        from_date = fields.Datetime.now() - timedelta(days=7)
        return {
            'name': 'Khách hàng mới 7 ngày',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('create_date', '>=', from_date)],
        }

    def action_xem_khach_hang_dang_hop_tac(self):
        self.ensure_one()
        return {
            'name': 'Khách hàng đang hợp tác',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': [('trang_thai_hop_tac', '=', 'dang_hop_tac')],
        }

    def action_xem_tuong_tac_chot(self):
        self.ensure_one()
        return {
            'name': 'Tương tác chốt hợp đồng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [('ket_qua', '=', 'chot_hop_dong')],
        }

    def action_xem_followup_qua_han(self):
        self.ensure_one()
        return {
            'name': 'Follow-up quá hạn',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [
                ('trang_thai', '=', 'planned'),
                ('hen_lien_he_tiep', '!=', False),
                ('hen_lien_he_tiep', '<', fields.Datetime.now()),
            ],
        }

    def action_chay_nhanh_theo_mau(self):
        self.ensure_one()
        action = self.env.ref('quan_ly_khach_hang.action_khach_hang_transfer_owner_wizard').read()[0]
        template = self.env.ref('quan_ly_khach_hang.transfer_template_overdue_silent_14', raise_if_not_found=False)

        context = dict(self.env.context or {})
        if template:
            context.update({
                'default_transfer_template_id': template.id,
                'default_trang_thai_hop_tac': template.trang_thai_hop_tac,
                'default_only_overdue': template.only_overdue,
                'default_only_silent': template.only_silent,
                'default_silent_days': template.silent_days,
            })

        action['context'] = context
        return action

    def action_tu_dong_phan_cong(self):
        self.ensure_one()
        assigned = self.env['khach_hang']._auto_assign_unowned_customers(limit=500)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tự động phân công hoàn tất'),
                'message': _('Đã tự động phân công %s khách hàng chưa có người phụ trách.') % assigned,
                'type': 'success',
                'sticky': False,
            },
        }

    @api.model
    def _get_manager_users(self):
        manager_group = self.env.ref('quan_ly_khach_hang.group_khach_hang_manager', raise_if_not_found=False)
        return manager_group.users.filtered(lambda user: user.active and user.partner_id and user.email) if manager_group else self.env['res.users']

    @api.model
    def _build_daily_summary_html(self):
        KhachHang = self.env['khach_hang']
        TuongTac = self.env['khach_hang_tuong_tac']

        now = fields.Datetime.now()
        start_today = fields.Datetime.to_datetime(fields.Date.today())
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        total_customers = KhachHang.search_count([('active', '=', True)])
        new_7_days = KhachHang.search_count([('active', '=', True), ('create_date', '>=', seven_days_ago)])
        unassigned = KhachHang.search_count([('active', '=', True), ('nhan_vien_phu_trach_id', '=', False)])
        silent_14 = KhachHang.search_count([
            ('active', '=', True),
            '|',
            ('lan_tuong_tac_cuoi_index', '=', False),
            ('lan_tuong_tac_cuoi_index', '<', fourteen_days_ago),
        ])

        interactions_today = TuongTac.search_count([('ngay_lien_he', '>=', start_today)])
        overdue_followups = TuongTac.search_count([
            ('trang_thai', '=', 'planned'),
            ('hen_lien_he_tiep', '!=', False),
            ('hen_lien_he_tiep', '<', now),
        ])

        return _(
            '<p><strong>Báo cáo tự động cuối ngày</strong></p>'
            '<ul>'
            '<li>Tổng khách hàng: %s</li>'
            '<li>Khách hàng mới 7 ngày: %s</li>'
            '<li>Khách hàng chưa phân công: %s</li>'
            '<li>Khách hàng im lặng &gt;14 ngày: %s</li>'
            '<li>Tương tác phát sinh hôm nay: %s</li>'
            '<li>Follow-up đang quá hạn: %s</li>'
            '</ul>'
        ) % (total_customers, new_7_days, unassigned, silent_14, interactions_today, overdue_followups)

    @api.model
    def _cron_send_daily_manager_digest(self):
        managers = self._get_manager_users()
        if not managers:
            return 0

        body_html = self._build_daily_summary_html()
        subject = _('[CRM] Báo cáo tự động cho Manager - %s') % fields.Date.today()

        mail_model = self.env['mail.mail'].sudo()
        for manager in managers:
            mail_model.create({
                'email_to': manager.email,
                'subject': subject,
                'body_html': body_html,
            })
        return len(managers)

    @api.model
    def _cron_alert_merge_backlog(self, threshold=20, force=False):
        pending_count = self.env['khach_hang_merge_suggestion'].search_count([('state', '=', 'draft')])
        if not force and pending_count <= threshold:
            return 0

        managers = self._get_manager_users()
        if not managers:
            return 0

        params = self.env['ir.config_parameter'].sudo()
        today_key = fields.Date.today().isoformat()
        last_alert_date = params.get_param('quan_ly_khach_hang.merge_backlog_alert_last_date')
        if not force and last_alert_date == today_key:
            return 0

        subject = _('[CRM] Cảnh báo backlog đề xuất gộp: %s') % pending_count
        body_html = _(
            '<p><strong>Cảnh báo tự động</strong></p>'
            '<p>Hiện có <strong>%s</strong> đề xuất gộp khách hàng đang chờ duyệt, vượt ngưỡng <strong>%s</strong>.</p>'
            '<p>Đề nghị Manager vào màn hình "Đề xuất gộp" để xử lý.</p>'
        ) % (pending_count, threshold)

        mail_model = self.env['mail.mail'].sudo()
        for manager in managers:
            mail_model.create({
                'email_to': manager.email,
                'subject': subject,
                'body_html': body_html,
            })

        critical_threshold = int(params.get_param('quan_ly_khach_hang.merge_backlog_critical_threshold', default='50'))
        created_tasks = 0
        if pending_count >= critical_threshold:
            created_tasks = self._create_critical_backlog_tasks(managers, pending_count)

        params.set_param('quan_ly_khach_hang.merge_backlog_alert_last_date', today_key)
        return len(managers), created_tasks

    @api.model
    def _get_or_create_manager_automation_project(self):
        project = self.env['du_an'].search([('ma_du_an', '=', 'DA-AUTO-MANAGER')], limit=1)
        if project:
            return project

        manager_group = self.env.ref('quan_ly_khach_hang.group_khach_hang_manager', raise_if_not_found=False)
        manager_user = manager_group.users.filtered(lambda user: user.active)[:1] if manager_group else self.env['res.users']
        manager_employee = self.env['nhan_vien'].search([('user_id', '=', manager_user.id)], limit=1) if manager_user else self.env['nhan_vien']

        return self.env['du_an'].create({
            'ma_du_an': 'DA-AUTO-MANAGER',
            'ten_du_an': 'Dự án tự động hoá cho Manager',
            'mo_ta': 'Dự án hệ thống tự tạo để chứa công việc cảnh báo vận hành tự động.',
            'ngay_bat_dau': fields.Date.today(),
            'nguoi_quan_ly_id': manager_employee.id if manager_employee else False,
            'trang_thai': 'dang_thuc_hien',
        })

    @api.model
    def _create_critical_backlog_tasks(self, managers, pending_count):
        project = self._get_or_create_manager_automation_project()
        CongViec = self.env['cong_viec']
        NhanVien = self.env['nhan_vien']
        today = fields.Date.today()

        created = 0
        for manager in managers:
            manager_employee = NhanVien.search([('user_id', '=', manager.id)], limit=1)
            task_code = 'CV-AUTO-BACKLOG-%s-%s' % (manager.id, today.strftime('%Y%m%d'))
            exists = CongViec.search_count([
                ('ma_cong_viec', '=', task_code),
            ])
            if exists:
                continue

            CongViec.create({
                'ma_cong_viec': task_code,
                'ten_cong_viec': _('Xử lý backlog đề xuất gộp (%s)') % pending_count,
                'mo_ta': _('Backlog đề xuất gộp đang vượt ngưỡng nghiêm trọng. Vui lòng ưu tiên xử lý ngay trong ngày.'),
                'ngay_bat_dau': today,
                'ngay_ket_thuc': today,
                'du_an_id': project.id,
                'nguoi_phu_trach_id': manager_employee.id if manager_employee else False,
                'do_uu_tien': 'rat_cao',
                'trang_thai': 'moi',
            })
            created += 1
        return created

    def action_gui_bao_cao_ngay(self):
        self.ensure_one()
        sent_count = self._cron_send_daily_manager_digest()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã gửi báo cáo'),
                'message': _('Đã gửi báo cáo tự động tới %s Manager.') % sent_count,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_xem_de_xuat_gop(self):
        self.ensure_one()
        return {
            'name': 'Đề xuất gộp khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_merge_suggestion',
            'view_mode': 'tree,form',
            'domain': [('state', '=', 'draft')],
        }

    def action_gui_canh_bao_backlog(self):
        self.ensure_one()
        sent_count, created_tasks = self._cron_alert_merge_backlog(force=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã gửi cảnh báo backlog'),
                'message': _('Đã gửi cảnh báo tới %s Manager và tạo %s công việc ưu tiên cao.') % (sent_count, created_tasks),
                'type': 'success',
                'sticky': False,
            },
        }
