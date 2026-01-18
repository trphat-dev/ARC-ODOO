# Copyright 2024
# License AGPL-3.0 or later

"""
PDF Utilities for contract signing
"""
import base64
import io
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None

_logger = logging.getLogger(__name__)


class PdfRect:
    """Helper class for PDF rectangle operations"""
    
    DEFAULT_DIGITAL_RECT = (315, 720, 560, 760)
    DEFAULT_SIGNATURE_RECT = (315, 662, 550, 700)
    DEFAULT_NAME_RECT = (180, 272, 600, 420)
    DEFAULT_BIRTH_RECT = (180, 298, 600, 340)
    DEFAULT_ID_RECT = (180, 324, 600, 370)
    DEFAULT_EMAIL_RECT = (180, 349, 600, 470)
    DEFAULT_PHONE_RECT = (180, 374, 600, 430)
    
    @staticmethod
    def parse_rect(rect_data: Any, default: Tuple[float, float, float, float]) -> 'fitz.Rect':
        """Parse rectangle data from various formats"""
        if not fitz:
            raise ImportError("PyMuPDF (fitz) is required for PDF operations")
            
        try:
            if isinstance(rect_data, (list, tuple)) and len(rect_data) == 4:
                return fitz.Rect(*[float(v) for v in rect_data])
        except (ValueError, TypeError) as e:
            _logger.warning(f"Invalid rect data: {e}, using default")
        return fitz.Rect(*default)


class PdfSigner:
    """PDF signing utilities"""
    
    @staticmethod
    def decode_base64_pdf(document_b64: str) -> bytes:
        """Decode base64 PDF document"""
        try:
            return base64.b64decode(document_b64)
        except Exception as e:
            _logger.error(f"Failed to decode base64 PDF: {e}")
            raise ValueError("document_base64 không hợp lệ")
    
    @staticmethod
    def open_pdf(pdf_bytes: bytes) -> 'fitz.Document':
        """Open PDF document from bytes"""
        if not fitz:
            raise ImportError("PyMuPDF (fitz) is required for PDF operations")
            
        try:
            return fitz.open(stream=io.BytesIO(pdf_bytes).getvalue(), filetype='pdf')
        except Exception as e:
            _logger.error(f"Failed to open PDF: {e}")
            raise ValueError("Không thể mở file PDF")
    
    @staticmethod
    def add_digital_signature(
        pdf_bytes: bytes,
        signer: str,
        position: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Add digital signature (text) to PDF"""
        doc = PdfSigner.open_pdf(pdf_bytes)
        page = doc[-1]
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        signed_text = f"Digitally signed by {signer} at {now}"
        
        positions = position or {}
        rect_digital = PdfRect.parse_rect(
            positions.get('digital'),
            PdfRect.DEFAULT_DIGITAL_RECT
        )
        
        page.insert_textbox(rect_digital, signed_text, fontsize=11, color=(0, 0, 0), align=0)
        
        out = io.BytesIO()
        doc.save(out)
        out.seek(0)
        return out.getvalue()
    
    @staticmethod
    def prepare_signature_image(image_data_url: str) -> bytes:
        """Prepare signature image from data URL"""
        if not Image:
            raise ImportError("PIL (Pillow) is required for image processing")
            
        try:
            header, encoded = image_data_url.split(',', 1)
            signature_bytes = base64.b64decode(encoded)
            
            img = Image.open(io.BytesIO(signature_bytes))
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                buf = io.BytesIO()
                background.save(buf, format='JPEG')
                return buf.getvalue()
            else:
                buf = io.BytesIO()
                img.convert('RGB').save(buf, format='JPEG')
                return buf.getvalue()
        except Exception as e:
            _logger.error(f"Failed to prepare signature image: {e}")
            raise ValueError("Không thể xử lý ảnh chữ ký")
    
    @staticmethod
    def add_hand_signature(
        pdf_bytes: bytes,
        signature_image_bytes: bytes,
        signer_info: Dict[str, str],
        positions: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Add hand signature with signer info to PDF"""
        doc = PdfSigner.open_pdf(pdf_bytes)
        page = doc[-1]
        
        pos = positions or {}
        
        # Parse rectangles
        rect_signature = PdfRect.parse_rect(
            pos.get('signature'),
            PdfRect.DEFAULT_SIGNATURE_RECT
        )
        rect_name = PdfRect.parse_rect(
            pos.get('name'),
            PdfRect.DEFAULT_NAME_RECT
        )
        rect_birth = PdfRect.parse_rect(
            pos.get('birth'),
            PdfRect.DEFAULT_BIRTH_RECT
        )
        rect_id = PdfRect.parse_rect(
            pos.get('id'),
            PdfRect.DEFAULT_ID_RECT
        )
        rect_email = PdfRect.parse_rect(
            pos.get('email'),
            PdfRect.DEFAULT_EMAIL_RECT
        )
        rect_phone = PdfRect.parse_rect(
            pos.get('phone'),
            PdfRect.DEFAULT_PHONE_RECT
        )
        
        # Insert signature image
        img_tmp = io.BytesIO(signature_image_bytes)
        page.insert_image(rect_signature, stream=img_tmp.getvalue())
        
        # Insert text fields
        page.insert_textbox(
            rect_name,
            signer_info.get('name', ''),
            fontsize=13,
            color=(0, 0, 0),
            align=0
        )
        page.insert_textbox(
            rect_email,
            signer_info.get('email', ''),
            fontsize=13,
            color=(0, 0, 0),
            align=0
        )
        page.insert_textbox(
            rect_birth,
            signer_info.get('birth_date', ''),
            fontsize=13,
            color=(0, 0, 0),
            align=0
        )
        page.insert_textbox(
            rect_id,
            signer_info.get('id_number', ''),
            fontsize=13,
            color=(0, 0, 0),
            align=0
        )
        page.insert_textbox(
            rect_phone,
            signer_info.get('phone', ''),
            fontsize=13,
            color=(0, 0, 0),
            align=0
        )
        
        out = io.BytesIO()
        doc.save(out)
        out.seek(0)
        return out.getvalue()

