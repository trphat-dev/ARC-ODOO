from odoo import models, fields


class IndexList(models.Model):
    """Stock Index List"""
    _name = 'ssi.index.list'
    _description = 'Index List'
    _order = 'index_code asc'
    _rec_name = 'index_code'

    index_code = fields.Char('Index Code', required=True, index=True)
    exchange = fields.Selection([
        ('hose', 'HOSE'),
        ('hnx', 'HNX'),
        ('upcom', 'UPCOM')
    ], string='Exchange', index=True)

    index_name_vn = fields.Char('Index Name (VN)')
    index_name_en = fields.Char('Index Name (EN)')
    index_type = fields.Char('Index Type')
    base_value = fields.Float('Base Value')
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now)

    component_ids = fields.One2many('ssi.index.components', 'index_id', string='Components')

    _sql_constraints = [
        ('index_code_unique', 'unique(index_code)', 'Index Code must be unique!')
    ]


