# -*- coding: utf-8 -*-
import re
import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_FALLBACK = [
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
]


class ChatbotConversation(models.Model):
    _name        = 'chatbot.conversation'
    _description = 'Cuộc hội thoại Chatbot'
    _order       = 'create_date desc'

    name         = fields.Char('Tiêu đề', compute='_compute_name', store=True)
    user_id      = fields.Many2one('res.users', default=lambda self: self.env.user)
    message_ids  = fields.One2many('chatbot.message', 'conversation_id', string='Tin nhắn')
    active       = fields.Boolean(default=True)

    @api.depends('message_ids')
    def _compute_name(self):
        for r in self:
            first = r.message_ids.filtered(lambda m: m.is_user).sorted('create_date')[:1]
            if first:
                txt = first.content or ''
                r.name = (txt[:50] + '...') if len(txt) > 50 else txt
            else:
                r.name = f'Hội thoại #{r.id or "mới"}'


class ChatbotMessage(models.Model):
    _name        = 'chatbot.message'
    _description = 'Tin nhắn Chatbot'
    _order       = 'create_date asc'

    conversation_id = fields.Many2one('chatbot.conversation', ondelete='cascade')
    content         = fields.Text('Nội dung', required=True)
    is_user         = fields.Boolean('Từ người dùng', default=True)
    timestamp       = fields.Datetime(default=fields.Datetime.now)
    intent          = fields.Char('Intent')


class ChatbotAssistant(models.Model):
    _name        = 'chatbot.assistant'
    _description = 'Cấu hình Chatbot AI'
    _rec_name    = 'name'

    name           = fields.Char('Tên', default='AI Assistant ERP', required=True)
    active         = fields.Boolean(default=True)
    gemini_api_key = fields.Char('Gemini API Key')
    use_gemini     = fields.Boolean('Dùng Gemini AI', default=True)
    temperature    = fields.Float('Temperature', default=0.7)
    max_tokens     = fields.Integer('Max Tokens', default=1000)

    # ──────────────────────────────────────────────────────────────
    # SYSTEM PROMPT
    # ──────────────────────────────────────────────────────────────
    def _get_system_prompt(self):
        today = fields.Date.today().strftime('%d/%m/%Y')
        return f"""Bạn là AI Assistant tích hợp trong hệ thống ERP quản lý doanh nghiệp.
Ngày hôm nay: {today}

🎯 Bạn hỗ trợ 3 module chính:

📋 MODULE NHÂN SỰ:
- Dashboard KPI: tổng nhân viên, lương tháng, biến động payroll, biểu đồ
- Nhân viên: thêm/sửa hồ sơ, CCCD, tài khoản ngân hàng
- Hợp đồng lao động: thử việc/chính thức/thời vụ, cảnh báo hết hạn
- Chấm công: ghi nhận giờ vào/ra, chấm công bất thường
- Nghỉ phép: gửi đơn, phê duyệt/từ chối
- Tính lương: tạo bảng lương tháng, tự động tính, duyệt, xuất file
- Tuyển dụng, Đào tạo & Đánh giá KPI

📋 MODULE CÔNG VIỆC:
- Dashboard KPI: task mở, task bị chặn, tỷ lệ blocked
- Dự án: tạo dự án, thành viên, ngày bắt đầu/kết thúc
- Task: giao việc, deadline, ưu tiên, trạng thái (Chờ/Đang làm/Bị chặn/Hoàn thành)
- Issue & Rủi ro, Timesheet, Báo cáo tiến độ

📋 MODULE KHÁCH HÀNG:
- Dashboard KPI: tổng KH, KH mới, followup quá hạn, tỷ lệ chốt, SLA breach
- Khách hàng: hồ sơ, phân công, cảnh báo trùng liên hệ
- Cơ hội bán hàng (CRM pipeline), Báo giá, Hợp đồng KH, Ticket hỗ trợ
- Tự động tạo Task khi tương tác KH / báo giá được chấp nhận / hợp đồng sắp hết hạn

📌 Quy tắc trả lời:
- Trả lời ngắn gọn, rõ ràng bằng tiếng Việt
- Dùng emoji phù hợp để dễ đọc
- Nếu có dữ liệu thực, ưu tiên hiển thị dữ liệu thực
- Luôn thân thiện và chuyên nghiệp"""

    # ──────────────────────────────────────────────────────────────
    # GEMINI API CALL
    # ──────────────────────────────────────────────────────────────
    def _call_gemini(self, message, context=''):
        api_key = self.gemini_api_key or ''
        if not api_key:
            _logger.warning("Chatbot: Không có Gemini API key")
            return None

        prompt = (f"{self._get_system_prompt()}\n\n"
                  f"Dữ liệu hệ thống hiện tại:\n{context}\n\n"
                  f"Câu hỏi của người dùng: {message}")

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }

        # Thử gemini-2.0-flash trước, fallback sang các model khác
        urls = [f"{GEMINI_API_URL}?key={api_key}"] + [f"{u}?key={api_key}" for u in GEMINI_FALLBACK]
        for url in urls:
            try:
                resp = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=30)
                _logger.info("Gemini HTTP %s", resp.status_code)
                if resp.status_code == 200:
                    data = resp.json()
                    text = (data.get('candidates', [{}])[0]
                                .get('content', {})
                                .get('parts', [{}])[0]
                                .get('text', ''))
                    if text:
                        return text
                elif resp.status_code == 429 or 'quota' in resp.text.lower():
                    _logger.warning("Gemini quota exceeded, trying fallback")
                    continue
                else:
                    _logger.warning("Gemini error %s: %s", resp.status_code, resp.text[:200])
                    break
            except requests.exceptions.Timeout:
                _logger.warning("Gemini timeout")
                break
            except Exception as e:
                _logger.warning("Gemini exception: %s", e)
                break
        return None

    # ──────────────────────────────────────────────────────────────
    # LẤY CONTEXT TỪ DATABASE
    # ──────────────────────────────────────────────────────────────
    def _get_context(self, intent):
        lines = []
        try:
            user = self.env.user
            lines.append(f"Người dùng đang đăng nhập: {user.name}")

            # Tìm nhân viên tương ứng
            nv = self.env['nhan_vien'].search([('email', '=', user.email)], limit=1)
            if nv:
                lines.append(f"Nhân viên: {nv.ho_va_ten} | Phòng ban: {nv.phong_ban_id.ten_phong_ban or 'N/A'}")

            # Nhân sự
            NhanVien = self.env['nhan_vien']
            lines.append(f"Tổng nhân viên đang làm việc: {NhanVien.search_count([('trang_thai','=','active')])}")

            # Công việc
            CV = self.env['cong_viec']
            active_domain = [('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])]
            lines.append(f"Task đang mở: {CV.search_count(active_domain)}")
            lines.append(f"Task bị chặn: {CV.search_count(active_domain + [('bi_chan','=',True)])}")

            # Dự án
            DuAn = self.env['du_an']
            lines.append(f"Dự án đang thực hiện: {DuAn.search_count([('trang_thai','=','dang_thuc_hien')])}")

            # Khách hàng
            KH = self.env['khach_hang']
            lines.append(f"Tổng khách hàng: {KH.search_count([('active','=',True)])}")
            lines.append(f"Khách hàng đang hợp tác: {KH.search_count([('trang_thai_hop_tac','=','dang_hop_tac')])}")

            # Công việc của user (nếu tìm được nhân viên)
            if nv:
                my_tasks = CV.search([
                    ('nguoi_phu_trach_id', '=', nv.id),
                    ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])
                ], limit=5)
                if my_tasks:
                    lines.append(f"\nTask đang làm của {nv.ho_va_ten}:")
                    for t in my_tasks:
                        lines.append(f"  - {t.ten_cong_viec} [{t.trang_thai}] | Dự án: {t.du_an_id.ten_du_an if t.du_an_id else 'N/A'}")

        except Exception as e:
            _logger.warning("Chatbot context error: %s", e)
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────
    # INTENT DETECTION
    # ──────────────────────────────────────────────────────────────
    def _detect_intent(self, msg):
        msg = msg.lower()
        patterns = {
            'chao':          [r'^(xin chào|hello|hi|chào|hey|chao)\b'],
            'nhan_su':       [r'nhân (viên|sự)', r'lương', r'chấm công', r'nghỉ phép', r'hợp đồng lao', r'tuyển dụng', r'phòng ban'],
            'cong_viec':     [r'công việc', r'task', r'dự án', r'tiến độ', r'bị chặn', r'blocked', r'timesheet'],
            'khach_hang':    [r'khách hàng', r'crm', r'báo giá', r'hợp đồng kh', r'ticket', r'tương tác', r'sla'],
            'thong_ke':      [r'thống kê', r'báo cáo', r'tổng quan', r'bao nhiêu', r'số lượng', r'dashboard'],
            'task_cua_toi':  [r'của tôi', r'task của tôi', r'việc của tôi', r'tôi có'],
            'huong_dan':     [r'cách', r'làm sao', r'hướng dẫn', r'như thế nào', r'quy trình', r'thêm mới', r'tạo mới'],
        }
        for intent, kws in patterns.items():
            for kw in kws:
                if re.search(kw, msg):
                    return intent
        return 'general'

    # ──────────────────────────────────────────────────────────────
    # RULE-BASED RESPONSES (fallback khi không có Gemini)
    # ──────────────────────────────────────────────────────────────
    def _rule_response(self, intent, msg):
        user = self.env.user
        nv = self.env['nhan_vien'].search([('email', '=', user.email)], limit=1)

        if intent == 'chao':
            return (
                f"👋 Xin chào <strong>{user.name}</strong>!\n\n"
                "Tôi là <strong>AI Assistant ERP</strong>, có thể giúp bạn:\n"
                "<ul>"
                "<li>👥 Thông tin <strong>Nhân sự</strong> – nhân viên, lương, chấm công</li>"
                "<li>📋 Quản lý <strong>Công việc</strong> – dự án, task, tiến độ</li>"
                "<li>🤝 Chăm sóc <strong>Khách hàng</strong> – CRM, báo giá, hợp đồng</li>"
                "<li>📊 <strong>Thống kê</strong> tổng quan hệ thống</li>"
                "</ul>"
                "Bạn cần hỗ trợ gì?",
                ['Thống kê tổng quan', 'Task của tôi', 'Hướng dẫn nhân sự']
            )

        if intent == 'task_cua_toi':
            if not nv:
                return ("ℹ️ Không tìm thấy hồ sơ nhân viên của bạn trong hệ thống.", [])
            CV = self.env['cong_viec']
            tasks = CV.search([
                ('nguoi_phu_trach_id', '=', nv.id),
                ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])
            ], limit=8)
            if not tasks:
                return (f"✅ <strong>{nv.ho_va_ten}</strong> không có task nào đang xử lý.", [])
            lines = [f"📋 <strong>Task của {nv.ho_va_ten}</strong> ({len(tasks)} task):<br>"]
            icons = {'moi': '🆕', 'cho_xu_ly': '⏳', 'dang_thuc_hien': '🔵', 'tam_dung': '🟠'}
            for t in tasks:
                icon = icons.get(t.trang_thai, '📌')
                da   = t.du_an_id.ten_du_an if t.du_an_id else 'N/A'
                dl   = t.ngay_ket_thuc.strftime('%d/%m/%Y') if t.ngay_ket_thuc else 'Chưa có'
                lines.append(f"{icon} <strong>{t.ten_cong_viec}</strong><br>&nbsp;&nbsp;&nbsp;Dự án: {da} | Deadline: {dl}")
            return ('<br>'.join(lines), ['Thống kê tổng quan', 'Công việc bị chặn'])

        if intent == 'thong_ke':
            NV  = self.env['nhan_vien']
            CV  = self.env['cong_viec']
            DA  = self.env['du_an']
            KH  = self.env['khach_hang']
            nv_count  = NV.search_count([('trang_thai', '=', 'active')])
            cv_open   = CV.search_count([('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])])
            cv_block  = CV.search_count([('bi_chan', '=', True), ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])])
            da_active = DA.search_count([('trang_thai', '=', 'dang_thuc_hien')])
            kh_total  = KH.search_count([('active', '=', True)])
            kh_hop    = KH.search_count([('trang_thai_hop_tac', '=', 'dang_hop_tac')])
            return (
                "📊 <strong>Thống kê tổng quan hệ thống:</strong><br><br>"
                f"👥 <strong>Nhân sự:</strong> {nv_count} nhân viên đang làm việc<br>"
                f"📁 <strong>Dự án:</strong> {da_active} dự án đang thực hiện<br>"
                f"✅ <strong>Công việc:</strong> {cv_open} task đang mở | {cv_block} task bị chặn<br>"
                f"🤝 <strong>Khách hàng:</strong> {kh_total} tổng | {kh_hop} đang hợp tác",
                ['Task của tôi', 'Hướng dẫn nhân sự', 'Hướng dẫn khách hàng']
            )

        if intent == 'nhan_su':
            NV = self.env['nhan_vien']
            count = NV.search_count([('trang_thai', '=', 'active')])
            return (
                f"👥 <strong>Module Quản lý Nhân sự</strong> — hiện có <strong>{count}</strong> nhân viên đang làm việc.<br><br>"
                "<strong>Các chức năng chính:</strong><br>"
                "<ul>"
                "<li><strong>Nhân viên</strong>: thêm/sửa hồ sơ, CCCD, tài khoản ngân hàng</li>"
                "<li><strong>Hợp đồng</strong>: thử việc/chính thức/thời vụ, cảnh báo hết hạn</li>"
                "<li><strong>Chấm công</strong>: ghi nhận giờ vào/ra, bất thường</li>"
                "<li><strong>Tính lương</strong>: bảng lương tháng, tự động tính, duyệt</li>"
                "<li><strong>Nghỉ phép</strong>: gửi đơn, phê duyệt</li>"
                "</ul>",
                ['Thêm nhân viên mới', 'Tính lương tháng', 'Chấm công']
            )

        if intent == 'cong_viec':
            CV = self.env['cong_viec']
            open_c  = CV.search_count([('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])])
            block_c = CV.search_count([('bi_chan', '=', True), ('trang_thai', 'not in', ['hoan_thanh', 'huy_bo'])])
            return (
                f"📋 <strong>Module Quản lý Công việc</strong> — <strong>{open_c}</strong> task đang mở, <strong>{block_c}</strong> bị chặn.<br><br>"
                "<strong>Các chức năng chính:</strong><br>"
                "<ul>"
                "<li><strong>Dự án</strong>: tạo, quản lý, thêm thành viên</li>"
                "<li><strong>Task</strong>: giao việc, deadline, ưu tiên, trạng thái</li>"
                "<li><strong>Timesheet</strong>: ghi nhận giờ làm theo task</li>"
                "<li><strong>Báo cáo tiến độ</strong>: % hoàn thành, export</li>"
                "</ul>"
                "💡 Khi tạo tương tác với KH, hệ thống <strong>tự động tạo Task</strong> tương ứng!",
                ['Task của tôi', 'Tạo dự án mới', 'Thống kê tổng quan']
            )

        if intent == 'khach_hang':
            KH = self.env['khach_hang']
            total   = KH.search_count([('active', '=', True)])
            hop_tac = KH.search_count([('trang_thai_hop_tac', '=', 'dang_hop_tac')])
            return (
                f"🤝 <strong>Module Quản lý Khách hàng</strong> — <strong>{total}</strong> KH tổng, <strong>{hop_tac}</strong> đang hợp tác.<br><br>"
                "<strong>Các chức năng chính:</strong><br>"
                "<ul>"
                "<li><strong>Khách hàng</strong>: hồ sơ, phân công, cảnh báo trùng</li>"
                "<li><strong>Cơ hội bán hàng</strong>: CRM pipeline, theo dõi deal</li>"
                "<li><strong>Báo giá</strong>: tạo/gửi, chuyển thành hợp đồng</li>"
                "<li><strong>Ticket hỗ trợ</strong>: SLA, xử lý, cảnh báo vi phạm</li>"
                "</ul>"
                "💡 Tương tác KH → <strong>tự động tạo Task</strong>. Báo giá được chấp nhận → <strong>tự động tạo Task theo dõi HĐ</strong>.",
                ['Thêm khách hàng', 'Tạo báo giá', 'Thống kê tổng quan']
            )

        if intent == 'huong_dan':
            return (
                "📚 <strong>Hướng dẫn nhanh các thao tác chính:</strong><br><br>"
                "<strong>➕ Thêm nhân viên:</strong><br>"
                "Menu Nhân viên → Tạo mới → Điền hồ sơ → Lưu<br><br>"
                "<strong>📋 Tạo task:</strong><br>"
                "Menu Công việc → Tạo mới → Chọn dự án, giao việc → Lưu<br><br>"
                "<strong>🤝 Thêm khách hàng:</strong><br>"
                "Menu Khách hàng → Tạo mới → Điền thông tin → Lưu<br><br>"
                "<strong>💰 Tạo bảng lương:</strong><br>"
                "Menu Tính lương → Tạo mới → Chọn tháng → Tính lương → Duyệt",
                ['Thống kê tổng quan', 'Task của tôi', 'Hướng dẫn chi tiết hơn']
            )

        # general
        return (
            "🤔 Tôi chưa hiểu rõ câu hỏi.<br>Bạn có thể hỏi về:<br>"
            "<ul>"
            "<li>👥 Nhân sự (nhân viên, lương, chấm công)</li>"
            "<li>📋 Công việc (dự án, task, tiến độ)</li>"
            "<li>🤝 Khách hàng (CRM, báo giá, hợp đồng)</li>"
            "<li>📊 Thống kê tổng quan</li>"
            "</ul>",
            ['Thống kê tổng quan', 'Task của tôi', 'Hướng dẫn']
        )

    # ──────────────────────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ──────────────────────────────────────────────────────────────
    @api.model
    def process_message(self, message, conversation_id=None):
        # Tìm hoặc tạo conversation
        if conversation_id:
            conv = self.env['chatbot.conversation'].browse(conversation_id)
            if not conv.exists():
                conv = self.env['chatbot.conversation'].create({'user_id': self.env.user.id})
        else:
            conv = self.env['chatbot.conversation'].create({'user_id': self.env.user.id})

        # Lưu tin nhắn người dùng
        self.env['chatbot.message'].create({
            'conversation_id': conv.id,
            'content':         message,
            'is_user':         True,
        })

        intent    = self._detect_intent(message)
        assistant = self.search([('active', '=', True)], limit=1)

        answer      = None
        suggestions = []

        # 1. Thử Gemini
        if assistant and assistant.use_gemini and assistant.gemini_api_key:
            context = self._get_context(intent)
            answer  = assistant._call_gemini(message, context)

        # 2. Fallback rule-based
        if not answer:
            answer, suggestions = self._rule_response(intent, message)

        # Lưu câu trả lời
        self.env['chatbot.message'].create({
            'conversation_id': conv.id,
            'content':         answer,
            'is_user':         False,
            'intent':          intent,
        })

        return {
            'conversation_id': conv.id,
            'answer':          answer,
            'intent':          intent,
            'suggestions':     suggestions,
        }
