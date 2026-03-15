/** @odoo-module **/

import { Component, useState, useRef, onMounted, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ──────────────────────────────────────────────
// Quick Action Suggestions
// ──────────────────────────────────────────────
const QUICK_ACTIONS = [
    { icon: "fa-line-chart", label: "Phân tích FPT", message: "Phân tích FPT" },
    { icon: "fa-globe", label: "Toàn cảnh thị trường", message: "Thị trường hôm nay thế nào?" },
    { icon: "fa-book", label: "RSI là gì?", message: "RSI là gì? Cách sử dụng trong giao dịch?" },
    { icon: "fa-balance-scale", label: "So sánh VNM & HPG", message: "So sánh VNM và HPG" },
];

// ──────────────────────────────────────────────
// Markdown Renderer (lightweight, client-side)
// ──────────────────────────────────────────────
function renderMarkdown(text) {
    if (!text) return "";
    let html = text;

    // Headings: ### Title, ## Title
    html = html.replace(/^### (.+)$/gm, '<h4 style="color: #60a5fa; font-size: 14px; font-weight: 700; margin: 14px 0 6px 0; border-left: 3px solid #3b82f6; padding-left: 8px;">$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3 style="color: #60a5fa; font-size: 15px; font-weight: 700; margin: 16px 0 8px 0; border-left: 3px solid #3b82f6; padding-left: 8px;">$1</h3>');

    // Bold: **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong style="color: #60a5fa;">$1</strong>');

    // Italic: *text*
    html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em style="color: #94a3b8;">$1</em>');

    // Bullet lists: - item or * item
    html = html.replace(/^[\-\*] (.+)$/gm, '<div style="padding-left: 12px; margin: 3px 0; display: flex; align-items: flex-start; gap: 6px;"><span style="color: #3b82f6; font-size: 8px; margin-top: 6px;">●</span><span>$1</span></div>');

    // Numbered lists: 1. item
    html = html.replace(/^(\d+)\. (.+)$/gm, '<div style="padding-left: 12px; margin: 3px 0; display: flex; align-items: flex-start; gap: 6px;"><span style="color: #f59e0b; font-weight: 600; min-width: 18px;">$1.</span><span>$2</span></div>');

    // Inline code: `code`
    html = html.replace(/`([^`]+)`/g, '<code style="background: rgba(59,130,246,0.15); color: #93c5fd; padding: 1px 5px; border-radius: 3px; font-size: 13px;">$1</code>');

    // Emojis are already supported, no conversion needed

    // Line breaks
    html = html.replace(/\n/g, '<br/>');

    return html;
}

export class AIChatbot extends Component {
    setup() {
        this.orm = useService("orm");
        this.chatBodyRef = useRef("chatBody");

        this.state = useState({
            isOpen: false,
            isTyping: false,
            inputValue: "",
            showQuickActions: true,
            messages: [
                {
                    id: 0,
                    sender: 'bot',
                    type: 'text',
                    text: 'Xin chào! Tôi là ARC Intelligence — Trợ lý AI chuyên tư vấn chứng khoán của bạn.',
                }
            ],
            msgCounter: 1
        });

        // Make quick actions available in template
        this.quickActions = QUICK_ACTIONS;
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            this.scrollToBottom();
        }
    }

    onQuickAction(action) {
        this.state.inputValue = action.message;
        this.state.showQuickActions = false;
        this.sendMessage();
    }

    async sendMessage() {
        const text = this.state.inputValue.trim();
        if (!text || this.state.isTyping) return;

        // Hide quick actions after first message
        this.state.showQuickActions = false;

        // Add user message
        this.state.messages.push({
            id: this.state.msgCounter++,
            sender: 'user',
            type: 'text',
            text: text
        });

        this.state.inputValue = "";
        this.state.isTyping = true;
        this.scrollToBottom();

        try {
            const result = await this.orm.call("stock.ticker", "ai_chat", [text]);

            if (result.status === 'success') {
                if (result.type === 'general') {
                    // Render markdown text
                    let textHtml = renderMarkdown(result.data.text_content);
                    result.data.text_html = markup(textHtml);

                } else if (result.type === 'multi') {
                    for (let item of result.data) {
                        if (item.data) {
                            if (item.data.expert_comment) {
                                item.data.expert_comment = markup(item.data.expert_comment);
                            }
                            // Render stars client-side
                            const renderStars = (n) => {
                                const starIcon = '<i class="fa fa-star" style="color: #f59e0b;"></i>';
                                return markup(`${n} ${Array(n).fill(starIcon).join(' ')}`);
                            };
                            if (item.data.price_stars) item.data.price_stars_html = renderStars(item.data.price_stars);
                            if (item.data.trend_stars) item.data.trend_stars_html = renderStars(item.data.trend_stars);
                            if (item.data.pos_stars) item.data.pos_stars_html = renderStars(item.data.pos_stars);
                            if (item.data.flow_stars) item.data.flow_stars_html = renderStars(item.data.flow_stars);
                            if (item.data.volat_stars) item.data.volat_stars_html = renderStars(item.data.volat_stars);
                            if (item.data.base_stars) item.data.base_stars_html = renderStars(item.data.base_stars);
                        }
                    }
                }

                this.state.messages.push({
                    id: this.state.msgCounter++,
                    sender: 'bot',
                    type: result.type,
                    data: result.data
                });
            } else {
                this.state.messages.push({
                    id: this.state.msgCounter++,
                    sender: 'bot',
                    type: 'error',
                    text: result.message || "Lỗi xử lý phản hồi."
                });
            }

        } catch (error) {
            console.error("ARC Chatbot error:", error);
            this.state.messages.push({
                id: this.state.msgCounter++,
                sender: 'bot',
                type: 'error',
                text: "Không thể kết nối tới máy chủ. Vui lòng kiểm tra kết nối mạng và thử lại."
            });
        } finally {
            this.state.isTyping = false;
            this.scrollToBottom();
        }
    }

    retryLastMessage() {
        // Find the last user message and resend it
        for (let i = this.state.messages.length - 1; i >= 0; i--) {
            if (this.state.messages[i].sender === 'user') {
                this.state.inputValue = this.state.messages[i].text;
                // Remove the error message
                if (this.state.messages[this.state.messages.length - 1].type === 'error') {
                    this.state.messages.pop();
                }
                this.sendMessage();
                return;
            }
        }
    }

    onKeyUp(ev) {
        if (ev.key === "Enter") {
            this.sendMessage();
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.chatBodyRef.el) {
                this.chatBodyRef.el.scrollTop = this.chatBodyRef.el.scrollHeight;
            }
        }, 50);
    }
}

AIChatbot.template = "ai_trading_assistant.AIChatbot";

// Register for Odoo 18 backend (main_components)
registry.category("main_components").add("ai_trading_assistant.AIChatbot", {
    Component: AIChatbot,
});

// Register for frontend (website pages)
import { mountComponent } from "@web/env";

registry.category("website_frontend_ready").add("ai_trading_assistant.AIChatbot_init", () => {
    if (document.body) {
        const chatbotContainer = document.createElement("div");
        document.body.appendChild(chatbotContainer);
        mountComponent(AIChatbot, chatbotContainer);
    }
});
