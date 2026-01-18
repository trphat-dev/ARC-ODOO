# Copyright 2024
# License AGPL-3.0 or later

"""
Contract utilities for generating contract codes and names
"""
import hashlib
from datetime import datetime
from typing import Optional

from odoo import http
from odoo.http import request


class ContractCodeGenerator:
    """Generate contract codes"""
    
    PREFIX_DIGITAL = "SC-D"
    PREFIX_HAND = "SC-H"
    
    @staticmethod
    def generate_code(signed_type: str = 'hand') -> str:
        """Generate contract code"""
        prefix = (
            ContractCodeGenerator.PREFIX_DIGITAL
            if signed_type == 'digital'
            else ContractCodeGenerator.PREFIX_HAND
        )
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}-{timestamp}"
    
    @staticmethod
    def generate_filename(code: str) -> str:
        """Generate filename from code"""
        return f"{code}.pdf"


class ContractHashGenerator:
    """Generate hash for contract integrity"""
    
    @staticmethod
    def compute_hash(data: bytes) -> str:
        """Compute SHA256 hash of contract data"""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def compute_hash_from_base64(base64_data: str) -> str:
        """Compute hash from base64 encoded data"""
        import base64
        try:
            data = base64.b64decode(base64_data)
            return ContractHashGenerator.compute_hash(data)
        except Exception:
            return ""


class ContractSignerInfo:
    """Extract signer information from request"""
    
    @staticmethod
    def get_signer_from_request(default_signer: Optional[str] = None) -> str:
        """Get signer from request context"""
        if default_signer:
            return default_signer
        
        user = request.env.user
        return user.email or user.login or ''

