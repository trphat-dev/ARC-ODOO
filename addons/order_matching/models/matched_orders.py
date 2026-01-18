from odoo import models, fields, api

class MatchedOrders(models.Model):
    _name = 'transaction.matched.orders'
    _description = 'Matched Buy/Sell Orders'
    _order = 'match_date desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', readonly=True)
    match_date = fields.Datetime(string='Match Date', default=fields.Datetime.now)
    buy_order_id = fields.Many2one('portfolio.transaction', string='Buy Order', domain=[('transaction_type', '=', 'buy')])
    sell_order_id = fields.Many2one('portfolio.transaction', string='Sell Order', domain=[('transaction_type', '=', 'sell')])
    matched_quantity = fields.Float(string='Matched Quantity')
    matched_price = fields.Float(string='Matched Price')
    total_value = fields.Float(string='Total Value', compute='_compute_total_value', store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True, tracking=True)
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True, default=lambda self: self.env.user)
    match_type = fields.Selection([
        ('investor_investor', 'Investor - Investor'),
        ('investor_market_maker', 'Investor - Market Maker'),
        ('market_maker_market_maker', 'Market Maker - Market Maker')
    ], string='Match Type', compute='_compute_match_type', store=True)
    buy_user_type = fields.Selection([
        ('investor', 'Investor'),
        ('market_maker', 'Market Maker')
    ], string='Buy User Type', compute='_compute_user_types', store=True)
    sell_user_type = fields.Selection([
        ('investor', 'Investor'),
        ('market_maker', 'Market Maker')
    ], string='Sell User Type', compute='_compute_user_types', store=True)
    
    # Add source fields
    buy_source = fields.Selection(related='buy_order_id.source', string='Buy Source', store=True)
    sell_source = fields.Selection(related='sell_order_id.source', string='Sell Source', store=True)

    # Add explicit user fields for clarity in UI/report
    buy_user_id = fields.Many2one(related='buy_order_id.user_id', string='Buy User', store=True)
    sell_user_id = fields.Many2one(related='sell_order_id.user_id', string='Sell User', store=True)

    # Fund info
    fund_id = fields.Many2one(related='buy_order_id.fund_id', string='Fund', store=True)

    # Term and interest rate (per side)
    buy_term_months = fields.Integer(related='buy_order_id.term_months', string='Buy Term (months)', store=True)
    sell_term_months = fields.Integer(related='sell_order_id.term_months', string='Sell Term (months)', store=True)
    buy_interest_rate = fields.Float(related='buy_order_id.interest_rate', string='Buy Interest Rate (%)', store=True)
    sell_interest_rate = fields.Float(related='sell_order_id.interest_rate', string='Sell Interest Rate (%)', store=True)

    # In/Out times per side
    buy_in_time = fields.Datetime(string='Buy In Time', compute='_compute_in_out_times', store=True)
    sell_in_time = fields.Datetime(string='Sell In Time', compute='_compute_in_out_times', store=True)
    # Use stable field available in base transaction model to avoid dependency issues
    buy_out_time = fields.Datetime(related='buy_order_id.date_end', string='Buy Out Time', store=True)
    sell_out_time = fields.Datetime(related='sell_order_id.date_end', string='Sell Out Time', store=True)

    # Additional quantitative fields for UI reporting
    buy_units = fields.Float(related='buy_order_id.units', string='Buy Units', store=True)
    sell_units = fields.Float(related='sell_order_id.units', string='Sell Units', store=True)
    buy_price = fields.Float(related='buy_order_id.current_nav', string='Buy Price', store=True)
    sell_price = fields.Float(related='sell_order_id.current_nav', string='Sell Price', store=True)
    # Remaining units - computed từ units - matched_units để đảm bảo chính xác (theo chuẩn Stock Exchange)
    buy_remaining_units = fields.Float(
        string='Buy Remaining Units',
        compute='_compute_remaining_units',
        store=True,
        help='Số lượng còn lại của lệnh mua (tính từ units - matched_units)'
    )
    sell_remaining_units = fields.Float(
        string='Sell Remaining Units',
        compute='_compute_remaining_units',
        store=True,
        help='Số lượng còn lại của lệnh bán (tính từ units - matched_units)'
    )
    
    # Related fields để hiển thị executions trong form view
    buy_executions = fields.One2many(
        related='buy_order_id.matched_order_ids',
        string='Executions của lệnh mua',
        readonly=True
    )
    sell_executions = fields.One2many(
        related='sell_order_id.matched_sell_order_ids',
        string='Executions của lệnh bán',
        readonly=True
    )
    
    # Field để đánh dấu đã gửi lên sàn
    sent_to_exchange = fields.Boolean(string="Đã gửi lên sàn", default=False, tracking=True, help="Cặp lệnh đã được gửi lên sàn thông qua trading.order")
    sent_to_exchange_at = fields.Datetime(string="Thời gian gửi lên sàn", help="Thời điểm cặp lệnh được gửi lên sàn")

    @api.depends('buy_order_id.user_id', 'sell_order_id.user_id', 'buy_source', 'sell_source')
    def _compute_user_types(self):
        for record in self:
            # Default to investor
            record.buy_user_type = 'investor'
            record.sell_user_type = 'investor'

            def is_market_maker(user, source):
                try:
                    # Internal User in Odoo
                    if user and user.has_group('base.group_user'):
                        return True
                except Exception:
                    pass
                # Fallback theo nguồn: chỉ 'sale' coi là MM
                return (source == 'sale')

            # Determine buy side
            if record.buy_order_id:
                record.buy_user_type = 'market_maker' if is_market_maker(record.buy_order_id.user_id, record.buy_source) else 'investor'

            # Determine sell side
            if record.sell_order_id:
                record.sell_user_type = 'market_maker' if is_market_maker(record.sell_order_id.user_id, record.sell_source) else 'investor'

    @api.depends('buy_user_type', 'sell_user_type')
    def _compute_match_type(self):
        for record in self:
            if record.buy_user_type == 'investor' and record.sell_user_type == 'investor':
                record.match_type = 'investor_investor'
            elif record.buy_user_type == 'market_maker' and record.sell_user_type == 'market_maker':
                record.match_type = 'market_maker_market_maker'
            else:
                record.match_type = 'investor_market_maker'

    @api.depends('matched_quantity', 'matched_price')
    def _compute_total_value(self):
        for record in self:
            record.total_value = record.matched_quantity * record.matched_price

    @api.depends('buy_order_id.units', 'buy_order_id.matched_units', 'sell_order_id.units', 'sell_order_id.matched_units')
    def _compute_remaining_units(self):
        """
        Tính toán remaining_units chính xác từ units - matched_units (theo chuẩn Stock Exchange)
        """
        for record in self:
            # Tính toán buy_remaining_units
            if record.buy_order_id:
                buy_units = float(record.buy_order_id.units or 0)
                buy_matched = float(record.buy_order_id.matched_units or 0)
                record.buy_remaining_units = max(0.0, buy_units - buy_matched)
            else:
                record.buy_remaining_units = 0.0
            
            # Tính toán sell_remaining_units
            if record.sell_order_id:
                sell_units = float(record.sell_order_id.units or 0)
                sell_matched = float(record.sell_order_id.matched_units or 0)
                record.sell_remaining_units = max(0.0, sell_units - sell_matched)
            else:
                record.sell_remaining_units = 0.0

    @api.depends('buy_order_id.create_date', 'sell_order_id.create_date')
    def _compute_in_out_times(self):
        for record in self:
            # Prefer explicit created_at if exists, fallback to create_date
            try:
                buy_created_at = getattr(record.buy_order_id, 'created_at', False)
            except Exception:
                buy_created_at = False
            try:
                sell_created_at = getattr(record.sell_order_id, 'created_at', False)
            except Exception:
                sell_created_at = False

            record.buy_in_time = buy_created_at or record.buy_order_id.create_date or False
            record.sell_in_time = sell_created_at or record.sell_order_id.create_date or False
            
    def update_transaction_statuses(self):
        """Deprecated: Transaction status updates are now handled by OrderMatchingEngine"""
        pass

    @api.model_create_multi
    def create(self, vals_list):
        import logging
        _logger = logging.getLogger(__name__)
        
        # Generate names for records that don't have them
        # Format: HDC-DDMMYY/STT (STT = số thứ tự tự động tăng)
        for vals in vals_list:
            if not vals.get('name'):
                # Generate reference number using sequence
                try:
                    sequence = self.env['ir.sequence'].next_by_code('transaction.matched.orders')
                    if sequence:
                        vals['name'] = sequence
                    else:
                        # Fallback if sequence not found - Format: HDC-DDMMYY/STT
                        from datetime import date
                        today = date.today()
                        # Lấy số thứ tự từ sequence hoặc tự đếm
                        try:
                            seq_obj = self.env['ir.sequence'].search([('code', '=', 'transaction.matched.orders')], limit=1)
                            if seq_obj:
                                stt = seq_obj.number_next
                            else:
                                # Đếm số matched orders trong ngày
                                today_start = fields.Datetime.to_datetime(today.strftime('%Y-%m-%d 00:00:00'))
                                today_end = fields.Datetime.to_datetime(today.strftime('%Y-%m-%d 23:59:59'))
                                count = self.env['transaction.matched.orders'].search_count([
                                    ('create_date', '>=', today_start),
                                    ('create_date', '<=', today_end)
                                ])
                                stt = count + 1
                        except Exception:
                            stt = 1
                        vals['name'] = "HDC-%s/%04d" % (today.strftime('%d%m%y'), stt)
                except Exception as e:
                    _logger.warning("Could not generate sequence for matched order: %s", e)
                    # Fallback với format HDC-DDMMYY/STT
                    from datetime import date
                    today = date.today()
                    try:
                        # Đếm số matched orders trong ngày
                        today_start = fields.Datetime.to_datetime(today.strftime('%Y-%m-%d 00:00:00'))
                        today_end = fields.Datetime.to_datetime(today.strftime('%Y-%m-%d 23:59:59'))
                        count = self.env['transaction.matched.orders'].search_count([
                            ('create_date', '>=', today_start),
                            ('create_date', '<=', today_end)
                        ])
                        stt = count + 1
                    except Exception:
                        stt = 1
                    vals['name'] = "HDC-%s/%04d" % (today.strftime('%d%m%y'), stt)

        try:
            # Create the records
            records = super().create(vals_list)
            
            # Cập nhật name để hiển thị rõ ràng khi có lệnh nhỏ (nếu chưa có indicator)
            for record in records:
                # Kiểm tra xem name đã có indicator chưa (tránh duplicate)
                if record.name and ('[B[S]' in record.name or '[S[S]' in record.name):
                    continue  # Đã có indicator rồi, không cần thêm
                
                # Kiểm tra và thêm indicator cho lệnh nhỏ
                buy_is_split = False
                sell_is_split = False
                if record.buy_order_id:
                    buy_is_split = getattr(record.buy_order_id, 'is_split_order', False)
                if record.sell_order_id:
                    sell_is_split = getattr(record.sell_order_id, 'is_split_order', False)
                
                indicators = []
                if buy_is_split:
                    indicators.append("B[S]")  # Buy Split
                if sell_is_split:
                    indicators.append("S[S]")  # Sell Split
                
                if indicators:
                    # Thêm indicator vào name
                    new_name = "%s [%s]" % (record.name, '/'.join(indicators))
                    record.write({'name': new_name})
            
            _logger.info("Created %s matched orders", len(records))

            # Note: We don't update transaction units here anymore
            # This is now handled in the action_match_orders method
            # to avoid double updates and conflicts

            # Trigger recompute stats cho engines
            self._trigger_engine_stats_recompute()
            return records

        except Exception as e:
            _logger.error("Error creating matched order: %s", str(e))
            import traceback
            traceback.print_exc()
            raise

    def write(self, vals):
        result = super(MatchedOrders, self).write(vals)
        # Trigger recompute stats cho engines
        self._trigger_engine_stats_recompute()
        return result

    def unlink(self):
        result = super(MatchedOrders, self).unlink()
        # Trigger recompute stats cho engines
        self._trigger_engine_stats_recompute()
        return result

    @api.model
    def _trigger_engine_stats_recompute(self):
        """Trigger recompute stats cho engines khi có thay đổi matched orders"""
        try:
            engine_model = self.env['transaction.partial.matching.engine']
            if hasattr(engine_model, '_trigger_recompute_stats'):
                engine_model._trigger_recompute_stats()
        except Exception:
            # Ignore errors để không ảnh hưởng đến chức năng chính
            pass

    def get_remaining_orders_summary(self):
        """Lấy tổng kết các lệnh còn lại - simplified version"""
        try:
            pending_buys = self.env['portfolio.transaction'].search([
                ('transaction_type', '=', 'buy'),
                ('status', '=', 'completed'),
                ('ccq_remaining_to_match', '>', 0)
            ])
            
            pending_sells = self.env['portfolio.transaction'].search([
                ('transaction_type', '=', 'sell'),
                ('status', '=', 'completed'),
                ('ccq_remaining_to_match', '>', 0)
            ])
            
            return {
                'success': True,
                'buy_orders_count': len(pending_buys),
                'sell_orders_count': len(pending_sells),
                'total_buy_remaining': sum(b.ccq_remaining_to_match for b in pending_buys),
                'total_sell_remaining': sum(s.ccq_remaining_to_match for s in pending_sells)
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}

