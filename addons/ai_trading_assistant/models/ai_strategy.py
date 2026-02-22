from odoo import models, fields, api

class AIStrategy(models.Model):
    _name = 'ai.strategy'
    _description = 'AI Trading Strategy (FinRL Model)'
    
    name = fields.Char(string='Tên Chiến lược', required=True)
    description = fields.Text(string='Mô tả chiến lược')
    
    ticker_ids = fields.Many2many(
        'stock.ticker', 
        string='Áp dụng cho Mã CK', 
        help='Nếu để trống, chiến lược này áp dụng chung cho mọi mã. Nếu chọn mã cụ thể, Chatbot sẽ ưu tiên dùng chiến lược này cho các mã tương ứng.'
    )
    
    algorithm = fields.Selection([
        ('ppo', 'PPO (Proximal Policy Optimization)'),
        ('a2c', 'A2C (Advantage Actor Critic)'),
        ('ddpg', 'DDPG')
    ], string='Thuật toán (Algorithm)', required=True, default='ppo')
    
    status = fields.Selection([
        ('draft', 'Mới tạo'),
        ('training', 'Đang huấn luyện'),
        ('trained', 'Đã huấn luyện xong'),
        ('active', 'Đang sử dụng')
    ], string='Trạng thái', default='draft')
    
    model_file = fields.Binary(string='File Mô hình AI (.zip)', attachment=True, help='Upload file .zip chứa model weights')
    model_filename = fields.Char(string='Tên File')
    
    # Hyperparameters
    learning_rate = fields.Float(string='Learning Rate', default=0.00025, tracking=True)
    batch_size = fields.Integer(string='Batch Size', default=64, tracking=True)
    ent_coef = fields.Float(string='Entropy Coefficient', default=0.01, tracking=True)
    
    # metrics
    sharpe_ratio = fields.Float(string='Sharpe Ratio (Backtest)', tracking=True)
    expected_return = fields.Float(string='Return (%)', tracking=True)
    max_drawdown = fields.Float(string='Max Drawdown (%)', tracking=True)
    
    # Môi trường
    framework_version = fields.Char(string='FinRL/SB3 Version')
    training_time = fields.Char(string='Thời gian huấn luyện')
    
    # Tracking / Security
    user_id = fields.Many2one('res.users', string='Người phụ trách', default=lambda self: self.env.user)
    
    def _parse_model_metadata(self, model_binary):
        """Mở file ZIP, đọc metadata.json và trả về dict các giá trị."""
        import zipfile
        import json
        import io
        import base64
        
        if not model_binary:
            return {}
            
        try:
            content = base64.b64decode(model_binary)
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                if 'metadata.json' in zf.namelist():
                    with zf.open('metadata.json') as f:
                        return json.loads(f.read().decode('utf-8'))
        except Exception:
            pass
        return {}

    def action_activate(self):
        # Tắt các chiến lược active khác (hoặc cải thiện để chỉ tắt các chiến lược trùng mã)
        self.search([('status', '=', 'active')]).write({'status': 'trained'})
        self.status = 'active'
        
    def action_draft(self):
        self.status = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('model_file'):
                metadata = self._parse_model_metadata(vals['model_file'])
                if metadata:
                    # Tự động điền các field từ metadata nếu có
                    vals.update({
                        'algorithm': metadata.get('algorithm', vals.get('algorithm', 'ppo')),
                        'learning_rate': metadata.get('learning_rate', 0.00025),
                        'batch_size': metadata.get('batch_size', 64),
                        'ent_coef': metadata.get('ent_coef', 0.01),
                        'sharpe_ratio': metadata.get('sharpe_ratio', 0.0),
                        'expected_return': metadata.get('expected_return', 0.0),
                        'max_drawdown': metadata.get('max_drawdown', 0.0),
                        'training_time': metadata.get('training_time', ''),
                        'framework_version': metadata.get('framework_version', ''),
                        'status': 'trained'
                    })
                elif vals.get('status', 'draft') == 'draft':
                    vals['status'] = 'trained'
                    
        records = super().create(vals_list)
        
        # Tạo Training History sau khi tạo record thành công
        for record in records:
            if record.model_file:
                self._create_history_log(record)
        return records

    def write(self, vals):
        if vals.get('model_file'):
            metadata = self._parse_model_metadata(vals['model_file'])
            if metadata:
                 vals.update({
                    'algorithm': metadata.get('algorithm', self.algorithm),
                    'learning_rate': metadata.get('learning_rate', self.learning_rate),
                    'batch_size': metadata.get('batch_size', self.batch_size),
                    'ent_coef': metadata.get('ent_coef', self.ent_coef),
                    'sharpe_ratio': metadata.get('sharpe_ratio', self.sharpe_ratio),
                    'expected_return': metadata.get('expected_return', self.expected_return),
                    'max_drawdown': metadata.get('max_drawdown', self.max_drawdown),
                    'training_time': metadata.get('training_time', self.training_time),
                    'framework_version': metadata.get('framework_version', self.framework_version),
                    'status': 'trained'
                })
            else:
                vals['status'] = 'trained'
            
        res = super(AIStrategy, self).write(vals)
        
        if vals.get('model_file'):
            for record in self:
                self._create_history_log(record)
        return res

    def _create_history_log(self, record):
        """Helper để tạo log lịch sử huấn luyện."""
        self.env['ai.training.history'].create({
            'name': f"Upload: {record.model_filename or 'Unknown.zip'} ({record.name})",
            'algorithm': record.algorithm,
            'tickers': ", ".join(record.ticker_ids.mapped('name')) if record.ticker_ids else "ALL",
            'learning_rate': record.learning_rate,
            'batch_size': record.batch_size,
            'ent_coef': record.ent_coef,
            'sharpe_ratio': record.sharpe_ratio,
            'max_drawdown': record.max_drawdown,
            'training_time': record.training_time,
            'model_file': record.model_file,
            'model_filename': record.model_filename,
            'log_text': f"Mô hình được tải lên cho chiến lược [{record.name}].\n"
                       f"Thuật toán: {record.algorithm}\n"
                       f"Sharpe Ratio: {record.sharpe_ratio}\n"
                       f"Framework: {record.framework_version}",
        })
