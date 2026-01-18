import os
import base64
from odoo import http
from odoo.http import request
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ImageController(http.Controller):
    @http.route('/investor/upload/id_document', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_id_document(self, **post):
        """Handle ID document image upload"""
        try:
            # Get uploaded files
            front_image = post.get('front_image')
            back_image = post.get('back_image')
            
            if not front_image or not back_image:
                return {'error': 'Missing required images'}

            # Get current user email for filename
            user_email = request.env.user.email
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Save files to id_images folder
            save_path = os.path.join(request.env['ir.config_parameter'].sudo().get_param('data_dir'), 'id_images')
            os.makedirs(save_path, exist_ok=True)
            
            # Save front image
            front_filename = f'cccd_front_{user_email}_{timestamp}.jpg'
            front_path = os.path.join(save_path, front_filename)
            front_image_data = base64.b64decode(front_image.split(',')[1])
            with open(front_path, 'wb') as f:
                f.write(front_image_data)

            # Save back image  
            back_filename = f'cccd_back_{user_email}_{timestamp}.jpg'
            back_path = os.path.join(save_path, back_filename)
            back_image_data = base64.b64decode(back_image.split(',')[1])
            with open(back_path, 'wb') as f:
                f.write(back_image_data)

            # Update investor profile with image paths (current user only)
            investor = request.env['investor.profile'].sudo().search([
                ('user_id', '=', request.env.user.id)
            ], limit=1)
            if investor:
                investor.write({
                    'id_front_path': front_path,
                    'id_back_path': back_path
                })

            return {'success': True, 'message': 'Images uploaded successfully'}

        except Exception as e:
            _logger.error('Error uploading ID documents: %s', str(e))
            return {'error': str(e)}
