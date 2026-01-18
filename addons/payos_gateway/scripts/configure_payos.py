"""
Script để cấu hình PayOS credentials vào Odoo
Chạy script này trong Odoo shell để tự động cấu hình PayOS credentials
"""
import odoo
from odoo import api, SUPERUSER_ID

def configure_payos_credentials():
    """
    Cấu hình PayOS credentials vào ir.config_parameter
    """
    # PayOS credentials
    CLIENT_ID = '5edf2d5c-a8d9-4eb3-a452-6dec60a38a10'
    API_KEY = '3aaed460-eaa8-4944-a975-0d2071140a85'
    CHECKSUM_KEY = 'c19d6cd87aaff29ee63507cc242c760ad9aeeda48cc97cb32be5943ff90f279a'
    
    # Khởi tạo Odoo registry
    env = odoo.api.Environment(odoo.registry(odoo.tools.config['db_name']), SUPERUSER_ID, {})
    
    # Lấy ir.config_parameter
    params = env['ir.config_parameter'].sudo()
    
    # Cấu hình PayOS credentials
    params.set_param('payos.client_id', CLIENT_ID)
    params.set_param('payos.api_key', API_KEY)
    params.set_param('payos.checksum_key', CHECKSUM_KEY)
    
    print("✅ Đã cấu hình PayOS credentials thành công!")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   API Key: {API_KEY[:20]}...")
    print(f"   Checksum Key: {CHECKSUM_KEY[:20]}...")

if __name__ == '__main__':
    configure_payos_credentials()

