odoo.define('custom_auth.login', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.CustomLogin = publicWidget.Widget.extend({
        selector: '[data-js="custom-login"]',
        events: {
            'click .password-toggle': '_onTogglePassword',
            'click .social-button': '_onSocialLogin',
            'submit form': '_onSubmitForm'
        },

        start: function () {
            this._super.apply(this, arguments);
            this._initPasswordToggle();
            this._initFormValidation();
            return this;
        },

        _initPasswordToggle: function () {
            var self = this;
            // Use event delegation for better performance
            this.$el.on('click', '.password-toggle', function (e) {
                e.preventDefault();
                e.stopPropagation();
                self._togglePasswordVisibility($(this));
            });
            
            // Add keyboard support
            this.$el.on('keydown', '.password-toggle', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    self._togglePasswordVisibility($(this));
                }
            });
        },

        _togglePasswordVisibility: function (toggleButton) {
            var passwordInput = toggleButton.siblings('input[type="password"], input[type="text"]');
            var icon = toggleButton.find('i');
            
            if (passwordInput.attr('type') === 'password') {
                passwordInput.attr('type', 'text');
                icon.removeClass('fa-eye-slash').addClass('fa-eye');
                toggleButton.attr('aria-label', 'Ẩn mật khẩu');
                toggleButton.addClass('password-visible');
                
                // Auto-hide password after 3 seconds for security
                setTimeout(function () {
                    if (passwordInput.attr('type') === 'text') {
                        passwordInput.attr('type', 'password');
                        icon.removeClass('fa-eye').addClass('fa-eye-slash');
                        toggleButton.attr('aria-label', 'Hiển thị mật khẩu');
                        toggleButton.removeClass('password-visible');
                    }
                }, 3000);
                
            } else {
                passwordInput.attr('type', 'password');
                icon.removeClass('fa-eye').addClass('fa-eye-slash');
                toggleButton.attr('aria-label', 'Hiển thị mật khẩu');
                toggleButton.removeClass('password-visible');
            }
        },

        _initFormValidation: function () {
            var self = this;
            
            // Real-time validation
            this.$('input[type="email"]').on('blur', function () {
                self._validateEmail($(this));
            });
            
            this.$('input[type="password"]').on('blur', function () {
                self._validatePassword($(this));
            });
        },

        _validateEmail: function (emailInput) {
            var email = emailInput.val();
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && !emailRegex.test(email)) {
                this._showError(emailInput, '<i class="fas fa-exclamation-circle"></i> Email không hợp lệ');
                return false;
            } else {
                this._hideError(emailInput);
                return true;
            }
        },

        _validatePassword: function (passwordInput) {
            var password = passwordInput.val();
            
            if (password && password.length < 6) {
                this._showError(passwordInput, '<i class="fas fa-exclamation-circle"></i> Mật khẩu phải có ít nhất 6 ký tự');
                return false;
            } else {
                this._hideError(passwordInput);
                return true;
            }
        },

        _showError: function (input, message) {
            var errorDiv = input.siblings('.error-message');
            if (errorDiv.length === 0) {
                errorDiv = $('<div class="error-message"></div>');
                input.after(errorDiv);
            }
            errorDiv.html(message);
            input.removeClass('success').addClass('error');
        },

        _hideError: function (input) {
            input.siblings('.error-message').remove();
            input.removeClass('error');
        },

        _onSubmitForm: function (e) {
            var emailInput = this.$('input[type="email"]');
            var passwordInput = this.$('input[type="password"]');
            
            var isEmailValid = this._validateEmail(emailInput);
            var isPasswordValid = this._validatePassword(passwordInput);
            
            if (!isEmailValid || !isPasswordValid) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            var submitButton = this.$('.btn-primary');
            var originalText = submitButton.text();
            submitButton.html('<i class="fas fa-spinner fa-spin me-2"></i>Đang đăng nhập...').prop('disabled', true);
            
            // Re-enable after a delay (in case of error)
            setTimeout(function () {
                submitButton.html(originalText).prop('disabled', false);
            }, 3000);
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
                // Redirect to social login URL or show message
                console.log('Social login with:', provider);
            }, 2000);
        },

        _onTogglePassword: function (e) {
            e.preventDefault();
            this._togglePasswordVisibility($(e.currentTarget));
        }
    });

    return publicWidget.registry.CustomLogin;
}); 