from odoo import models, fields, api


class DailyIndex(models.Model):
    """Daily Index Data from SSI API"""
    _name = 'ssi.daily.index'
    _description = 'Daily Index Data'
    _order = 'date desc, index_code'

    index_code = fields.Char('Index Code', required=True, index=True)
    exchange = fields.Char('Exchange', index=True)
    date = fields.Date('Date', required=True, index=True)
    
    # Core values (the new schema)
    index_value = fields.Float('Index Value', digits=(16, 2))
    change = fields.Float('Change', digits=(16, 2))
    ratio_change = fields.Float('Ratio Change', digits=(16, 6))

    # Trades/volume/value
    total_trade = fields.Integer('Total Trade')
    total_match_vol = fields.Float('Total Match Vol', digits=(16, 0))
    total_match_val = fields.Float('Total Match Val', digits=(16, 0))
    total_deal_vol = fields.Float('Total Deal Vol', digits=(16, 0))
    total_deal_val = fields.Float('Total Deal Val', digits=(16, 0))
    total_vol = fields.Float('Total Vol', digits=(16, 0))
    total_val = fields.Float('Total Val', digits=(16, 0))

    # Market breadth
    advances = fields.Integer('Advances')
    no_changes = fields.Integer('No Changes')
    declines = fields.Integer('Declines')
    ceilings = fields.Integer('Ceilings')
    floors = fields.Integer('Floors')

    # Others
    index_name = fields.Char('Index Name')
    trading_session = fields.Char('Trading Session')
    time = fields.Char('Time')

    # Compatibility fields for existing views/graphs
    close_value = fields.Float('Close Value', digits=(16, 2))
    volume = fields.Float('Volume', digits=(16, 0))
    total_value = fields.Float('Total Value', digits=(16, 2))
    change_percent = fields.Float('Change Percent', digits=(16, 4))
    
    # Metadata
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now)
    
    _sql_constraints = [
        ('unique_index_date', 'unique(index_code, date)', 
         'Index code and date must be unique!'),
    ]

    @api.model
    def get_index_codes(self):
        """Get all available index codes"""
        return self.search([]).mapped('index_code')
