# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class KhachHang(models.Model):
    _name = 'khach_hang'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Khách hàng'
    _rec_name = 'ten_khach_hang'
    _order = 'ma_khach_hang desc'

    ma_khach_hang = fields.Char(string='Mã khách hàng', required=True, index=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Đang hoạt động', default=True)
    ten_khach_hang = fields.Char(string='Tên khách hàng', required=True, tracking=True)
    nguoi_lien_he = fields.Char(string='Người liên hệ')
    email = fields.Char(string='Email')
    dien_thoai = fields.Char(string='Điện thoại')
    email_normalized = fields.Char(string='Email chuẩn hóa', compute='_compute_contact_normalized', store=True, index=True)
    phone_normalized = fields.Char(string='Điện thoại chuẩn hóa', compute='_compute_contact_normalized', store=True, index=True)
    dia_chi = fields.Text(string='Địa chỉ')
    mo_ta = fields.Text(string='Ghi chú')

    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string='Nhân viên phụ trách', tracking=True)
    trang_thai_hop_tac = fields.Selection([
        ('tiem_nang', 'Tiềm năng'),
        ('dang_hop_tac', 'Đang hợp tác'),
        ('tam_ngung', 'Tạm ngưng'),
        ('ngung_hop_tac', 'Ngừng hợp tác'),
    ], string='Trạng thái hợp tác', default='tiem_nang', tracking=True)

    du_an_ids = fields.One2many('du_an', 'khach_hang_id', string='Dự án')
    tuong_tac_ids = fields.One2many('khach_hang_tuong_tac', 'khach_hang_id', string='Lịch sử tương tác')
    cong_viec_ids = fields.Many2many('cong_viec', compute='_compute_cong_viec_ids', string='Công việc', store=False)

    so_du_an = fields.Integer(string='Số dự án', compute='_compute_thong_ke', store=True)
    so_du_an_dang_thuc_hien = fields.Integer(string='Dự án đang thực hiện', compute='_compute_thong_ke', store=True)
    tong_ngan_sach = fields.Float(string='Tổng ngân sách (VND)', compute='_compute_thong_ke', store=True)
    so_lan_tuong_tac = fields.Integer(string='Số lần tương tác', compute='_compute_thong_ke_tuong_tac', store=False)
    so_tuong_tac_qua_han = fields.Integer(string='Số follow-up quá hạn', compute='_compute_thong_ke_tuong_tac', store=False)
    so_ban_ghi_trung = fields.Integer(string='Bản ghi trùng', compute='_compute_so_ban_ghi_trung', store=False)
    lan_tuong_tac_cuoi_index = fields.Datetime(string='Mốc tương tác gần nhất', compute='_compute_lan_tuong_tac_cuoi_index', store=True, index=True)
    canh_bao_van_hanh = fields.Boolean(string='Cần xử lý', compute='_compute_canh_bao_van_hanh', store=False)
    lan_tuong_tac_cuoi = fields.Datetime(string='Tương tác gần nhất', compute='_compute_lan_tuong_tac_cuoi', store=False)
    de_xuat_gop_ids = fields.One2many('khach_hang_merge_suggestion', 'primary_khach_hang_id', string='Đề xuất gộp')

    _sql_constraints = [
        ('ma_khach_hang_unique', 'unique(ma_khach_hang)', 'Mã khách hàng phải là duy nhất!'),
    ]

    @api.depends('email', 'dien_thoai')
    def _compute_contact_normalized(self):
        for record in self:
            record.email_normalized = record._normalize_email(record.email)
            record.phone_normalized = record._normalize_phone(record.dien_thoai)

    @api.model
    def _normalize_email(self, email):
        return (email or '').strip().lower()

    @api.model
    def _normalize_phone(self, phone):
        raw = (phone or '').strip()
        return ''.join(ch for ch in raw if ch.isdigit())

    @api.constrains('email', 'dien_thoai', 'active')
    def _check_duplicate_contact(self):
        for record in self:
            if not record.active:
                continue

            duplicate_domain = [('id', '!=', record.id), ('active', '=', True)]
            email_value = record._normalize_email(record.email)
            phone_value = record._normalize_phone(record.dien_thoai)

            if email_value:
                duplicate_email = self.search_count(duplicate_domain + [('email_normalized', '=', email_value)])
                if duplicate_email:
                    raise ValidationError(_('Email đã tồn tại trên một khách hàng khác.'))

            if phone_value:
                duplicate_phone = self.search_count(duplicate_domain + [('phone_normalized', '=', phone_value)])
                if duplicate_phone:
                    raise ValidationError(_('Số điện thoại đã tồn tại trên một khách hàng khác.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_khach_hang', _('New')) == _('New'):
                vals['ma_khach_hang'] = self.env['ir.sequence'].next_by_code('khach_hang.sequence') or _('New')
        records = super().create(vals_list)
        return records

    @api.depends('du_an_ids', 'du_an_ids.trang_thai', 'du_an_ids.ngan_sach')
    def _compute_thong_ke(self):
        for record in self:
            record.so_du_an = len(record.du_an_ids)
            record.so_du_an_dang_thuc_hien = len(record.du_an_ids.filtered(lambda p: p.trang_thai in ['chuan_bi', 'dang_thuc_hien', 'tam_dung']))
            record.tong_ngan_sach = sum(record.du_an_ids.mapped('ngan_sach'))

    @api.depends('du_an_ids', 'du_an_ids.cong_viec_ids')
    def _compute_cong_viec_ids(self):
        for record in self:
            record.cong_viec_ids = record.du_an_ids.mapped('cong_viec_ids')

    @api.depends('tuong_tac_ids', 'tuong_tac_ids.trang_thai', 'tuong_tac_ids.hen_lien_he_tiep')
    def _compute_thong_ke_tuong_tac(self):
        now = fields.Datetime.now()
        for record in self:
            record.so_lan_tuong_tac = len(record.tuong_tac_ids)
            record.so_tuong_tac_qua_han = len(record.tuong_tac_ids.filtered(lambda x: x.trang_thai == 'planned' and x.hen_lien_he_tiep and x.hen_lien_he_tiep < now))

    @api.depends('tuong_tac_ids', 'tuong_tac_ids.ngay_lien_he')
    def _compute_lan_tuong_tac_cuoi_index(self):
        for record in self:
            record.lan_tuong_tac_cuoi_index = max(record.tuong_tac_ids.mapped('ngay_lien_he')) if record.tuong_tac_ids else False

    @api.depends('lan_tuong_tac_cuoi_index')
    def _compute_lan_tuong_tac_cuoi(self):
        for record in self:
            record.lan_tuong_tac_cuoi = record.lan_tuong_tac_cuoi_index

    def _compute_canh_bao_van_hanh(self):
        silent_threshold = fields.Datetime.now() - timedelta(days=14)
        for record in self:
            no_owner = not record.nhan_vien_phu_trach_id
            silent_too_long = not record.lan_tuong_tac_cuoi_index or record.lan_tuong_tac_cuoi_index < silent_threshold
            record.canh_bao_van_hanh = bool(no_owner or record.so_tuong_tac_qua_han or silent_too_long)

    def _get_duplicate_domain(self):
        self.ensure_one()
        email_value = self._normalize_email(self.email)
        phone_value = self._normalize_phone(self.dien_thoai)

        if not email_value and not phone_value:
            return [('id', '=', 0)]

        base_domain = [('id', '!=', self.id), ('active', '=', True)]
        if email_value and phone_value:
            return ['|', ('email_normalized', '=', email_value), ('phone_normalized', '=', phone_value)] + base_domain
        if email_value:
            return [('email_normalized', '=', email_value)] + base_domain
        return [('phone_normalized', '=', phone_value)] + base_domain

    def _compute_so_ban_ghi_trung(self):
        for record in self:
            record.so_ban_ghi_trung = self.search_count(record._get_duplicate_domain())

    def action_xem_ban_ghi_trung(self):
        self.ensure_one()
        return {
            'name': 'Bản ghi khách hàng trùng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'view_mode': 'tree,form',
            'domain': self._get_duplicate_domain(),
            'context': {'active_test': True},
        }

    def action_xem_tuong_tac_qua_han(self):
        self.ensure_one()
        return {
            'name': 'Tương tác quá hạn của khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [
                ('khach_hang_id', '=', self.id),
                ('trang_thai', '=', 'planned'),
                ('hen_lien_he_tiep', '!=', False),
                ('hen_lien_he_tiep', '<', fields.Datetime.now()),
            ],
        }

    def action_xem_du_an(self):
        self.ensure_one()
        return {
            'name': 'Dự án khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'du_an',
            'view_mode': 'kanban,tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {
                'default_khach_hang_id': self.id,
                'default_nguoi_quan_ly_id': self.nhan_vien_phu_trach_id.id,
            },
        }

    def action_xem_cong_viec(self):
        self.ensure_one()
        return {
            'name': 'Công việc khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'view_mode': 'kanban,tree,form,calendar',
            'domain': [('du_an_id.khach_hang_id', '=', self.id)],
        }

    def action_xem_tuong_tac(self):
        self.ensure_one()
        return {
            'name': 'Tương tác khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang_tuong_tac',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {
                'default_khach_hang_id': self.id,
                'default_nhan_vien_id': self.nhan_vien_phu_trach_id.id,
            },
        }

    def action_tao_du_an_nhanh(self):
        self.ensure_one()
        du_an = self.env['du_an'].create({
            'ma_du_an': f"DA-{self.ma_khach_hang}-{self.so_du_an + 1}",
            'ten_du_an': f"Dự án {self.ten_khach_hang}",
            'ngay_bat_dau': fields.Date.today(),
            'khach_hang_id': self.id,
            'nguoi_quan_ly_id': self.nhan_vien_phu_trach_id.id,
            'trang_thai': 'chuan_bi',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'du_an',
            'res_id': du_an.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _merge_duplicate_records(self, duplicates):
        self.ensure_one()
        duplicates = duplicates.filtered(lambda rec: rec.id != self.id and rec.active)
        if not duplicates:
            return 0

        if not self.nhan_vien_phu_trach_id:
            self.nhan_vien_phu_trach_id = duplicates.filtered('nhan_vien_phu_trach_id')[:1].nhan_vien_phu_trach_id

        for duplicate in duplicates:
            self.env['du_an'].search([('khach_hang_id', '=', duplicate.id)]).write({'khach_hang_id': self.id})
            self.env['khach_hang_tuong_tac'].search([('khach_hang_id', '=', duplicate.id)]).write({'khach_hang_id': self.id})

            update_vals = {}
            if not self.nguoi_lien_he and duplicate.nguoi_lien_he:
                update_vals['nguoi_lien_he'] = duplicate.nguoi_lien_he
            if not self.email and duplicate.email:
                update_vals['email'] = duplicate.email
            if not self.dien_thoai and duplicate.dien_thoai:
                update_vals['dien_thoai'] = duplicate.dien_thoai
            if not self.dia_chi and duplicate.dia_chi:
                update_vals['dia_chi'] = duplicate.dia_chi
            if duplicate.mo_ta:
                update_vals['mo_ta'] = ((self.mo_ta or '').strip() + '\n' + duplicate.mo_ta.strip()).strip()
            if update_vals:
                self.write(update_vals)

            duplicate.active = False

        return len(duplicates)

    def action_merge_duplicate_khach_hang(self):
        self.ensure_one()

        duplicate_domain = self._get_duplicate_domain()
        if duplicate_domain == [('id', '=', 0)]:
            raise ValidationError(_('Cần có email hoặc số điện thoại để xác định hồ sơ trùng.'))

        duplicates = self.search(duplicate_domain)
        if not duplicates:
            raise ValidationError(_('Không tìm thấy khách hàng trùng để gộp.'))

        merged_count = self._merge_duplicate_records(duplicates)
        self.message_post(body=_('Đã gộp %s khách hàng trùng vào hồ sơ hiện tại.') % merged_count)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'khach_hang',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _cron_generate_merge_suggestions(self):
        Suggestion = self.env['khach_hang_merge_suggestion'].sudo()
        active_customers = self.search([('active', '=', True)])

        groups = {}
        for customer in active_customers:
            if customer.email_normalized:
                groups.setdefault(('email', customer.email_normalized), []).append(customer)
            if customer.phone_normalized:
                groups.setdefault(('phone', customer.phone_normalized), []).append(customer)

        created = 0
        for (reason_type, value), customers in groups.items():
            if len(customers) < 2:
                continue

            sorted_customers = sorted(customers, key=lambda rec: (rec.create_date or fields.Datetime.now(), rec.id))
            primary = sorted_customers[0]
            for duplicate in sorted_customers[1:]:
                exists = Suggestion.search_count([
                    ('primary_khach_hang_id', '=', primary.id),
                    ('duplicate_khach_hang_id', '=', duplicate.id),
                    ('state', '=', 'draft'),
                ])
                if exists:
                    continue
                Suggestion.create({
                    'primary_khach_hang_id': primary.id,
                    'duplicate_khach_hang_id': duplicate.id,
                    'reason': 'same_email' if reason_type == 'email' else 'same_phone',
                    'match_value': value,
                })
                created += 1
        return created

    @api.model
    def _get_auto_assign_candidate_employees(self):
        return self.env['nhan_vien'].search([
            ('trang_thai', 'in', ['active', 'probation']),
            ('user_id', '!=', False),
        ], order='id asc')

    @api.model
    def _auto_assign_unowned_customers(self, limit=200):
        employees = self._get_auto_assign_candidate_employees()
        if not employees:
            return 0

        customers = self.search([
            ('active', '=', True),
            ('nhan_vien_phu_trach_id', '=', False),
        ], order='create_date asc, id asc', limit=limit)
        if not customers:
            return 0

        load_map = {employee.id: 0 for employee in employees}
        grouped_load = self.read_group(
            [('active', '=', True), ('nhan_vien_phu_trach_id', 'in', employees.ids)],
            ['nhan_vien_phu_trach_id'],
            ['nhan_vien_phu_trach_id'],
        )
        for row in grouped_load:
            employee_id = row['nhan_vien_phu_trach_id'][0]
            load_map[employee_id] = row['nhan_vien_phu_trach_id_count']

        assignment_map = {employee.id: self.browse() for employee in employees}
        ordered_ids = sorted(load_map.keys(), key=lambda emp_id: (load_map[emp_id], emp_id))

        for customer in customers:
            target_emp_id = ordered_ids[0]
            assignment_map[target_emp_id] |= customer
            load_map[target_emp_id] += 1
            ordered_ids = sorted(load_map.keys(), key=lambda emp_id: (load_map[emp_id], emp_id))

        for emp_id, customer_batch in assignment_map.items():
            if customer_batch:
                customer_batch.write({'nhan_vien_phu_trach_id': emp_id})

        return len(customers)

    @api.model
    def _cron_auto_assign_unowned_customers(self):
        self._auto_assign_unowned_customers(limit=200)
