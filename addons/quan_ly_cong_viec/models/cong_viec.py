# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CongViec(models.Model):
    _name = "cong_viec"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Công việc"
    _rec_name = "ten_cong_viec"
    _order = "ngay_bat_dau, ma_cong_viec"
    
    ma_cong_viec = fields.Char(string="Mã công việc", required=True, index=True)
    ten_cong_viec = fields.Char(string="Tên công việc", required=True)
    mo_ta = fields.Text(string="Mô tả")
    
    # Thời gian
    ngay_bat_dau = fields.Date(string="Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date(string="Ngày kết thúc")
    
    # Quan hệ
    du_an_id = fields.Many2one('du_an', string="Thuộc dự án", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Khách hàng chăm sóc", tracking=True)
    contact_person_id = fields.Many2one('res.partner', string='Nguoi lien he')
    nguoi_phu_trach_id = fields.Many2one('nhan_vien', string="Người phụ trách")
    user_ids = fields.Many2many(
        'res.users',
        'cong_viec_user_rel',
        'cong_viec_id',
        'user_id',
        string='Người thực hiện (User)',
    )
    
    # Các trường quan hệ tham chiếu ngược
    nguoi_tham_gia_ids = fields.One2many('nguoi_tham_gia', 'cong_viec_id', string="Người tham gia")
    bao_cao_tien_do_ids = fields.One2many('bao_cao_tien_do', 'cong_viec_id', string="Báo cáo tiến độ")
    nguon_luc_ids = fields.One2many('phan_bo_nguon_luc', 'cong_viec_id', string="Nguồn lực phân bổ")
    
    # Thông tin tiến độ
    ke_hoach_gio = fields.Float(string="Kế hoạch (giờ)")
    thuc_te_gio = fields.Float(string="Thực tế (giờ)", compute="_compute_thuc_te_gio", store=True)
    tien_do = fields.Float(string="Tiến độ (%)", compute="_compute_tien_do", store=True)
    
    # Độ ưu tiên, trạng thái
    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('rat_cao', 'Rất cao')
    ], string="Độ ưu tiên", default='trung_binh')
    
    trang_thai = fields.Selection([
        ('moi',           'Mới'),
        ('cho_xu_ly',     'Chờ xử lý'),
        ('dang_thuc_hien','Đang thực hiện'),
        ('tam_dung',      'Tạm dừng'),
        ('hoan_thanh',    'Hoàn thành'),
        ('huy_bo',        'Hủy bỏ'),
    ], string="Trạng thái", default='moi', tracking=True)

    cong_viec_phu_thuoc_ids = fields.Many2many(
        'cong_viec',
        'cong_viec_dependency_rel',
        'cong_viec_id',
        'phu_thuoc_id',
        string='Phụ thuộc công việc',
        help='Công việc này chỉ có thể bắt đầu khi các công việc phụ thuộc đã hoàn thành.'
    )
    cong_viec_bi_chan_ids = fields.Many2many(
        'cong_viec',
        'cong_viec_dependency_rel',
        'phu_thuoc_id',
        'cong_viec_id',
        string='Đang chặn công việc',
        readonly=True,
    )
    bi_chan = fields.Boolean(string='Bị chặn', compute='_compute_bi_chan', store=True)
    ly_do_bi_chan = fields.Text(string='Lý do bị chặn', compute='_compute_bi_chan', store=True)
    
    _sql_constraints = [
        ('ma_cong_viec_unique', 'unique(ma_cong_viec)', 'Mã công việc phải là duy nhất!'),
    ]
    
    @api.depends('bao_cao_tien_do_ids', 'bao_cao_tien_do_ids.so_gio')
    def _compute_thuc_te_gio(self):
        for record in self:
            record.thuc_te_gio = sum(record.bao_cao_tien_do_ids.mapped('so_gio'))
    
    @api.depends('nguoi_tham_gia_ids', 'nguoi_tham_gia_ids.trang_thai')
    def _compute_tien_do(self):
        for record in self:
            if record.nguoi_tham_gia_ids:
                # Đếm số người đã báo cáo
                so_da_bao_cao = len(record.nguoi_tham_gia_ids.filtered(lambda x: x.trang_thai == 'da_bao_cao'))
                tong_tham_gia = len(record.nguoi_tham_gia_ids)
                # Tính phần trăm: (số đã báo cáo / tổng tham gia) × 100
                record.tien_do = (so_da_bao_cao / tong_tham_gia) * 100 if tong_tham_gia > 0 else 0
            else:
                record.tien_do = 0

    @api.depends('cong_viec_phu_thuoc_ids', 'cong_viec_phu_thuoc_ids.trang_thai')
    def _compute_bi_chan(self):
        for record in self:
            waiting = record.cong_viec_phu_thuoc_ids.filtered(lambda task: task.trang_thai != 'hoan_thanh')
            record.bi_chan = bool(waiting)
            record.ly_do_bi_chan = ', '.join(waiting.mapped('ten_cong_viec')) if waiting else False
    
    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_ket_thuc and record.ngay_bat_dau > record.ngay_ket_thuc:
                raise ValidationError(_("Ngày bắt đầu không thể sau ngày kết thúc!"))
    
    @api.constrains('du_an_id', 'ngay_bat_dau', 'ngay_ket_thuc')
    def _check_project_dates(self):
        for record in self:
            if record.du_an_id.ngay_bat_dau and record.ngay_bat_dau < record.du_an_id.ngay_bat_dau:
                raise ValidationError(_("Ngày bắt đầu công việc không thể trước ngày bắt đầu dự án!"))
            
            if record.du_an_id.ngay_ket_thuc and record.ngay_ket_thuc and record.ngay_ket_thuc > record.du_an_id.ngay_ket_thuc:
                raise ValidationError(_("Ngày kết thúc công việc không thể sau ngày kết thúc dự án!"))

    @api.constrains('cong_viec_phu_thuoc_ids')
    def _check_dependency_validity(self):
        for record in self:
            if record in record.cong_viec_phu_thuoc_ids:
                raise ValidationError(_("Công việc không thể phụ thuộc chính nó."))

            if record.du_an_id and any(dep.du_an_id != record.du_an_id for dep in record.cong_viec_phu_thuoc_ids):
                raise ValidationError(_("Chỉ được phép phụ thuộc công việc trong cùng dự án."))

    @api.constrains('nguoi_phu_trach_id', 'user_ids')
    def _check_executor_required(self):
        for record in self:
            if not record.nguoi_phu_trach_id and not record.user_ids:
                raise ValidationError(_("Công việc phải gắn ít nhất một nhân viên thực hiện."))

    @api.onchange('nguoi_phu_trach_id')
    def _onchange_nguoi_phu_trach_id(self):
        for record in self:
            owner_user = record._find_user_from_employee(record.nguoi_phu_trach_id)
            if owner_user and owner_user not in record.user_ids:
                record.user_ids = [(4, owner_user.id)]

    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        for record in self:
            if not record.user_ids:
                continue
            employee = record._find_employee_from_user(record.user_ids[0])
            if employee:
                record.nguoi_phu_trach_id = employee

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Khi chọn Khách hàng:
        1. Tự động điền SĐT & Email vào mô tả (Bước 3 - Mức 1)
        2. Nếu KH Vàng → ưu tiên Cao (Gợi ý 1 - Nâng cao)
        3. Reset contact_person nếu không thuộc KH đã chọn (Gợi ý 2)
        """
        for record in self:
            if not record.partner_id:
                record.contact_person_id = False
                continue

            # Gợi ý 1: KH Vàng → priority cao tự động
            if hasattr(record.partner_id, 'rank') and record.partner_id.rank == 'vang':
                record.do_uu_tien = 'cao'

            # Gợi ý 2: reset người liên hệ nếu không thuộc công ty đã chọn
            if (record.contact_person_id
                    and record.contact_person_id.parent_id != record.partner_id):
                record.contact_person_id = False

            # Bước 3 Mức 1: tự động điền SĐT & Email vào mô tả
            lines = [
                '--- Thông tin chăm sóc khách hàng ---',
                '- Khách hàng : %s' % (record.partner_id.name  or 'N/A'),
                '- Điện thoại : %s' % (record.partner_id.phone or 'N/A'),
                '- Email      : %s' % (record.partner_id.email or 'N/A'),
                '- Phân hạng  : %s' % (dict(record.partner_id._fields['rank'].selection).get(
                    record.partner_id.rank, '') if hasattr(record.partner_id, 'rank') else 'N/A'),
                '-------------------------------------',
            ]
            contact_block = '\n'.join(lines)

            if record.mo_ta:
                if '--- Thông tin chăm sóc khách hàng ---' not in record.mo_ta:
                    record.mo_ta = contact_block + '\n\n' + record.mo_ta
            else:
                record.mo_ta = contact_block

    def _find_user_from_employee(self, employee):
        if not employee or not employee.email:
            return False
        return self.env['res.users'].sudo().search([
            '|', ('login', '=', employee.email), ('email', '=', employee.email)
        ], limit=1)

    def _find_employee_from_user(self, user):
        if not user:
            return False

        NhanVien = self.env['nhan_vien'].sudo()
        if 'user_id' in NhanVien._fields:
            employee = NhanVien.search([('user_id', '=', user.id)], limit=1)
            if employee:
                return employee

        if user.email:
            employee = NhanVien.search([('email', '=', user.email)], limit=1)
            if employee:
                return employee
        if user.login:
            return NhanVien.search([('email', '=', user.login)], limit=1)
        return False

    @api.model
    def _extract_user_ids_from_commands(self, commands):
        if not commands:
            return []
        ids = []
        for command in commands:
            if not isinstance(command, (list, tuple)) or not command:
                continue
            code = command[0]
            if code == 6:
                ids = list(command[2] or [])
            elif code == 4:
                ids.append(command[1])
            elif code in (2, 3):
                ids = [x for x in ids if x != command[1]]
            elif code == 5:
                ids = []
        return ids

    @api.model
    def _prepare_executor_sync_vals(self, vals):
        prepared_vals = dict(vals)
        employee_id = prepared_vals.get('nguoi_phu_trach_id')
        user_commands = prepared_vals.get('user_ids')

        if employee_id:
            employee = self.env['nhan_vien'].browse(employee_id)
            owner_user = self._find_user_from_employee(employee)
            if owner_user and not user_commands:
                prepared_vals['user_ids'] = [(4, owner_user.id)]
            elif owner_user and user_commands:
                current_user_ids = self._extract_user_ids_from_commands(user_commands)
                if owner_user.id not in current_user_ids:
                    prepared_vals['user_ids'] = list(user_commands) + [(4, owner_user.id)]
        elif user_commands:
            user_ids = self._extract_user_ids_from_commands(user_commands)
            if user_ids:
                employee = self._find_employee_from_user(self.env['res.users'].browse(user_ids[0]))
                if employee:
                    prepared_vals['nguoi_phu_trach_id'] = employee.id
        return prepared_vals

    def _sync_executor_bidirectional(self, triggered_by_user_ids=False):
        for record in self:
            update_vals = {}

            if triggered_by_user_ids and record.user_ids:
                mapped_employee = record._find_employee_from_user(record.user_ids[0])
                if mapped_employee and record.nguoi_phu_trach_id != mapped_employee:
                    update_vals['nguoi_phu_trach_id'] = mapped_employee.id

            owner_user = record._find_user_from_employee(record.nguoi_phu_trach_id)
            if owner_user and owner_user not in record.user_ids:
                update_vals['user_ids'] = [(4, owner_user.id)]

            if update_vals:
                record.with_context(skip_executor_sync=True).write(update_vals)

    @api.model_create_multi
    def create(self, vals_list):
        synced_vals_list = [self._prepare_executor_sync_vals(vals) for vals in vals_list]
        records = super().create(synced_vals_list)
        records._sync_executor_bidirectional()
        return records

    def write(self, vals):
        # Lưu trạng thái bi_chan trước khi write
        bi_chan_before = {r.id: r.bi_chan for r in self}
        result = super().write(vals)
        if not self.env.context.get('skip_executor_sync') and {'nguoi_phu_trach_id', 'user_ids'} & set(vals):
            self._sync_executor_bidirectional(
                triggered_by_user_ids=('user_ids' in vals and 'nguoi_phu_trach_id' not in vals)
            )
        # Gửi Telegram khi task chuyển sang bị chặn
        if 'bi_chan' in vals or 'cong_viec_bi_chan_ids' in vals:
            try:
                for task in self:
                    if task.bi_chan and not bi_chan_before.get(task.id):
                        self.env['telegram.config'].notify_task_bi_chan(task)
            except Exception:
                pass
        return result

    @api.model
    def _get_int_param(self, key, default):
        value = self.env['ir.config_parameter'].sudo().get_param(key, default=str(default))
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _create_single_activity(self, summary, note, deadline=False):
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get_id('cong_viec')
        fallback_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env.user

        for task in self:
            owner_user = self._find_user_from_employee(task.nguoi_phu_trach_id)
            if not owner_user:
                owner_user = self._find_user_from_employee(task.du_an_id.nguoi_quan_ly_id)
            if not owner_user:
                owner_user = fallback_user

            existed = self.env['mail.activity'].sudo().search_count([
                ('res_model_id', '=', model_id),
                ('res_id', '=', task.id),
                ('user_id', '=', owner_user.id),
                ('summary', '=', summary),
            ])
            if existed:
                continue

            values = {
                'res_model_id': model_id,
                'res_id': task.id,
                'user_id': owner_user.id,
                'summary': summary,
                'note': note,
                'date_deadline': deadline or fields.Date.today(),
            }
            if todo_type:
                values['activity_type_id'] = todo_type.id
            self.env['mail.activity'].sudo().create(values)

    def action_bat_dau(self):
        for record in self:
            if record.bi_chan:
                raise ValidationError(
                    _("Không thể bắt đầu công việc '%s' vì còn phụ thuộc chưa hoàn thành: %s")
                    % (record.ten_cong_viec, record.ly_do_bi_chan)
                )
            if record.trang_thai not in ['moi', 'tam_dung']:
                raise ValidationError(_("Chỉ công việc Mới hoặc Tạm dừng mới được bắt đầu."))
            record.trang_thai = 'dang_thuc_hien'

    def action_hoan_thanh(self):
        for record in self:
            if record.trang_thai not in ['dang_thuc_hien', 'tam_dung']:
                raise ValidationError(_("Chỉ công việc đang thực hiện hoặc tạm dừng mới được hoàn thành."))
            record.trang_thai = 'hoan_thanh'

    @api.model
    def _cron_task_automation(self):
        today = fields.Date.today()
        stale_days = max(self._get_int_param('quan_ly_cong_viec.task_stale_days', 3), 1)

        overdue_tasks = self.search([
            ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo']),
            ('ngay_ket_thuc', '!=', False),
            ('ngay_ket_thuc', '<', today),
        ])
        for task in overdue_tasks:
            values = {'do_uu_tien': 'rat_cao'}
            if task.trang_thai == 'moi':
                values['trang_thai'] = 'dang_thuc_hien'
            task.write(values)
            task._create_single_activity(
                summary=_("Công việc quá hạn: %s") % task.ten_cong_viec,
                note=_(
                    "Công việc đã quá hạn từ ngày %(deadline)s, tiến độ hiện tại %(progress)s%%. "
                    "Vui lòng xử lý ưu tiên."
                ) % {
                    'deadline': task.ngay_ket_thuc,
                    'progress': task.tien_do,
                },
                deadline=today,
            )

        stale_day = fields.Date.add(today, days=-stale_days)
        stale_tasks = self.search([
            ('trang_thai', 'in', ['moi', 'dang_thuc_hien']),
            ('ngay_bat_dau', '!=', False),
            ('ngay_bat_dau', '<=', stale_day),
        ])
        stale_tasks = stale_tasks.filtered(lambda task: not task.bao_cao_tien_do_ids)
        for task in stale_tasks:
            task._create_single_activity(
                summary=_("Công việc chưa cập nhật tiến độ: %s") % task.ten_cong_viec,
                note=_(
                    "Công việc đã bắt đầu từ %(start)s nhưng chưa có báo cáo tiến độ. "
                    "Vui lòng cập nhật trạng thái thực tế."
                ) % {
                    'start': task.ngay_bat_dau,
                },
                deadline=today,
            )
