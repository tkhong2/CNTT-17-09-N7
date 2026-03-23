# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class ChatbotController(http.Controller):

    @http.route('/erp_chatbot/message', type='json', auth='user', methods=['POST'])
    def send_message(self, message, conversation_id=None, **kwargs):
        """Nhận tin nhắn, gọi AI, trả kết quả."""
        result = request.env['chatbot.assistant'].process_message(
            message, conversation_id
        )
        return result

    @http.route('/erp_chatbot/history', type='json', auth='user', methods=['POST'])
    def get_history(self, conversation_id, **kwargs):
        """Lấy lịch sử tin nhắn của một conversation."""
        conv = request.env['chatbot.conversation'].browse(conversation_id)
        if not conv.exists():
            return {'messages': []}
        messages = []
        for msg in conv.message_ids:
            messages.append({
                'content':   msg.content,
                'is_user':   msg.is_user,
                'timestamp': msg.timestamp.strftime('%H:%M') if msg.timestamp else '',
            })
        return {'messages': messages}
