/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useBus } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class GlobalChatbot extends Component {
    static quickSuggestions = [
        "Phân tích danh mục của tôi",
        "Dự đoán xu hướng hôm nay",
        "Cổ phiếu nào nên mua?",
        "Đánh giá rủi ro hiện tại",
    ];

    setup() {
        this.orm = useService("orm");
        this.busService = useService("bus_service");
        this.session = session;
        
        
        this.state = useState({
            isOpen: false,
            input: "",
            messages: [],
            isTyping: false,
            unreadCount: 0,
            reasoningOpen: {},
            showSuggestions: true,
            // Watchlist & Notifications
            showWatchlistPanel: false,
            watchlist: [],
            searchTerm: "",
            searchResults: [],
            pendingSignals: [],
            activeSignal: null,
            tradeQuantity: 100,
        });
        this.messagesRef = useRef("messages");
        
        onMounted(async () => {
            await this._loadWatchlist();
            await this._loadPendingNotifications();
            this._setupBusListener();
        });

        onWillUnmount(() => {
            if (this.busService && this.onNotificationBound) {
                this.busService.unsubscribe("notification", this.onNotificationBound);
            }
        });
    }

    // ==========================================
    // WebSocket Listener for Signal Notifications
    // ==========================================
    _setupBusListener() {
        if (!this.busService) return;

        // User specific channel
        const userId = this.session.uid;
        const channel = `ai_signal_${userId}`;
        
        this.busService.addChannel(channel);
        
        this.onNotificationBound = this._onNotification.bind(this);
        this.busService.subscribe("notification", this.onNotificationBound);
        
        console.log(`[AIChatbot] Listening on channel: ${channel}`);
    }

    _onNotification(notifications) {
        // Defensive: Notifications can be single object or array
        const notifList = Array.isArray(notifications) ? notifications : [notifications];
        
        for (const notif of notifList) {
            if (notif.type === 'signal_notification' || notif.payload?.type === 'signal_notification') {
                const payload = notif.payload || notif;
                console.log('[AIChatbot] Received signal:', payload);
                this._handleSignalNotification(payload);
            }
        }
    }

    _handleSignalNotification(payload) {
        // Add to pending signals
        this.state.pendingSignals.push({
            id: payload.prediction_id,
            symbol: payload.symbol,
            signal_type: payload.signal_type,
            confidence: payload.confidence,
            current_price: payload.current_price,
            create_date: new Date().toISOString(),
        });
        this.state.unreadCount++;
        
        // Show signal popup if not already showing
        if (!this.state.activeSignal) {
            this._showNextSignal();
        }
    }

    _showNextSignal() {
        if (this.state.pendingSignals.length > 0) {
            this.state.activeSignal = this.state.pendingSignals[0];
        } else {
            this.state.activeSignal = null;
        }
    }

    get quickSuggestions() {
        return GlobalChatbot.quickSuggestions;
    }

    // ==========================================
    // Watchlist Management
    // ==========================================
    async _loadWatchlist() {
        try {
            const watchlist = await this.orm.call("ai.chatbot.conversation", "get_watchlist", []);
            this.state.watchlist = watchlist || [];
        } catch (e) {
            console.error('Failed to load watchlist:', e);
        }
    }

    toggleWatchlistPanel() {
        this.state.showWatchlistPanel = !this.state.showWatchlistPanel;
        if (this.state.showWatchlistPanel) {
            this._searchSecurities();
        }
    }

    async _searchSecurities() {
        try {
            const results = await this.orm.call("ai.chatbot.conversation", "get_available_securities", [], {
                search_term: this.state.searchTerm,
                limit: 20,
            });
            this.state.searchResults = results || [];
        } catch (e) {
            console.error('Failed to search securities:', e);
        }
    }

    onSearchInput(ev) {
        this.state.searchTerm = ev.target.value;
        // Debounce search
        clearTimeout(this._searchTimeout);
        this._searchTimeout = setTimeout(() => this._searchSecurities(), 300);
    }

    async addToWatchlist(securityId) {
        try {
            const result = await this.orm.call("ai.chatbot.conversation", "add_to_watchlist", [securityId]);
            if (result.success) {
                await this._loadWatchlist();
                this.notification.add("Đã thêm vào danh sách theo dõi", { type: "success" });
            }
        } catch (e) {
            console.error('Failed to add to watchlist:', e);
        }
    }

    async removeFromWatchlist(securityId) {
        try {
            const result = await this.orm.call("ai.chatbot.conversation", "remove_from_watchlist", [securityId]);
            if (result.success) {
                await this._loadWatchlist();
                this.notification.add("Đã xóa khỏi danh sách theo dõi", { type: "info" });
            }
        } catch (e) {
            console.error('Failed to remove from watchlist:', e);
        }
    }

    isInWatchlist(securityId) {
        return this.state.watchlist.some(w => w.security_id === securityId);
    }

    // ==========================================
    // Signal Notifications & Trading
    // ==========================================
    async _loadPendingNotifications() {
        try {
            const result = await this.orm.call("ai.chatbot.conversation", "get_pending_notifications", []);
            this.state.pendingSignals = result.notifications || [];
            this.state.unreadCount = result.unread_count || 0;
            
            if (this.state.pendingSignals.length > 0 && !this.state.activeSignal) {
                this._showNextSignal();
            }
        } catch (e) {
            console.error('Failed to load notifications:', e);
        }
    }

    async confirmTrade() {
        if (!this.state.activeSignal) return;
        
        try {
            const result = await this.orm.call("ai.chatbot.conversation", "confirm_trade", [this.state.activeSignal.id], {
                quantity: this.state.tradeQuantity,
            });
            
            if (result.success) {
                this.notification.add(`Đã đặt lệnh thành công! Mã: ${result.order_ref}`, { type: "success" });
                this._removeCurrentSignal();
            } else {
                this.notification.add(`Lỗi: ${result.error}`, { type: "danger" });
            }
        } catch (e) {
            console.error('Failed to confirm trade:', e);
            this.notification.add("Không thể đặt lệnh", { type: "danger" });
        }
    }

    async dismissSignal() {
        if (!this.state.activeSignal) return;
        
        try {
            await this.orm.call("ai.chatbot.conversation", "dismiss_notification", [this.state.activeSignal.id]);
            this._removeCurrentSignal();
        } catch (e) {
            console.error('Failed to dismiss signal:', e);
        }
    }

    _removeCurrentSignal() {
        if (this.state.activeSignal) {
            const idx = this.state.pendingSignals.findIndex(s => s.id === this.state.activeSignal.id);
            if (idx >= 0) {
                this.state.pendingSignals.splice(idx, 1);
            }
            this.state.unreadCount = Math.max(0, this.state.unreadCount - 1);
            this._showNextSignal();
        }
    }

    onQuantityChange(ev) {
        this.state.tradeQuantity = parseInt(ev.target.value) || 100;
    }

    sendQuickMessage(text) {
        this.state.input = text;
        this.state.showSuggestions = false;
        this._sendMessage();
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            this.state.unreadCount = 0;
            this._scrollToBottom();
            this._loadPendingNotifications();
        }
    }

    toggleReasoning(msgId) {
        this.state.reasoningOpen[msgId] = !this.state.reasoningOpen[msgId];
    }

    async _sendMessage() {
        if (!this.state.input.trim()) return;

        const userMsg = {
            id: Date.now(),
            role: 'user',
            content: this.state.input,
            time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
        };

        this.state.messages.push(userMsg);
        const text = this.state.input;
        this.state.input = "";
        this.state.isTyping = true;
        this._scrollToBottom();

        try {
            const result = await this.orm.call("ai.chatbot.conversation", "chat_wrapper", [], {
                message: text,
                context: {
                    'website_popup': true
                }
            });

            if (result.success) {
                const botMsg = {
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: result.data.messages.find(m => m.role === 'assistant').content,
                    reasoning_details: result.data.messages.find(m => m.role === 'assistant').reasoning_details,
                    time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                };
                this.state.messages.push(botMsg);
            } else {
                this.state.messages.push({
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: "Error: " + result.error,
                    time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                });
            }

        } catch (error) {
            console.error(error);
             this.state.messages.push({
                id: Date.now() + 1,
                role: 'assistant',
                content: "Network Error: Could not reach FinRL service.",
                time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
            });
        } finally {
            this.state.isTyping = false;
            this._scrollToBottom();
        }
    }

    _onKeydown(ev) {
        if (ev.key === "Enter") {
            this._sendMessage();
        }
    }

    _scrollToBottom() {
        setTimeout(() => {
            if (this.messagesRef.el) {
                this.messagesRef.el.scrollTop = this.messagesRef.el.scrollHeight;
            }
        }, 50);
    }
}

GlobalChatbot.template = "ai_trading_assistant.WebsiteChatbot";

// Mount to backend main components
registry.category("main_components").add("ai_trading_assistant.GlobalChatbot", {
    Component: GlobalChatbot,
});
