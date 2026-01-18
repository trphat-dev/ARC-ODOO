/** @odoo-module **/

/**
 * Auto Match Worker - Tự động khớp lệnh mỗi 1 giây
 * 
 * Worker này chạy nền trên mọi trang để tự động khớp lệnh theo thuật toán Price-Time Priority (FIFO):
 * - Buy orders: Giá cao nhất trước, cùng giá thì thời gian sớm nhất trước
 * - Sell orders: Giá thấp nhất trước, cùng giá thì thời gian sớm nhất trước
 * - Điều kiện khớp: buy_price >= sell_price
 * - Giá khớp: Luôn lấy giá của sell order
 * 
 * Backend sẽ tự query tất cả lệnh pending từ database và khớp theo thuật toán chuẩn Stock Exchange.
 */

(function () {
    // Tránh khởi tạo nhiều lần
    if (window.__tl_autoMatchWorkerStarted) {
        return;
    }
    window.__tl_autoMatchWorkerStarted = true;

    let isMatchingInFlight = false;

    /**
     * Thực hiện khớp lệnh tự động
     * Gọi API khớp lệnh mỗi 1 giây, áp dụng Price-Time Priority (FIFO)
     */
    async function autoMatchTick() {
        if (isMatchingInFlight) {
            return; // Đang khớp, bỏ qua lần này
        }

        isMatchingInFlight = true;
        try {
            const resp = await fetch('/api/transaction-list/match-orders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    match_type: 'all',
                    use_time_priority: true, // Sử dụng Price-Time Priority (FIFO)
                    status_mode: 'pending'
                })
            });

            // Không cần xử lý UI; chỉ đảm bảo request thành công để backend chạy matching
            // Backend sẽ tự xử lý và tạo execution records
            if (!resp.ok && resp.status >= 500) {
                // Chỉ log lỗi server (500+), không log lỗi client (401, 403, etc.)
                console.error('[AUTO MATCH WORKER] Server error:', resp.status);
            }
        } catch (error) {
            // Giữ im lặng để không gây ồn console khi không đăng nhập/không có quyền
            // Chỉ log lỗi nghiêm trọng
            if (error.message && !error.message.includes('Network')) {
                console.error('[AUTO MATCH WORKER] Unexpected error:', error);
            }
        } finally {
            isMatchingInFlight = false;
        }
    }

    // Khởi chạy interval 1 giây toàn cục
    const intervalId = setInterval(autoMatchTick, 1000);

    // Dọn dẹp khi rời trang
    window.addEventListener('beforeunload', function () {
        clearInterval(intervalId);
        window.__tl_autoMatchWorkerStarted = false;
    });
})();


