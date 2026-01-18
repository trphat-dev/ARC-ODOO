/** @odoo-module */

import { Component, useState, onMounted, onWillStart, xml } from "@odoo/owl";

/**
 * NormalOrderFormComponent
 * 
 * OWL Component for Normal Order form in Fund Buy page
 * Features:
 * - Fund search/selection matching negotiated order form style
 * - Order type box buttons with time-based locking
 * - Purchasing power display
 * - Investment amount input
 * - Lot size validation (100 CCQ)
 */
export class NormalOrderFormComponent extends Component {
    static template = xml`
        <div class="normal-order-form-container">
            <div class="normal-order-form">
                
                <!-- Fund Selection (matching negotiated order form style) -->
                <div class="mb-3">
                    <label class="form-label text-secondary fw-bold fs-xs mb-2">Chọn quỹ đầu tư</label>
                    <div class="fund-search-wrapper">
                        <div class="input-group shadow-sm rounded-pill border p-1 bg-white">
                            <span class="input-group-text bg-white border-0 ps-3 pe-2">
                                <i class="fa fa-search text-primary"></i>
                            </span>
                            <input 
                                type="text" 
                                class="form-control border-0 bg-white py-2 shadow-none"
                                placeholder="Tìm kiếm mã quỹ..."
                                t-att-value="state.searchQuery"
                                t-on-input="onSearchInput"
                                t-on-focus="() => this.state.showDropdown = true"
                            />
                        </div>
                        
                        <!-- Fund Dropdown -->
                        <div class="fund-dropdown" t-if="state.showDropdown and state.filteredFunds.length > 0">
                            <t t-foreach="state.filteredFunds" t-as="fund" t-key="fund.id">
                                <div 
                                    class="fund-dropdown-item"
                                    t-att-class="{'active': state.selectedFundId === fund.id}"
                                    t-on-click="() => this.selectFund(fund)"
                                >
                                    <span class="fund-ticker"><t t-esc="fund.ticker"/></span>
                                    <span class="fund-name"><t t-esc="fund.name"/></span>
                                </div>
                            </t>
                        </div>
                    </div>
                    
                    <!-- NAV Display (matching negotiated form style) -->
                    <div class="nav-display-card mt-2" t-if="state.selectedFundId">
                        <div class="nav-icon">
                            <i class="fa fa-chart-line"></i>
                        </div>
                        <div class="nav-info">
                            <span class="nav-label">Giá NAV hiện tại</span>
                            <div class="nav-value">
                                <strong><t t-esc="formatCurrency(state.navPrice)"/></strong>
                            </div>
                        </div>
                        <div class="market-badge-container">
                            <span t-att-class="'market-badge market-' + (state.market || 'hose').toLowerCase()">
                                <t t-esc="state.market"/>
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Order Type Box Buttons -->
                <div class="form-group order-type-section">
                    <label class="form-label text-secondary fw-bold fs-xs mb-2">Loại lệnh</label>
                    <div class="order-type-grid">
                        <t t-foreach="state.orderTypes" t-as="ot" t-key="ot.value">
                            <div 
                                t-att-class="'order-type-box' + (state.orderType === ot.value ? ' selected' : '') + (!ot.enabled ? ' locked' : '')"
                                t-on-click="() => this.selectOrderType(ot)"
                            >
                                <div class="ot-header">
                                    <span class="ot-code"><t t-esc="ot.label"/></span>
                                    <i t-if="!ot.enabled" class="fa fa-lock ot-lock-icon"></i>
                                    <i t-if="state.orderType === ot.value" class="fa fa-check-circle ot-check-icon"></i>
                                </div>
                                <div class="ot-name"><t t-esc="ot.full_label"/></div>
                            </div>
                        </t>
                    </div>
                </div>

                <!-- Purchasing Power Display (Compact) -->
                <div class="purchasing-power-compact">
                    <div class="pp-icon">
                        <i class="fa fa-wallet"></i>
                    </div>
                    <div class="pp-info">
                        <span class="pp-label">Sức mua</span>
                        <span class="pp-value">
                            <t t-esc="formatCurrency(state.purchasingPower)"/>
                            <span class="pp-units">
                                (<span class="pp-buy"><t t-esc="formatNumber(state.maxBuyUnits)"/></span>/<span class="pp-sell"><t t-esc="formatNumber(state.maxSellUnits || 0)"/></span>)
                            </span>
                        </span>
                    </div>
                    <div class="pp-refresh" t-on-click="loadPurchasingPower" title="Làm mới">
                        <i class="fa fa-refresh"></i>
                    </div>
                </div>

                <!-- Debug Toggle -->
                <div class="row g-3 mt-2">
                    <div class="col-md-12">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="debugModeToggle" t-model="state.debugMode" t-on-input="validateForm"/>
                            <label class="form-check-label text-danger fw-bold" for="debugModeToggle">
                                <i class="fas fa-bug me-1"></i>Bỏ qua kiểm tra giá (Debug)
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Price Input -->
                <div class="row g-3 mt-2">
                    <div class="col-md-12">
                        <label class="form-label text-secondary fw-bold fs-xs mb-1">Giá đặt lệnh</label>
                        
                        <!-- Market Order Label Display -->
                        <div t-if="state.isMarketOrder" class="p-2 bg-light border rounded text-center fw-bold text-primary mb-2">
                            <i class="fas fa-tag me-1 text-muted"></i><t t-esc="state.formattedPrice"/>
                        </div>
                        
                        <!-- Limit Order Price Input -->
                        <input t-else=""
                            type="text" 
                            id="normal-order-price-input"
                            t-att-class="'form-control fw-bold' + (state.priceError ? ' is-invalid' : '')"
                            t-att-value="state.formattedPrice"
                            t-on-input="onPriceInput"
                            t-on-blur="onPriceBlur"
                            t-att-disabled="!state.selectedFundId || !state.orderType"
                            placeholder="Nhập giá..."
                        />
                        <!-- Dynamic Price Feedback -->
                        <div class="form-text text-danger fs-xs fw-bold" t-if="state.priceError">
                            <i class="fas fa-exclamation-circle me-1"></i><t t-esc="state.priceError"/>
                        </div>
                        <div class="form-text text-success fs-xs" t-if="!state.priceError and state.price > 0 and state.selectedFundId and !state.isMarketOrder">
                            <i class="fas fa-check-circle me-1"></i>Giá hợp lệ
                        </div>
                    </div>
                </div>

                <!-- Quantity -->
                <div class="row g-3 mt-2">
                    <div class="col-md-12">
                        <label class="form-label text-secondary fw-bold fs-xs mb-1">Số lượng CCQ</label>
                        <input 
                            type="text" 
                            id="normal-order-quantity-input"
                            t-att-class="'form-control' + (state.lotSizeError || state.liquidityWarning ? ' is-invalid' : '')"
                            t-att-value="state.formattedQuantity"
                            t-on-input="onQuantityInput"
                            t-att-disabled="!state.selectedFundId || !state.orderType"
                            placeholder="Nhập số CCQ..."
                        />
                        <div class="invalid-feedback" t-if="state.lotSizeError">
                            <t t-esc="state.lotSizeError"/>
                        </div>
                        <div class="form-text text-warning fs-xs fw-bold" t-if="state.purchasingPowerError">
                            <i class="fas fa-exclamation-circle me-1"></i><t t-esc="state.purchasingPowerError"/>
                        </div>
                        <div class="form-text text-warning fs-xs fw-bold" t-if="!state.lotSizeError and !state.purchasingPowerError and state.liquidityWarning">
                           <i class="fas fa-exclamation-triangle me-1"></i><t t-esc="state.liquidityWarning"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    
    `;

    static props = {
        fundId: { type: Number, optional: true },
        transactionType: { type: String, optional: true },
        onOrderCreated: { type: Function, optional: true },
    };

    setup() {
        this.state = useState({
            priceError: '',
            purchasingPowerError: '',
            // Fund Search & Selection
            funds: [],
            filteredFunds: [],
            selectedFundId: null,
            searchQuery: '',
            showDropdown: false,
            
            // Market Info & Purchasing Power
            purchasingPower: 0,
            cashBalance: 0,
            availableCash: 0,
            maxBuyUnits: 0,
            market: 'HOSE',
            navPrice: 0,
            ceilingPrice: 0,
            floorPrice: 0,
            volume: 0,
            
            // Order Types with time-based locking
            orderTypes: this.getDefaultOrderTypes(),
            orderType: '',
            isPriceReadonly: false,
            isMarketOrder: false,
            
            // Form
            amount: 0,
            formattedAmount: '',
            quantity: 0,
            formattedQuantity: '',
            price: 0,
            formattedPrice: '',
            estimatedTotal: 0,
            
            // Validation
            isValid: false,
            lotSizeError: '',
            liquidityWarning: '',
            // Validation
            isValid: false,
            lotSizeError: '',
            liquidityWarning: '',
            submitting: false,
            debugMode: false,
        });
        
        this.LOT_SIZE = 1;
        
        onWillStart(async () => {
             // Init with passed fundId if any
             if (this.props.fundId) {
                this.state.selectedFundId = this.props.fundId;
             }
             await this.loadMarketInfo();
             this.updateOrderTypesAvailability();
        });
        
        onMounted(() => {
            // Refresh market info every 30s
            this.refreshInterval = setInterval(() => {
                this.loadMarketInfo(true);
            }, 30000);
            
            // Update order type availability every minute
            this.orderTypeInterval = setInterval(() => {
                this.updateOrderTypesAvailability();
            }, 60000);
            
            // Listen for submit trigger from main button
            this.submitHandler = () => this.submitNormalOrder();
            document.addEventListener('trigger-normal-submit', this.submitHandler);
            
            // Close dropdown when clicking outside
            document.addEventListener('click', this.handleOutsideClick.bind(this));
        });
    }
    
    willUnmount() {
        if (this.refreshInterval) clearInterval(this.refreshInterval);
        if (this.orderTypeInterval) clearInterval(this.orderTypeInterval);
        if (this.submitHandler) {
            document.removeEventListener('trigger-normal-submit', this.submitHandler);
        }
        document.removeEventListener('click', this.handleOutsideClick.bind(this));
    }
    
    handleOutsideClick(e) {
        if (!e.target.closest('.fund-search-wrapper')) {
            this.state.showDropdown = false;
        }
    }
    
    getDefaultOrderTypes() {
        return [
            { 
                value: 'LO', 
                label: 'LO', 
                full_label: 'Lệnh giới hạn',
                time_range: '09:00 - 14:30',
                enabled: true,
                reason: ''
            },
            { 
                value: 'ATO', 
                label: 'ATO', 
                full_label: 'Lệnh mở cửa',
                time_range: '09:00 - 09:15',
                enabled: true,
                reason: ''
            },
            { 
                value: 'ATC', 
                label: 'ATC', 
                full_label: 'Lệnh đóng cửa',
                time_range: '14:30 - 14:45',
                enabled: true,
                reason: ''
            },
            { 
                value: 'MTL', 
                label: 'MTL', 
                full_label: 'Lệnh thị trường',
                time_range: '09:15 - 14:30',
                enabled: true,
                reason: ''
            },
        ];
    }
    
    // Search & Fund Selection
    onSearchInput(e) {
        const query = e.target.value.toLowerCase();
        this.state.searchQuery = e.target.value;
        this.state.showDropdown = true;
        
        if (query.length === 0) {
            this.state.filteredFunds = this.state.funds;
        } else {
            this.state.filteredFunds = this.state.funds.filter(fund => 
                fund.ticker.toLowerCase().includes(query) ||
                fund.name.toLowerCase().includes(query)
            );
        }
    }
    
    selectFund(fund) {
        this.state.selectedFundId = fund.id;
        this.state.searchQuery = `${fund.ticker} - ${fund.name}`;
        this.state.showDropdown = false;
        this.updateFundInfo();
    }
    
    async loadMarketInfo(silent = false) {
        try {
            const response = await fetch('/api/fund/normal-order/market-info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {}
                })
            });
            
            const result = await response.json();
            
            if (result.result && result.result.success) {
                this.state.funds = result.result.funds || [];
                this.state.filteredFunds = this.state.funds;
                
                // If we have selected fund, update its info (NAV, Market)
                if (this.state.selectedFundId) {
                    this.updateFundInfo(true); // Preserve user input on refresh
                }
            }
            
            // Load purchasing power from stock_trading API
            await this.loadPurchasingPower();
            
        } catch (error) {
            console.error('[NormalOrderForm] Error loading market info:', error);
        }
    }
    
    async loadPurchasingPower() {
        try {
            const response = await fetch('/api/trading/v1/purchasing-power', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {}
                })
            });
            
            const result = await response.json();
            console.log('[NormalOrderForm] Purchasing power API response:', result);
            
            if (result.result) {
                const data = result.result.data || {};
                
                // Parse values from API response
                const purchasingPower = parseFloat(data.purchasing_power || 0);
                const cashBalance = parseFloat(data.cash_balance || 0);
                const availableCash = parseFloat(data.available_cash || 0);
                
                this.state.purchasingPower = purchasingPower;
                this.state.cashBalance = cashBalance;
                this.state.availableCash = availableCash;
                
                this.state.availableCash = availableCash;
                
                // Update max buy units if NAV is available
                // Tính số lượng tối đa có thể mua (không làm tròn theo lô để hiển thị chính xác khả năng mua)
                if (this.state.navPrice > 0) {
                     let calcPrice = this.state.price > 0 ? this.state.price : this.state.navPrice;
                     
                     // If Market Order use Ceiling Price
                     if (this.state.isMarketOrder) {
                         // STRICT: Use Ceiling Price only. No mock data.
                         calcPrice = this.state.ceilingPrice; 
                     }
                     
                     if (calcPrice > 0) {
                        this.state.maxBuyUnits = Math.floor(purchasingPower / calcPrice);
                     } else {
                        this.state.maxBuyUnits = 0;
                     }
                }
                
                console.log('[NormalOrderForm] Purchasing power loaded:', { purchasingPower, cashBalance, availableCash });
            }
        } catch (error) {
            console.error('[NormalOrderForm] Error loading purchasing power:', error);
        }
    }
    
    onFundChange(e) {
        const fundId = parseInt(e.target.value);
        this.state.selectedFundId = fundId || null;
        this.updateFundInfo();
        
        // Reset calculation and selection
        this.state.orderType = ''; 
        // this.calculateQuantity(); // REMOVED as Amount input is gone
        this.validateForm();
        
        // Load order types for this fund's market
        if (fundId) {
            this.loadOrderTypes();
        } else {
             this.state.availableOrderTypes = [];
        }
    }
    
    updateFundInfo(preserveInput = false) {
        if (!this.state.selectedFundId) {
            this.state.market = 'HOSE';
            this.state.navPrice = 0;
            this.state.ceilingPrice = 0;
            this.state.floorPrice = 0;
            this.state.volume = 0;
            this.state.maxBuyUnits = 0;
            return;
        }
        
        const fund = this.state.funds.find(f => f.id === this.state.selectedFundId);
        if (fund) {
            this.state.market = fund.market || 'HOSE';
            this.state.navPrice = fund.current_nav || 0;
            // Use high_price as ceiling, low_price as floor (per API assumption)
            // UPDATED: Use explicit fields from API or fallback
            this.state.ceilingPrice = fund.ceiling_price || fund.high_price || 0;
            this.state.floorPrice = fund.floor_price || fund.low_price || 0;
            this.state.volume = fund.volume || 0;
            
            // Default price to NAV/Ref if Price Input is empty or new fund selected
            if (!this.state.isMarketOrder && !preserveInput) {
                 this.state.price = this.state.navPrice;
                 this.state.formattedPrice = this.state.navPrice.toLocaleString('vi-VN');
            }

            
            this.checkOrderTypeConstraints();
            
            // Recalculate max buy units
            if (this.state.navPrice > 0) {
                 this.state.maxBuyUnits = Math.floor(this.state.purchasingPower / this.state.navPrice);
            } else {
                 this.state.maxBuyUnits = 0;
            }
        }
    }
    
    checkOrderTypeConstraints() {
        if (this.state.orderType) {
            this.onOrderTypeChange({ target: { value: this.state.orderType } });
        }
    }
    
    checkLotSize() {
        this.state.lotSizeError = '';
        this.state.liquidityWarning = '';
        
        if (this.state.quantity > 0) {
            // Check Lot Size
            if (this.state.quantity % this.LOT_SIZE !== 0) {
                this.state.lotSizeError = `Số lượng phải theo lô ${this.LOT_SIZE}`;
            }
            
            // Check Liquidity Warning (ATC with > 10% Avg Volume)
            // Or general check. User said "ATC with large quantity".
            // Let's apply for all or just ATC? "Cảnh báo ... nếu user đặt lệnh ATC với số lượng quá lớn"
            // I'll apply for all Market Orders or generally if large.
            if (this.state.volume > 0 && this.state.quantity > this.state.volume * 0.1) {
                this.state.liquidityWarning = `Khối lượng đặt lớn hơn 10% thanh khoản trung bình (${this.state.volume.toLocaleString()})`;
            }
        }
    }

    async loadOrderTypes() {
        try {
            const fundId = this.state.selectedFundId;
            const response = await fetch('/api/fund/normal-order/order-types', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { fund_id: fundId ? parseInt(fundId) : null }
                })
            });
            
            const result = await response.json();
            
            if (result.result && result.result.success) {
                const backendTypes = result.result.order_types || [];
                const serverTime = result.result.server_time;
                console.log(`[NormalOrderForm] Server Time: ${serverTime}, Types:`, backendTypes);
                
                // Strict mapping: Backend returns 'value' key, NOT 'code'
                this.state.orderTypes = this.state.orderTypes.map(uiType => {
                     const backendType = backendTypes.find(bt => bt.value === uiType.value);
                     if (backendType) {
                         return {
                             ...uiType,
                             enabled: backendType.enabled,
                             reason: backendType.enabled ? '' : backendType.reason
                         };
                     }
                     // Not found in backend => Disable strictly
                     return { ...uiType, enabled: false, reason: 'Không hỗ trợ' };
                });
                
                // Re-validate current selection
                if (this.state.orderType) {
                    const current = this.state.orderTypes.find(ot => ot.value === this.state.orderType);
                    if (current && !current.enabled) {
                        this.state.orderType = '';
                        // Try to auto-select first enabled
                        const firstEnabled = this.state.orderTypes.find(ot => ot.enabled);
                        if (firstEnabled) {
                            this.selectOrderType(firstEnabled);
                        } else {
                            // If all disabled, just clear selection
                            this.onOrderTypeChange({ target: { value: '' } });
                        }
                    }
                } else {
                    // Auto select first enabled if none selected
                    const firstEnabled = this.state.orderTypes.find(ot => ot.enabled);
                    if (firstEnabled) {
                        this.selectOrderType(firstEnabled);
                    }
                }
            } else {
                console.error('[NormalOrderForm] API Failed:', result.error || result.result?.message);
                // Fail-safe: Lock all on API error
                this.state.orderTypes = this.state.orderTypes.map(t => ({ ...t, enabled: false, reason: 'Lỗi tải dữ liệu' }));
            }
        } catch (error) {
            console.error('[NormalOrderForm] Network Error:', error);
            // Fail-safe: Lock all on Network error
            this.state.orderTypes = this.state.orderTypes.map(t => ({ ...t, enabled: false, reason: 'Lỗi kết nối mạng' }));
        }
    }
    
    updateOrderTypesAvailability() {
        this.loadOrderTypes();
    }
    
    selectOrderType(ot) {
        if (ot.enabled) {
            this.onOrderTypeChange({ target: { value: ot.value } });
        }
    }

    onOrderTypeChange(e) {
        const type = e.target.value;
        this.state.orderType = type;
        
        const isMarket = ['ATO', 'ATC', 'MP', 'MTL', 'MOK', 'MAK'].includes(type);
        this.state.isMarketOrder = isMarket;
        this.state.isPriceReadonly = isMarket;
        
        if (isMarket) {
            this.state.formattedPrice = type; // Display "ATO", "ATC"...
            this.state.price = 0; // Price 0 means use Market logic
        } else {
            // Restore price to NAV or last input if LO
             // ONLY reset to NAV if current price is 0 (e.g. coming from Market Order)
             if (this.state.price === 0 && this.state.navPrice > 0) {
                 this.state.price = this.state.navPrice;
                 this.state.formattedPrice = this.state.navPrice.toLocaleString('vi-VN');
             } else if (this.state.price > 0) {
                 // Keep existing custom price
                 this.state.formattedPrice = this.state.price.toLocaleString('vi-VN');
             } else {
                 this.state.formattedPrice = '';
                 this.state.price = 0;
             }
        }
        
        // Recalculate max buy units based on new constraint (Ceiling vs Price)
        // We trigger validation which triggers logic check
        this.validateForm();
        // Also re-calc amounts if we have quantity
        if (this.state.quantity > 0) {
            this.calculateTotalFromPriceQuantity();
        }
    }

    onPriceInput(e) {
        // Only for LO
        if (this.state.isPriceReadonly) return;
        
        const rawValue = e.target.value.replace(/[^0-9]/g, '');
        const price = parseInt(rawValue) || 0;
        
        this.state.price = price;
        this.state.formattedPrice = price > 0 ? price.toLocaleString('vi-VN') : '';
        
        this.calculateTotalFromPriceQuantity();
        this.validateForm(); // This updates isValid and priceError
        // updateRightSidebar is called inside validateForm, which disables the button
    }

    onPriceBlur(e) {
        if (this.state.isPriceReadonly) return;
        const price = this.mround(this.state.price, 50);
        this.state.price = price;
        this.state.formattedPrice = price > 0 ? price.toLocaleString('vi-VN') : '';
        this.calculateTotalFromPriceQuantity();
        this.validateForm();
    }

    mround(value, step = 50) {
        const num = Number(value || 0);
        if (!Number.isFinite(num) || step <= 0) return num;
        const remainder = num % step;
        const threshold = step / 2;
        if (remainder < threshold) {
            return Math.floor(num / step) * step;
        } else {
            return Math.ceil(num / step) * step;
        }
    }
    
    // ... Removed onAmountInput logic ...
    
    onQuantityInput(e) {
        const rawValue = e.target.value.replace(/[^0-9]/g, '');
        const quantity = parseInt(rawValue) || 0;
        
        this.state.quantity = quantity;
        this.state.formattedQuantity = quantity > 0 ? quantity.toLocaleString('vi-VN') : '';
        
        this.calculateTotalFromPriceQuantity();
        this.validateForm();
    }
    
    calculateTotalFromPriceQuantity() {
        // Use Input Price for LO, or Estimate Price (NAV) for Market - Display Purpose
        let calcPrice = this.state.price;
        if (this.state.isMarketOrder) {
             calcPrice = this.state.navPrice;
        }
        
        if (calcPrice > 0 && this.state.quantity > 0) {
            this.state.amount = calcPrice * this.state.quantity;
            this.state.formattedAmount = this.state.amount.toLocaleString('vi-VN');
            this.state.estimatedTotal = this.state.amount;
        } else {
            this.state.amount = 0;
            this.state.formattedAmount = '';
            this.state.estimatedTotal = 0;
        }
        // Removed checkLotSize()
    }
    
    // Removed calculateQuantityFromAmount
    
    calculateAmountFromQuantity() {
        this.calculateTotalFromPriceQuantity();
    }
    
    // Removed checkLotSize() implementation

    updateRightSidebar() {
        const summaryFundName = document.getElementById('summary-fund-name');
        const summaryUnits = document.getElementById('summary-units');
        const summaryInvestAmount = document.getElementById('summary-investment-amount'); // If exists
        const summaryAmount = document.getElementById('summary-amount');
        const summaryTotal = document.getElementById('summary-total');
        const summaryFee = document.getElementById('summary-fee');

        if (summaryFundName && this.state.selectedFundId) {
            const fund = this.state.funds.find(f => f.id === this.state.selectedFundId);
            if (fund) summaryFundName.textContent = fund.ticker || fund.name;
        }

        if (summaryUnits) summaryUnits.textContent = this.state.quantity > 0 ? this.state.quantity.toLocaleString('vi-VN') : '0';
        
        // For Normal Order, Investment Amount ~= Total Amount (fee included or excluded depending on logic, keeping simple for now)
        if (summaryInvestAmount) summaryInvestAmount.textContent = this.state.amount > 0 ? this.state.amount.toLocaleString('vi-VN') + 'đ' : '0đ';
        if (summaryAmount) summaryAmount.textContent = this.state.amount > 0 ? this.state.amount.toLocaleString('vi-VN') + 'đ' : '0đ';
        
        // Total Estimated
        if (summaryTotal) summaryTotal.textContent = this.state.estimatedTotal > 0 ? this.state.estimatedTotal.toLocaleString('vi-VN') + 'đ' : '0đ';
        
        // Fee (Estimate or Real)
        // For now, set to 0 or calculate if needed. Fund Buy JS calculates it.
        // Fee (Estimate or Real)
        // For now, set to 0 or calculate if needed. Fund Buy JS calculates it.
        if (summaryFee) summaryFee.textContent = '0đ'; 
        
        // Update Submit Button State (Shared Button)
        const paymentBtn = document.getElementById('payment-btn');
        if (paymentBtn) {
            paymentBtn.disabled = !this.state.isValid;
            paymentBtn.style.opacity = this.state.isValid ? '1' : '0.5';
            
            // Optional: Update text to indicate Normal Order action if needed
            // But 'Tiếp tục' is fine.
        }
    }

    validateForm() {
        const isTxBuy = this.props.transactionType !== 'sell';
        
        // Price Validation (Limit Order)
        this.state.priceError = '';
        if (!this.state.debugMode && !this.state.isMarketOrder && this.state.selectedFundId && this.state.price > 0) {
            // Check Ceiling
            if (this.state.ceilingPrice > 0 && this.state.price > this.state.ceilingPrice) {
                 this.state.priceError = `Giá đặt phải nhỏ hơn hoặc bằng giá trần (${this.formatNumber(this.state.ceilingPrice)})`;
            }
            // Check Floor
            else if (this.state.floorPrice > 0 && this.state.price < this.state.floorPrice) {
                 this.state.priceError = `Giá đặt phải lớn hơn hoặc bằng giá sàn (${this.formatNumber(this.state.floorPrice)})`;
            }
        }
        
        // Purchasing Power Error (Warning Only - Allow Proceed)
        this.state.purchasingPowerError = '';
        /* 
         * REMOVED per user request: Do not show warning text for insufficient PP.
         * Logic still allows proceed.
        if (isTxBuy && this.state.selectedFundId && this.state.quantity > 0) {
            if (this.state.quantity > this.state.maxBuyUnits) {
                this.state.purchasingPowerError = `Không đủ sức mua (Tối đa ${this.formatNumber(this.state.maxBuyUnits)}) - Sẽ chuyển sang thanh toán`;
            }
        }
        */

        this.state.isValid = (
            this.state.selectedFundId &&
            this.state.quantity > 0 &&
            this.state.orderType &&
            // !this.state.purchasingPowerError &&  <-- REMOVED BLOCK
            !this.state.priceError
        );
        
        // Update Sidebar whenever validation runs (state changed)
        this.updateRightSidebar();
    }
    
    async submitNormalOrder() {
        if (!this.state.isValid || this.state.submitting) return;
        
        this.state.submitting = true;
        
        // 1. Show Loading
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: "Đang kiểm tra thông tin...",
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });
        }
        
        try {
            // 2. Refresh Market Info (Purchasing Power)
            await this.loadMarketInfo(true);
            
            // 3. Calculate Required Amount
            let requiredAmount = this.state.amount;
            if (this.state.isMarketOrder) {
                // For Market Order, check against Ceiling Price or NAV if Ceiling 0
                const checkPrice = this.state.ceilingPrice > 0 ? this.state.ceilingPrice : this.state.navPrice;
                requiredAmount = checkPrice * this.state.quantity;
            }
            
            // 4. Check Purchasing Power
            const pp = this.state.purchasingPower;
            let ppStatus = 'sufficient';
            if (this.state.quantity > this.state.maxBuyUnits) {
                ppStatus = 'insufficient';
            }
            
            // 5. ALWAYS Save Session Data BEFORE any redirect or further action
            const fund = this.state.funds.find(f => f.id === this.state.selectedFundId);
            
            sessionStorage.setItem('selectedFundId', this.state.selectedFundId);
            sessionStorage.setItem('selectedFundName', fund ? (fund.ticker || fund.name) : '');
            sessionStorage.setItem('selectedUnits', this.state.quantity);
            sessionStorage.setItem('selectedAmount', this.state.amount);
            sessionStorage.setItem('selectedTotalAmount', this.state.estimatedTotal);
            
            sessionStorage.removeItem('selected_term_months');
            sessionStorage.removeItem('selected_interest_rate');
            
            sessionStorage.setItem('selected_order_type', this.state.orderType);
            sessionStorage.setItem('selected_price', this.state.price);
            sessionStorage.setItem('is_market_order', this.state.isMarketOrder);
            sessionStorage.setItem('normal_order_pp_status', ppStatus);
            
            console.log('[NormalOrderForm] Saved session data:', {
                fundId: this.state.selectedFundId,
                orderType: this.state.orderType,
                quantity: this.state.quantity,
                ppStatus
            });
            
            // 6. Branch Logic based on Purchasing Power
            if (ppStatus === 'insufficient') {
                // Insufficient -> Show notification and redirect to payment page
                if (typeof Swal !== 'undefined') {
                    Swal.close();
                    await Swal.fire({
                       title: "Sức mua không đủ",
                       text: "Hệ thống đang chuyển sang trang thanh toán...",
                       icon: "info",
                       timer: 1500,
                       showConfirmButton: false,
                       allowOutsideClick: false
                    });
                }
                window.location.href = '/fund_confirm';
            } else {
                // Sufficient -> Trigger OTP verification
                if (typeof Swal !== 'undefined') Swal.close();
                await this.triggerSmartOTP();
            }
            
        } catch (error) {
            console.error('Error during submit check:', error);
            this.state.submitting = false;
            if (typeof Swal !== 'undefined') {
                Swal.fire("Lỗi hệ thống", "Vui lòng thử lại sau.", "error");
            }
        }
    }
    
    async triggerSmartOTP() {
        try {
            // 1. Get OTP Config
            let otpType = 'smart';
            try {
                const configResponse = await fetch('/api/otp/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {} })
                });
                const configPayload = await configResponse.json().catch(() => ({}));
                const configData = (configPayload.result || configPayload).result || configPayload.result || configPayload;
                if (configData?.otp_type) otpType = configData.otp_type;
                
                // Bypass OTP if token valid
                if (configData?.has_valid_write_token) {
                     await this.createNormalOrder(); 
                     return;
                }
            } catch (e) { console.warn("OTP Config Error", e); }
            
            // 2. Show OTP Modal
            if (window.FundManagementSmartOTP && typeof window.FundManagementSmartOTP.open === 'function') {
                 window.FundManagementSmartOTP.open({
                    otpType: otpType,
                    onConfirm: async (otp, debugMode) => {
                        try {
                            const response = await fetch('/api/otp/verify', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { otp, debug: debugMode || false } })
                            });
                            const data = await response.json();
                            const result = data.result || data;
                            
                            if (!result || result.success !== true) {
                                throw new Error(result?.message || 'Mã OTP không hợp lệ');
                            }
                            
                            // OTP Success -> Create Order
                            await this.createNormalOrder();
                            
                        } catch (err) {
                            throw err; // Passed to OTP Modal to show error
                        }
                    }
                 });
            } else {
                 // Fallback if no OTP component
                 console.warn('SmartOTP Component not found. Proceeding without OTP.');
                 await this.createNormalOrder();
            }

        } catch (err) {
            console.error("OTP Error:", err);
            this.state.submitting = false; // Reset submitting state
            if (typeof Swal !== 'undefined') Swal.fire("Lỗi OTP", "Không thể kích hoạt xác thực.", "error");
        }
    }
    
    async createNormalOrder() {
        try {
            if (typeof Swal !== 'undefined') {
                 Swal.fire({
                    title: "Đang tạo lệnh...",
                    allowOutsideClick: false,
                    didOpen: () => Swal.showLoading()
                 });
            }
            
            const rpcParams = {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    fund_id: parseInt(this.state.selectedFundId),
                    transaction_type: this.props.transactionType || 'buy',
                    units: parseInt(this.state.quantity),
                    price: parseFloat(this.state.price) || 0,

                    order_type_detail: this.state.orderType,
                    debug: this.state.debugMode || false
                }
            };

            const res = await fetch('/api/fund/normal-order/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(rpcParams)
            });

            const resultJson = await res.json();
            
            if (resultJson.result && resultJson.result.success) {
                 const result = resultJson.result;
                 
                 // Save Result Info for Result Page
                 const fund = this.state.funds.find(f => f.id === this.state.selectedFundId);
                 
                 // Save with BOTH key formats for compatibility
                 sessionStorage.setItem('selectedFundId', this.state.selectedFundId);
                 sessionStorage.setItem('selectedFundName', fund ? (fund.ticker || fund.name) : '');
                 sessionStorage.setItem('selectedUnits', this.state.quantity);
                 sessionStorage.setItem('selectedAmount', this.state.amount);
                 sessionStorage.setItem('selectedTotalAmount', this.state.estimatedTotal);
                 sessionStorage.setItem('selected_order_type', this.state.orderType);
                 sessionStorage.setItem('selected_price', this.state.price);
                 
                 sessionStorage.setItem('result_fund_name', fund ? (fund.ticker || fund.name) : '');
                 sessionStorage.setItem('result_order_date', new Date().toLocaleString('vi-VN'));
                 sessionStorage.setItem('result_amount', this.state.amount);
                 sessionStorage.setItem('result_total_amount', this.state.estimatedTotal);
                 sessionStorage.setItem('result_units', this.state.quantity);
                 
                 // CRITICAL: Save Transaction ID for Result Page
                 if (result.order_id) {
                     sessionStorage.setItem('transaction_id', String(result.order_id));
                     console.log('[createNormalOrder] Saved transaction_id:', result.order_id);
                 } else {
                     console.warn('[createNormalOrder] No order_id returned from backend!');
                 }
                 
                 // Save NAV Data if present
                 if (result.nav_data) {
                    sessionStorage.setItem('nav_data', JSON.stringify(result.nav_data));
                 }
                 
                 // Show Success Message BEFORE redirect
                 if (typeof Swal !== 'undefined') {
                     Swal.close();
                     await Swal.fire({
                         title: "Đặt lệnh thành công!",
                         text: "Lệnh mua CCQ đã được ghi nhận.",
                         icon: "success",
                         confirmButtonText: "Xem kết quả",
                         confirmButtonColor: "#28a745",
                         timer: 2000,
                         timerProgressBar: true
                     });
                 }
                 
                 window.location.href = '/fund_result';
            } else {
                 throw new Error(resultJson.result?.message || resultJson.error?.data?.message || 'Không thể tạo lệnh');
            }
            
        } catch (err) {
            console.error("Create Order Error:", err);
            this.state.submitting = false;
            
            // Check for Insufficient Funds (Edge Case if PP check passed but backend failed)
            const msg = err.message || '';
            if (msg.toLowerCase().includes('sức mua') || msg.toLowerCase().includes('không đủ tiền')) {
                 if (typeof Swal !== 'undefined') Swal.close();
                 // Redirect to Confirm Page to pay
                 sessionStorage.setItem('normal_order_pp_status', 'insufficient');
                 window.location.href = '/fund_confirm';
            } else {
                 if (typeof Swal !== 'undefined') Swal.fire("Lỗi tạo lệnh", msg, "error");
            }
        }
    }
        

    
    formatCurrency(value) {
        return Number(value || 0).toLocaleString('vi-VN') + ' VNĐ';
    }
    
    formatNumber(value) {
        return Number(value || 0).toLocaleString('vi-VN');
    }
    
    showNotification(message, type = 'info') {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: type === 'error' ? 'error' : type === 'success' ? 'success' : 'info',
                title: message,
                timer: 3000,
                showConfirmButton: false,
                position: 'top-end',
                toast: true
            });
        } else {
             // Fallback
             console.log(type.toUpperCase() + ": " + message);
        }
    }
}

export default NormalOrderFormComponent;
