# -*- coding: utf-8 -*-
import re
import json
import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class ChatbotConversation(models.Model):
    _name        = 'chatbot.conversation'
    _description = 'Cuộc hội thoại Chatbot'
    _order       = 'create_date desc'

    name        = fields.Char('Tiêu đề', compute='_compute_name', store=True)
    user_id     = fields.Many2one('res.users', default=lambda self: self.env.user)
    message_ids = fields.One2many('chatbot.message', 'conversation_id', string='Tin nhắn')
    active      = fields.Boolean(default=True)

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

    name            = fields.Char('Tên', default='AI Assistant ERP', required=True)
    active          = fields.Boolean(default=True)
    # Claude (Anthropic)
    claude_api_key  = fields.Char('Claude API Key (Anthropic)')
    use_claude      = fields.Boolean('Dùng Claude AI', default=True)
    # Gemini (fallback)
    gemini_api_key  = fields.Char('Gemini API Key (fallback)')
    use_gemini      = fields.Boolean('Dùng Gemini AI', default=False)
    temperature     = fields.Float('Temperature', default=0.3)
    max_tokens      = fields.Integer('Max Tokens', default=1024)

    # ──────────────────────────────────────────────────────────────
    # SYSTEM PROMPT
    # ──────────────────────────────────────────────────────────────
    def _get_system_prompt(self, context):
        today = fields.Date.today().strftime('%d/%m/%Y')
        return f"""Bạn là AI Assistant tích hợp trong hệ thống ERP quản lý doanh nghiệp. Ngày hôm nay: {today}

Bạn hỗ trợ 3 module chính:

MODULE NHÂN SỰ (quan_ly_nhan_su):
- Nhân viên: hồ sơ, CCCD, phòng ban, chức vụ, tài khoản ngân hàng
- Hợp đồng lao động: thử việc/chính thức/thời vụ, cảnh báo hết hạn
- Chấm công: giờ vào/ra, bất thường, tăng ca
- Nghỉ phép: gửi đơn, phê duyệt, các loại nghỉ
- Tính lương: bảng lương tháng, tự động tính, phê duyệt, xuất file
- Tuyển dụng, Đào tạo, Đánh giá KPI

MODULE CÔNG VIỆC (quan_ly_cong_viec):
- Dự án: tạo, quản lý thành viên, timeline
- Task: giao việc, deadline, ưu tiên, trạng thái (Mới/Chờ xử lý/Đang thực hiện/Bị chặn/Hoàn thành/Huỷ bỏ)
- Issue & Rủi ro, Timesheet ghi nhận giờ làm
- Báo cáo tiến độ, % hoàn thành

MODULE KHÁCH HÀNG (quan_ly_khach_hang):
- Khách hàng: hồ sơ, phân công, cảnh báo trùng liên hệ
- CRM pipeline: cơ hội bán hàng, theo dõi deal
- Báo giá, Hợp đồng khách hàng
- Ticket hỗ trợ: SLA, xử lý, cảnh báo vi phạm
- Tự động tạo Task khi có tương tác KH

DỮ LIỆU THỰC TẾ HIỆN TẠI:
{context}

QUY TẮC TRẢ LỜI:
- Trả lời bằng tiếng Việt, ngắn gọn và rõ ràng
- Dùng HTML đơn giản (<strong>, <br>, <ul><li>) để format
- Luôn dựa vào dữ liệu thực tế ở trên khi trả lời về số liệu
- Khi hướng dẫn thao tác, chỉ rõ Menu nào → bước nào
- Thân thiện, chuyên nghiệp, không dài dòng"""

    # ──────────────────────────────────────────────────────────────
    # CLAUDE API CALL
    # ──────────────────────────────────────────────────────────────
    def _call_claude(self, message, context=''):
        api_key = self.claude_api_key or ''
        if not api_key:
            return None
        try:
            resp = requests.post(
                CLAUDE_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": self.max_tokens,
                    "system": self._get_system_prompt(context),
                    "messages": [{"role": "user", "content": message}],
                },
                timeout=30,
            )
            _logger.info("Claude HTTP %s", resp.status_code)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('content', [{}])[0].get('text', '')
            else:
                _logger.warning("Claude error %s: %s", resp.status_code, resp.text[:300])
                return None
        except Exception as e:
            _logger.warning("Claude exception: %s", e)
            return None

    # ──────────────────────────────────────────────────────────────
    # GEMINI API CALL (fallback)
    # ──────────────────────────────────────────────────────────────
    def _call_gemini(self, message, context=''):
        api_key = self.gemini_api_key or ''
        if not api_key:
            return None
        prompt = f"{self._get_system_prompt(context)}\n\nCâu hỏi: {message}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": self.temperature, "maxOutputTokens": self.max_tokens},
        }
        for model in GEMINI_MODELS:
            url = f"{GEMINI_BASE.format(model=model)}?key={api_key}"
            try:
                resp = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=30)
                _logger.info("Gemini [%s] HTTP %s", model, resp.status_code)
                if resp.status_code == 200:
                    data = resp.json()
                    text = (data.get('candidates', [{}])[0]
                                .get('content', {}).get('parts', [{}])[0].get('text', ''))
                    if text:
                        return text
                elif resp.status_code in (429, 503):
                    continue
                elif resp.status_code == 404:
                    continue
            except Exception as e:
                _logger.warning("Gemini [%s] error: %s", model, e)
                continue
        return None

    # ──────────────────────────────────────────────────────────────
    # CONTEXT TỪ DATABASE
    # ──────────────────────────────────────────────────────────────
    def _get_context(self):
        lines = []
        try:
            user = self.env.user
            lines.append(f"Người dùng: {user.name} | Email: {user.email}")
            nv = self.env['nhan_vien'].search([('email', '=', user.email)], limit=1)
            if nv:
                pb = nv.phong_ban_id.ten_phong_ban if nv.phong_ban_id else 'N/A'
                lines.append(f"Nhân viên hiện tại: {nv.ho_va_ten} | Phòng ban: {pb}")

            # Nhân sự
            NV = self.env['nhan_vien']
            lines.append(f"[Nhân sự] Đang làm việc: {NV.search_count([('trang_thai','=','active')])} | Tổng: {NV.search_count([])}")
            try:
                HD = self.env['hop_dong']
                lines.append(f"[Hợp đồng] Hiệu lực: {HD.search_count([('trang_thai','=','hieu_luc')])} | Sắp hết hạn: {HD.search_count([('trang_thai','=','hieu_luc'),('ngay_ket_thuc','<=',fields.Date.today())])}")
            except Exception: pass
            try:
                NP = self.env['nghi_phep']
                lines.append(f"[Nghỉ phép] Chờ duyệt: {NP.search_count([('trang_thai','=','cho_duyet')])} | Đã duyệt: {NP.search_count([('trang_thai','=','da_duyet')])}")
            except Exception: pass
            try:
                BL = self.env['bang_luong']
                lines.append(f"[Lương] Đã duyệt: {BL.search_count([('trang_thai','=','da_duyet')])} | Chờ: {BL.search_count([('trang_thai','not in',['da_duyet','huy'])])}")
            except Exception: pass

            # Công việc
            CV = self.env['cong_viec']
            cv_open  = CV.search_count([('trang_thai','not in',['hoan_thanh','huy_bo'])])
            cv_block = CV.search_count([('bi_chan','=',True),('trang_thai','not in',['hoan_thanh','huy_bo'])])
            cv_done  = CV.search_count([('trang_thai','=','hoan_thanh')])
            DA = self.env['du_an']
            lines.append(f"[Công việc] Task mở: {cv_open} | Bị chặn: {cv_block} | Hoàn thành: {cv_done}")
            lines.append(f"[Dự án] Đang thực hiện: {DA.search_count([('trang_thai','=','dang_thuc_hien')])} | Tổng: {DA.search_count([])}")

            if nv:
                my_tasks = CV.search([('nguoi_phu_trach_id','=',nv.id),('trang_thai','not in',['hoan_thanh','huy_bo'])], limit=8)
                if my_tasks:
                    lines.append(f"[Task của {nv.ho_va_ten}]")
                    for t in my_tasks:
                        dl = t.ngay_ket_thuc.strftime('%d/%m/%Y') if t.ngay_ket_thuc else 'N/A'
                        lines.append(f"  - [{t.trang_thai}] {t.ten_cong_viec} | Deadline: {dl}")

            # Khách hàng
            KH = self.env['khach_hang']
            lines.append(f"[Khách hàng] Tổng: {KH.search_count([('active','=',True)])} | Đang hợp tác: {KH.search_count([('trang_thai_hop_tac','=','dang_hop_tac')])}")
            try:
                BG = self.env['bao_gia']
                lines.append(f"[Báo giá] Đang xử lý: {BG.search_count([('trang_thai','not in',['da_xac_nhan','huy'])])}")
            except Exception: pass

        except Exception as e:
            _logger.warning("Context error: %s", e)
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────
    # RULE-BASED (fallback cuối)
    # ──────────────────────────────────────────────────────────────
    def _detect_intent(self, msg):
        m = msg.lower()
        rules = [
            ('chao',            [r'^(xin chào|hello|hi|chào|hey|chao|alo)\b']),
            ('task_cua_toi',    [r'task.*tôi|việc.*tôi|tôi.*đang làm|của tôi']),
            ('thong_ke',        [r'thống kê|tổng quan|bao nhiêu|số lượng|dashboard|tình hình']),
            ('them_nhan_vien',  [r'thêm nhân viên|tạo nhân viên|nhân viên mới|onboard']),
            ('tinh_luong',      [r'tính lương|bảng lương|tạo.*lương|lương tháng']),
            ('hop_dong',        [r'hợp đồng lao|hết hạn.*hợp đồng|ký hợp đồng']),
            ('cham_cong',       [r'chấm công|check.?in|check.?out|đi muộn|tăng ca']),
            ('nghi_phep',       [r'nghỉ phép|xin nghỉ|đơn nghỉ|duyệt nghỉ']),
            ('nhan_su',         [r'nhân (viên|sự)|lương|phòng ban|tuyển dụng|đào tạo']),
            ('cong_viec',       [r'công việc|task|dự án|tiến độ|bị chặn|timesheet|deadline']),
            ('khach_hang',      [r'khách hàng|crm|báo giá|ticket|sla|pipeline|doanh thu']),
            ('huong_dan',       [r'cách|làm sao|hướng dẫn|như thế nào|quy trình|là gì']),
        ]
        for intent, patterns in rules:
            for p in patterns:
                if re.search(p, m):
                    return intent
        return 'general'

    def _rule_response(self, intent, msg):
        user = self.env.user
        nv = self.env['nhan_vien'].search([('email', '=', user.email)], limit=1)

        if intent == 'chao':
            return (
                f"👋 Xin chào <strong>{user.name}</strong>!<br><br>"
                "Tôi có thể giúp bạn:<br>"
                "<ul><li>👥 <strong>Nhân sự</strong> — nhân viên, lương, chấm công, nghỉ phép</li>"
                "<li>📋 <strong>Công việc</strong> — dự án, task, deadline, tiến độ</li>"
                "<li>🤝 <strong>Khách hàng</strong> — CRM, báo giá, hợp đồng, ticket</li>"
                "<li>📊 <strong>Thống kê</strong> — KPI tổng quan</li></ul>"
                "Hỏi gì cũng được nhé!",
                ['Thống kê tổng quan', 'Task của tôi', 'Hướng dẫn']
            )

        if intent == 'task_cua_toi':
            if not nv:
                return ("ℹ️ Không tìm thấy hồ sơ nhân viên của bạn.", [])
            tasks = self.env['cong_viec'].search([
                ('nguoi_phu_trach_id','=',nv.id),
                ('trang_thai','not in',['hoan_thanh','huy_bo'])
            ], limit=8)
            if not tasks:
                return (f"✅ <strong>{nv.ho_va_ten}</strong> không có task nào đang xử lý.", [])
            icons = {'moi':'🆕','cho_xu_ly':'⏳','dang_thuc_hien':'🔵','bi_chan':'🔴','tam_dung':'🟠'}
            lines = [f"📋 <strong>Task của {nv.ho_va_ten}</strong> ({len(tasks)} task):<br>"]
            for t in tasks:
                dl = t.ngay_ket_thuc.strftime('%d/%m/%Y') if t.ngay_ket_thuc else 'Chưa có'
                da = t.du_an_id.ten_du_an if t.du_an_id else 'N/A'
                lines.append(f"{icons.get(t.trang_thai,'📌')} <strong>{t.ten_cong_viec}</strong><br>"
                             f"&nbsp;&nbsp;Dự án: {da} | Deadline: {dl}")
            return ('<br>'.join(lines), ['Thống kê tổng quan', 'Công việc bị chặn'])

        if intent == 'thong_ke':
            NV = self.env['nhan_vien']
            CV = self.env['cong_viec']
            DA = self.env['du_an']
            KH = self.env['khach_hang']
            return (
                "📊 <strong>Thống kê tổng quan:</strong><br><br>"
                f"👥 <strong>Nhân sự:</strong> {NV.search_count([('trang_thai','=','active')])} nhân viên đang làm việc<br>"
                f"📁 <strong>Dự án:</strong> {DA.search_count([('trang_thai','=','dang_thuc_hien')])} đang thực hiện<br>"
                f"✅ <strong>Công việc:</strong> {CV.search_count([('trang_thai','not in',['hoan_thanh','huy_bo'])])} task mở"
                f" | {CV.search_count([('bi_chan','=',True),('trang_thai','not in',['hoan_thanh','huy_bo'])])} bị chặn<br>"
                f"🤝 <strong>Khách hàng:</strong> {KH.search_count([('active','=',True)])} tổng"
                f" | {KH.search_count([('trang_thai_hop_tac','=','dang_hop_tac')])} đang hợp tác",
                ['Task của tôi', 'Hướng dẫn nhân sự', 'Hướng dẫn khách hàng']
            )

        if intent == 'them_nhan_vien':
            return (
                "➕ <strong>Thêm nhân viên mới:</strong><br><br>"
                "<strong>1.</strong> Menu <em>Nhân viên</em> → <em>Tạo mới</em><br>"
                "<strong>2.</strong> Điền: họ tên, ngày sinh, CCCD, email, phòng ban, chức vụ<br>"
                "<strong>3.</strong> Tab <em>Thông tin riêng tư</em> → CCCD, ngày/nơi cấp, quê quán<br>"
                "<strong>4.</strong> Lưu → tạo <em>Hợp đồng lao động</em> cho nhân viên",
                ['Tạo hợp đồng', 'Chấm công', 'Thống kê']
            )

        if intent == 'tinh_luong':
            try:
                BL = self.env['bang_luong']
                da_duyet = BL.search_count([('trang_thai','=','da_duyet')])
                cho_duyet = BL.search_count([('trang_thai','not in',['da_duyet','huy'])])
            except Exception:
                da_duyet = cho_duyet = 0
            return (
                f"💰 <strong>Tính lương</strong> — {da_duyet} bảng đã duyệt"
                + (f", {cho_duyet} chờ duyệt" if cho_duyet else "") + ".<br><br>"
                "<strong>1.</strong> Menu <em>Tính lương</em> → <em>Tạo mới</em><br>"
                "<strong>2.</strong> Chọn tháng/năm và nhân viên<br>"
                "<strong>3.</strong> Nhấn <em>Tính lương</em> → hệ thống tự tính<br>"
                "<strong>4.</strong> Kiểm tra → <em>Duyệt</em>",
                ['Xem bảng lương đã duyệt', 'Thống kê']
            )

        if intent == 'cham_cong':
            try:
                CC = self.env['cham_cong']
                hom_nay = CC.search_count([('ngay_cham_cong','=',fields.Date.today())])
            except Exception:
                hom_nay = 0
            return (
                f"⏱️ <strong>Chấm công</strong> — {hom_nay} bản ghi hôm nay.<br><br>"
                "Menu <em>Chấm công</em> → Tạo mới → Chọn nhân viên + giờ vào/ra → Lưu<br><br>"
                "Xem bất thường: Menu <em>Chấm công bất thường</em>",
                ['Thống kê', 'Hướng dẫn nhân sự']
            )

        if intent == 'nghi_phep':
            try:
                NP = self.env['nghi_phep']
                cho = NP.search_count([('trang_thai','=','cho_duyet')])
            except Exception:
                cho = 0
            return (
                f"🏖️ <strong>Nghỉ phép</strong> — {cho} đơn đang chờ duyệt.<br><br>"
                "<strong>Xin nghỉ:</strong> Menu <em>Nghỉ phép</em> → Tạo mới → Chọn loại + ngày → Gửi duyệt<br>"
                "<strong>Phê duyệt:</strong> Menu Nghỉ phép → Chọn đơn <em>Chờ duyệt</em> → Duyệt/Từ chối",
                ['Thống kê', 'Hướng dẫn nhân sự']
            )

        if intent == 'hop_dong':
            try:
                HD = self.env['hop_dong']
                hl = HD.search_count([('trang_thai','=','hieu_luc')])
            except Exception:
                hl = 0
            return (
                f"📄 <strong>Hợp đồng lao động</strong> — {hl} hợp đồng đang hiệu lực.<br><br>"
                "Loại: Thử việc / Chính thức / Thời vụ<br>"
                "⚠️ Hệ thống <strong>tự cảnh báo</strong> hợp đồng sắp hết hạn qua menu <em>Hợp đồng sắp hết hạn</em>",
                ['Thêm nhân viên mới', 'Thống kê']
            )

        if intent == 'nhan_su':
            count = self.env['nhan_vien'].search_count([('trang_thai','=','active')])
            return (
                f"👥 <strong>Quản lý Nhân sự</strong> — {count} nhân viên đang làm việc.<br><br>"
                "<ul><li>Nhân viên: hồ sơ, CCCD, phòng ban</li>"
                "<li>Hợp đồng: thử việc/chính thức/thời vụ</li>"
                "<li>Chấm công: giờ vào/ra, bất thường</li>"
                "<li>Tính lương: bảng lương tháng, phê duyệt</li>"
                "<li>Nghỉ phép: gửi đơn, phê duyệt</li></ul>",
                ['Thêm nhân viên mới', 'Tính lương tháng', 'Thống kê']
            )

        if intent == 'cong_viec':
            CV = self.env['cong_viec']
            return (
                f"📋 <strong>Quản lý Công việc</strong> — "
                f"{CV.search_count([('trang_thai','not in',['hoan_thanh','huy_bo'])])} task đang mở.<br><br>"
                "<ul><li>Dự án: tạo, quản lý thành viên</li>"
                "<li>Task: giao việc, deadline, ưu tiên</li>"
                "<li>Timesheet: ghi nhận giờ làm</li>"
                "<li>Báo cáo tiến độ: % hoàn thành</li></ul>",
                ['Task của tôi', 'Thống kê']
            )

        if intent == 'khach_hang':
            KH = self.env['khach_hang']
            return (
                f"🤝 <strong>Quản lý Khách hàng</strong> — "
                f"{KH.search_count([('active','=',True)])} KH tổng.<br><br>"
                "<ul><li>Khách hàng: hồ sơ, phân công</li>"
                "<li>CRM pipeline: cơ hội bán hàng</li>"
                "<li>Báo giá → Hợp đồng</li>"
                "<li>Ticket hỗ trợ: SLA, cảnh báo vi phạm</li></ul>",
                ['Thêm khách hàng', 'Thống kê']
            )

        if intent == 'huong_dan':
            return (
                "📚 <strong>Hướng dẫn nhanh:</strong><br><br>"
                "➕ <strong>Thêm nhân viên:</strong> Menu Nhân viên → Tạo mới → Điền hồ sơ → Lưu<br><br>"
                "📋 <strong>Tạo task:</strong> Menu Công việc → Tạo mới → Chọn dự án → Lưu<br><br>"
                "🤝 <strong>Thêm khách hàng:</strong> Menu Khách hàng → Tạo mới → Lưu<br><br>"
                "💰 <strong>Tính lương:</strong> Menu Tính lương → Tạo mới → Chọn tháng → Tính → Duyệt",
                ['Thống kê', 'Task của tôi']
            )

        return (
            "🤔 Tôi chưa hiểu câu hỏi. Bạn có thể hỏi về:<br>"
            "<ul><li>👥 Nhân sự (nhân viên, lương, chấm công, nghỉ phép)</li>"
            "<li>📋 Công việc (dự án, task, deadline)</li>"
            "<li>🤝 Khách hàng (CRM, báo giá, hợp đồng)</li>"
            "<li>📊 Thống kê tổng quan</li></ul>",
            ['Thống kê tổng quan', 'Task của tôi', 'Hướng dẫn']
        )

    # ──────────────────────────────────────────────────────────────
    # MAIN
    # ──────────────────────────────────────────────────────────────
    @api.model
    def process_message(self, message, conversation_id=None):
        if conversation_id:
            conv = self.env['chatbot.conversation'].browse(conversation_id)
            if not conv.exists():
                conv = self.env['chatbot.conversation'].create({'user_id': self.env.user.id})
        else:
            conv = self.env['chatbot.conversation'].create({'user_id': self.env.user.id})

        self.env['chatbot.message'].create({
            'conversation_id': conv.id, 'content': message, 'is_user': True,
        })

        intent    = self._detect_intent(message)
        assistant = self.search([('active','=',True)], limit=1)
        answer    = None
        suggestions = []

        # 1. Claude (thông minh nhất)
        if assistant and assistant.use_claude and assistant.claude_api_key:
            context = self._get_context()
            answer  = self._call_claude(message, context)

        # 2. Gemini (fallback)
        if not answer and assistant and assistant.use_gemini and assistant.gemini_api_key:
            context = self._get_context()
            answer  = self._call_gemini(message, context)

        # 3. Rule-based (fallback cuối)
        if not answer:
            answer, suggestions = self._rule_response(intent, message)

        self.env['chatbot.message'].create({
            'conversation_id': conv.id, 'content': answer,
            'is_user': False, 'intent': intent,
        })

        return {
            'conversation_id': conv.id, 'answer': answer,
            'intent': intent, 'suggestions': suggestions,
        }
