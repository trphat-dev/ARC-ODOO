import hashlib
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..utils import constants

_logger = logging.getLogger(__name__)


class FundSignedContract(models.Model):
    _name = 'fund.signed.contract'
    _description = 'Fund Signed Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Contract Code',
        required=True,
        index=True,
        readonly=True,
        copy=False,
        default=lambda self: self._generate_contract_code()
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Investor',
        required=False,
        index=True,
        ondelete='set null',
        tracking=True
    )
    investment_id = fields.Many2one(
        'portfolio.investment',
        string='Investment',
        required=False,
        index=True,
        ondelete='set null',
        tracking=True
    )
    transaction_id = fields.Many2one(
        'portfolio.transaction',
        string='Transaction',
        required=False,
        index=True,
        ondelete='set null',
        tracking=True
    )

    signed_type = fields.Selection(
        constants.CONTRACT_SIGNED_TYPES,
        string='Sign Type',
        default=constants.CONTRACT_SIGNED_TYPE_HAND,
        required=True,
        tracking=True
    )

    file_data = fields.Binary(
        string='Contract File',
        attachment=True,
        required=True
    )
    filename = fields.Char(string='Filename', required=True)

    # Hash for integrity verification
    contract_hash = fields.Char(
        string='Contract Hash',
        readonly=True,
        copy=False,
        help='SHA256 hash of the contract file for integrity verification'
    )

    signer_email = fields.Char(string='Signer Email', tracking=True)
    signer_phone = fields.Char(string='Signer Phone', tracking=True)
    signer_id_number = fields.Char(string='Signer ID Number', tracking=True)
    signer_birth_date = fields.Char(string='Signer Birth Date', tracking=True)
    
    signed_on = fields.Datetime(
        string='Signed On',
        readonly=True,
        default=lambda self: fields.Datetime.now(),
        tracking=True
    )

    create_date = fields.Datetime(readonly=True)
    write_date = fields.Datetime(readonly=True)

    @api.model
    def _generate_contract_code(self, signed_type=None):
        """Generate contract code"""
        from ..utils.contract_utils import ContractCodeGenerator
        return ContractCodeGenerator.generate_code(
            signed_type or constants.CONTRACT_SIGNED_TYPE_HAND
        )

    @api.constrains('file_data')
    def _check_file_present(self):
        """Validate that file data is present"""
        for rec in self:
            if not rec.file_data:
                raise ValidationError("Contract file is required")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to compute hash and set defaults"""
        for vals in vals_list:
            # Set filename if not provided
            if not vals.get('filename') and vals.get('name'):
                from ..utils.contract_utils import ContractCodeGenerator
                vals['filename'] = ContractCodeGenerator.generate_filename(vals['name'])
            
            # Compute hash if file_data is provided
            if vals.get('file_data'):
                vals['contract_hash'] = self._compute_file_hash(vals['file_data'])
        
        records = super().create(vals_list)
        
        # Log creation
        for record in records:
            record._log_action('create')
        
        return records

    def write(self, vals):
        """Override write to update hash if file_data changes"""
        if 'file_data' in vals:
            vals['contract_hash'] = self._compute_file_hash(vals['file_data'])
        
        result = super().write(vals)
        
        # Log update
        if vals:
            for record in self:
                record._log_action('update')
        
        return result

    @staticmethod
    def _compute_file_hash(file_data_base64):
        """Compute SHA256 hash of file data"""
        import base64
        try:
            if isinstance(file_data_base64, str):
                # Already base64 encoded
                file_bytes = base64.b64decode(file_data_base64)
            else:
                # Binary field - decode if needed
                file_bytes = base64.b64decode(file_data_base64) if file_data_base64 else b''
            return hashlib.sha256(file_bytes).hexdigest()
        except Exception as e:
            _logger.warning(f"Failed to compute file hash: {e}")
            return ""

    def _log_action(self, action):
        """Log action on contract"""
        try:
            self.message_post(
                body=f"Contract {action}",
                subject=f"Contract {action.title()}"
            )
        except Exception as e:
            _logger.warning(f"Failed to log action: {e}")

    def get_contract_by_investment(self, investment_id):
        """Get contract by investment ID"""
        return self.search([
            ('investment_id', '=', investment_id)
        ], limit=1, order='create_date desc')

    def get_contract_by_partner(self, partner_id):
        """Get contract by partner ID"""
        return self.search([
            ('partner_id', '=', partner_id)
        ], limit=1, order='create_date desc')

    def get_contract_by_transaction(self, transaction_id):
        """Get contract by transaction ID"""
        return self.search([
            ('transaction_id', '=', transaction_id)
        ], limit=1, order='create_date desc')


