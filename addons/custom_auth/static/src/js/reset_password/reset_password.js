odoo.define('custom_auth.reset_password', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.CustomResetPassword = publicWidget.Widget.extend({
        selector: '.custom-reset-form',
        events: {
            'click .social-button': '_onSocialLogin',
            'submit form': '_onSubmitForm',
            'input #email': '_onEmailInput'
        },

        start: function () {
            this._super.apply(this, arguments);
            this._initFormValidation();
            this._checkForSuccessMessage();
            return this;
        },

        _initFormValidation: function () {
            var self = this;
            
            // Real-time validation
            this.$('input[type="email"]').on('blur', function () {
                self._validateEmail($(this));
            });
        },

        _validateEmail: function (emailInput) {
            var email = emailInput.val().trim();
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (!email) {
                this._showError(emailInput, 'Vui lòng nhập email');
                return false;
            } else if (!emailRegex.test(email)) {
                this._showError(emailInput, 'Email không hợp lệ');
                return false;
            } else {
                this._showSuccess(emailInput);
                return true;
            }
        },

        _showError: function (input, message) {
            var errorDiv = input.siblings('.error-message');
            if (errorDiv.length === 0) {
                errorDiv = $('<div class="error-message"></div>');
                input.after(errorDiv);
            }
            errorDiv.text(message);
            input.removeClass('success').addClass('error');
        },

        _showSuccess: function (input) {
            var errorDiv = input.siblings('.error-message');
            var successDiv = input.siblings('.success-message');
            
            errorDiv.remove();
            if (successDiv.length === 0) {
                successDiv = $('<div class="success-message">✓ Email hợp lệ</div>');
                input.after(successDiv);
            }
            input.removeClass('error').addClass('success');
        },

        _hideMessages: function (input) {
            input.siblings('.error-message, .success-message').remove();
            input.removeClass('error success');
        },

        _onSubmitForm: function (e) {
            var emailInput = this.$('#email');
            var isEmailValid = this._validateEmail(emailInput);
            
            if (!isEmailValid) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            var submitButton = this.$('.login-button');
            var originalText = submitButton.text();
            submitButton.text('Đang gửi...').prop('disabled', true);
            
            // Re-enable after a delay (in case of error)
            setTimeout(function () {
                submitButton.text(originalText).prop('disabled', false);
            }, 5000);
        },

        _onSocialLogin: function (e) {
            e.preventDefault();
            var provider = $(e.currentTarget).data('provider');
            
            // Show loading state
            var button = $(e.currentTarget);
            var originalContent = button.html();
            button.html('<i class="fas fa-spinner fa-spin"></i>').prop('disabled', true);
            
            // Simulate social login (replace with actual implementation)
            setTimeout(function () {
                button.html(originalContent).prop('disabled', false);
                console.log('Social login with:', provider);
            }, 2000);
        },

        _onEmailInput: function (e) {
            var input = $(e.target);
            if (input.val().trim()) {
                this._hideMessages(input);
            }
        },

        _checkForSuccessMessage: function () {
            // Check if there's a success message from Odoo
            var successAlert = this.$('.alert-success');
            if (successAlert.length > 0) {
                this._showEmailSentConfirmation();
            }
        },

        _showEmailSentConfirmation: function () {
            var form = this.$('form');
            var email = this.$('#email').val();
            
            // Replace form with success message
            form.hide();
            
            var successHtml = `
                <div class="email-sent">
                    <div class="email-sent-icon">
                        <i class="fas fa-envelope-open"></i>
                    </div>
                    <div class="email-sent-title">Email đã được gửi!</div>
                    <div class="email-sent-message">
                        Chúng tôi đã gửi hướng dẫn đặt lại mật khẩu đến <strong>${email}</strong>.<br>
                        Vui lòng kiểm tra hộp thư và làm theo hướng dẫn.
                    </div>
                </div>
                <div class="resend-countdown">
                    <div>Chưa nhận được email? <button class="resend-button" id="resend-button">Gửi lại</button></div>
                    <div id="countdown" style="display: none; margin-top: 0.5rem; font-size: 0.75rem; color: #9ca3af;"></div>
                </div>
            `;
            
            form.after(successHtml);
            
            // Handle resend button
            this.$('#resend-button').on('click', function () {
                $(this).prop('disabled', true).text('Đang gửi...');
                var countdown = $('#countdown');
                var timeLeft = 60;
                
                countdown.show().text(`Có thể gửi lại sau ${timeLeft} giây`);
                
                var timer = setInterval(function () {
                    timeLeft--;
                    countdown.text(`Có thể gửi lại sau ${timeLeft} giây`);
                    
                    if (timeLeft <= 0) {
                        clearInterval(timer);
                        countdown.hide();
                        $('#resend-button').prop('disabled', false).text('Gửi lại');
                    }
                }, 1000);
                
                // Simulate resend request
                setTimeout(function () {
                    console.log('Resending reset password email to:', email);
                }, 2000);
            });
        },

        _showInfoMessage: function (message) {
            var infoDiv = $('<div class="reset-info"></div>');
            infoDiv.text(message);
            this.$('form').before(infoDiv);
        },

        _showWarningMessage: function (message) {
            var warningDiv = $('<div class="reset-warning"></div>');
            warningDiv.text(message);
            this.$('form').before(warningDiv);
        },

        _showSuccessMessage: function (message) {
            var successDiv = $('<div class="reset-success"></div>');
            successDiv.text(message);
            this.$('form').before(successDiv);
        }
    });

    return publicWidget.registry.CustomResetPassword;
});