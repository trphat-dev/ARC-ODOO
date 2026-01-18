# Copyright 2024
# License AGPL-3.0 or later

"""
URL Utilities for contract signing
"""
import logging
import os
from typing import Optional
from urllib.parse import urlparse, urlunparse

try:
    import requests
except ImportError:
    requests = None

from odoo import http
from odoo.http import request
import odoo

_logger = logging.getLogger(__name__)


class UrlValidator:
    """URL validation and processing utilities"""
    
    FORBIDDEN_PATHS = [
        '/transaction_management/contract',
    ]
    
    @staticmethod
    def get_base_urls():
        """Get internal and external base URLs"""
        internal_base = request.httprequest.host_url.rstrip('/')
        xf_proto = request.httprequest.headers.get('X-Forwarded-Proto')
        xf_host = request.httprequest.headers.get('X-Forwarded-Host')
        external_base = None
        
        if xf_host:
            external_base = f"{(xf_proto or 'http')}://{xf_host}"
        
        return internal_base, external_base
    
    @staticmethod
    def build_internal_url_from_absolute(abs_url: str, internal_base: str) -> str:
        """Build internal URL from absolute URL"""
        parsed = urlparse(abs_url)
        path_query = urlunparse(('', '', parsed.path or '/', '', parsed.query or '', ''))
        return internal_base + (path_query if path_query.startswith('/') else '/' + path_query)
    
    @staticmethod
    def is_allowed_url(url: str) -> tuple[bool, Optional[str]]:
        """Check if URL is allowed and return internal URL if valid"""
        internal_base, external_base = UrlValidator.get_base_urls()
        
        # Check forbidden paths
        parsed_path = urlparse(url).path or ''
        for forbidden_path in UrlValidator.FORBIDDEN_PATHS:
            if parsed_path.startswith(forbidden_path):
                return False, None
        
        # Absolute URL
        if url.startswith('http://') or url.startswith('https://'):
            if external_base and url.startswith(external_base):
                target_internal_url = UrlValidator.build_internal_url_from_absolute(url, internal_base)
                return True, target_internal_url
            elif url.startswith(internal_base):
                return True, url
            return False, None
        
        # Relative URL
        return True, internal_base + (url if url.startswith('/') else '/' + url)
    
    @staticmethod
    def fetch_pdf(url: str, timeout: int = 10) -> bytes:
        """Fetch PDF from URL or static file path"""
        # Parse URL to get path
        parsed = urlparse(url)
        path = parsed.path or url
        
        # Kiểm tra nếu là static file path (bắt đầu với /fund_management/static/ hoặc fund_management/static/)
        if path.startswith('/fund_management/static/') or path.startswith('fund_management/static/'):
            # Đọc từ static files trực tiếp thay vì HTTP request
            return UrlValidator._read_static_file(path)
        
        # Nếu là HTTP URL, dùng HTTP request
        if not requests:
            raise ImportError("requests library is required for URL fetching")
        
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            _logger.error(f"Failed to fetch PDF from {url}: {e}")
            raise ValueError(f"Không thể tải PDF: {str(e)}")
    
    @staticmethod
    def _read_static_file(path: str) -> bytes:
        """Read static file from addons directory"""
        try:
            # Loại bỏ leading slash và 'fund_management/' prefix
            # path: /fund_management/static/src/pdf/terms2.pdf
            # file_path: static/src/pdf/terms2.pdf
            if path.startswith('/fund_management/'):
                file_path = path[len('/fund_management/'):]
            elif path.startswith('fund_management/'):
                file_path = path[len('fund_management/'):]
            else:
                file_path = path
            
            # Tìm addons path
            addons_paths = odoo.tools.config.get('addons_path', '').split(',')
            addons_paths = [p.strip() for p in addons_paths if p.strip()]
            
            # Tìm file trong các addons paths
            for addons_path in addons_paths:
                full_path = os.path.join(addons_path, 'fund_management', file_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    with open(full_path, 'rb') as f:
                        return f.read()
            
            # Nếu không tìm thấy, thử tìm trong module directory hiện tại
            import inspect
            current_file = inspect.getfile(UrlValidator)
            module_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            full_path = os.path.join(module_dir, file_path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, 'rb') as f:
                    return f.read()
            
            raise FileNotFoundError(f"Static file not found: {path}")
        except Exception as e:
            _logger.error(f"Failed to read static file {path}: {e}")
            raise ValueError(f"Không thể đọc file PDF: {str(e)}")

