from odoo import models, fields


class IndexComponents(models.Model):
    """Index Components"""
    _name = 'ssi.index.components'
    _description = 'Index Components'
    _order = 'weight desc'

    index_id = fields.Many2one('ssi.index.list', string='Index', required=True, ondelete='cascade')
    index_code = fields.Char(related='index_id.index_code', store=True, readonly=True)

    security_id = fields.Many2one('ssi.securities', string='Security', required=True, ondelete='cascade')
    symbol = fields.Char(related='security_id.symbol', store=True, readonly=True)

    weight = fields.Float('Weight (%)')
    is_active = fields.Boolean('Is Active', default=True)
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now)

    _sql_constraints = [
        ('index_security_unique', 'unique(index_id, security_id)', 'Index and Security combination must be unique!')
    ]


