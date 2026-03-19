/** @odoo-module **/

import { Component, useState, useRef, onMounted, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ──────────────────────────────────────────────
// Quick Action Suggestions
// ──────────────────────────────────────────────
const QUICK_ACTIONS = [
    { icon: "fa-globe", label: "Phân tích thị trường hôm nay", message: "Phân tích tổng quan thị trường chứng khoán Việt Nam hôm nay" },
    { icon: "fa-search", label: "Phân tích mã cổ phiếu", message: "Tôi muốn phân tích một mã cổ phiếu" },
];

// ──────────────────────────────────────────────
// Markdown Renderer (lightweight, client-side)
// ──────────────────────────────────────────────
function renderMarkdown(text) {
    if (!text) return "";
    let html = text;

    // Normalize <br/> back to \n for processing
    html = html.replace(/<br\s*\/?>/gi, '\n');

    // ── Code blocks: ```lang\n...\n``` ──
    html = html.replace(/```[\w]*\n([\s\S]*?)```/g, (_, code) => {
        const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;').trim();
        return `<pre class="ai-md-code"><code>${escaped}</code></pre>`;
    });

    // ── Tables: |col|col| ──
    html = html.replace(/((?:^\|.+\|$\n?)+)/gm, (tableBlock) => {
        const rows = tableBlock.trim().split('\n').filter(r => r.trim());
        if (rows.length < 2) return tableBlock;

        // Check if 2nd row is separator (|---|---|)
        const isSep = /^\|[\s\-:]+\|/.test(rows[1]);
        let headerRow = null;
        let bodyRows = rows;

        if (isSep) {
            headerRow = rows[0];
            bodyRows = rows.slice(2);
        }

        const parseRow = (row, tag) => {
            const cells = row.split('|').filter((c, i, a) => i > 0 && i < a.length - 1);
            return '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
        };

        let table = '<div class="ai-md-table-wrap"><table class="ai-md-table">';
        if (headerRow) {
            table += '<thead>' + parseRow(headerRow, 'th') + '</thead>';
        }
        table += '<tbody>' + bodyRows.map(r => parseRow(r, 'td')).join('') + '</tbody>';
        table += '</table></div>';
        return table;
    });

    // ── Horizontal rules: --- or *** ──
    html = html.replace(/^[\-\*]{3,}$/gm, '<hr class="ai-md-hr"/>');

    // ── Headings ──
    html = html.replace(/^#### (.+)$/gm, '<h5 class="ai-md-h5">$1</h5>');
    html = html.replace(/^### (.+)$/gm, '<h4 class="ai-md-h4">$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3 class="ai-md-h3">$1</h3>');

    // ── Checkboxes ──
    html = html.replace(/^\[x\] (.+)$/gm, '<div class="ai-md-check done"><i class="fa fa-check-square-o"></i> $1</div>');
    html = html.replace(/^\[ \] (.+)$/gm, '<div class="ai-md-check"><i class="fa fa-square-o"></i> $1</div>');

    // ── Bold + Italic ──
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="ai-md-bold">$1</strong>');
    html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em class="ai-md-italic">$1</em>');

    // ── Lists ──
    html = html.replace(/^[\-\*] (.+)$/gm, '<div class="ai-md-bullet"><span class="ai-md-dot">●</span><span>$1</span></div>');
    html = html.replace(/^(\d+)\. (.+)$/gm, '<div class="ai-md-num"><span class="ai-md-num-idx">$1.</span><span>$2</span></div>');

    // ── Inline code ──
    html = html.replace(/`([^`]+)`/g, '<code class="ai-md-inline-code">$1</code>');

    // ── Line breaks ──
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
