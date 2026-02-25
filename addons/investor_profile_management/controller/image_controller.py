import base64
from odoo import http
from odoo.http import request
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ImageController(http.Controller):
    @http.route('/investor/upload/id_document', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_id_document(self, **post):
        """Handle ID document image upload - saves to database only"""
        try:
            front_image = post.get('front_image')
            back_image = post.get('back_image')
            
            if not front_image or not back_image:
                return {'error': 'Missing required images'}

            user_email = request.env.user.email
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Decode and save front image to database
            front_filename = f'cccd_front_{user_email}_{timestamp}.jpg'
            front_image_data = base64.b64decode(front_image.split(',')[1])

            # Decode and save back image to database
            back_filename = f'cccd_back_{user_email}_{timestamp}.jpg'
            back_image_data = base64.b64decode(back_image.split(',')[1])

            # Update investor profile with image data in database
            investor = request.env['investor.profile'].sudo().search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            if investor:
                investor.write({
                    'id_front': front_image_data,
                    'id_front_filename': front_filename,
                    'id_back': back_image_data,
                    'id_back_filename': back_filename,
                })

            return {'success': True, 'message': 'Images uploaded successfully'}

        except Exception as e:
            _logger.error('Error uploading ID documents: %s', str(e))
            return {'error': str(e)}
