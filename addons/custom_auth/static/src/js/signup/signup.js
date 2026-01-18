odoo.define('custom_auth.signup', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.CustomSignup = publicWidget.Widget.extend({
        selector: '[data-js="custom-signup"]',
        events: {
            'click .password-toggle': '_onTogglePassword',
            'click .social-button': '_onSocialSignup',
            'submit form': '_onSubmitForm',
            'input #password': '_onPasswordInput',
            'input #confirm_password': '_onConfirmPasswordInput',
            'input #name': '_onNameInput',
            'input #email': '_onEmailInput'
        },

        start: function () {
            this._super.apply(this, arguments);
            this._initPasswordStrength();
            this._initFormValidation();
            this._initPasswordToggle();
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

        _initPasswordStrength: function () {
            var self = this;
            this.$('#password').on('input', function () {
                self._checkPasswordStrength($(this).val());
            });
        },

        _checkPasswordStrength: function (password) {
            var strength = 0;
            var feedback = '';

            // Check length
            if (password.length >= 8) strength += 1;
            if (password.length >= 12) strength += 1;

            // Check for different character types
            if (/[a-z]/.test(password)) strength += 1;
            if (/[A-Z]/.test(password)) strength += 1;
            if (/[0-9]/.test(password)) strength += 1;
            if (/[^A-Za-z0-9]/.test(password)) strength += 1;

            // Determine strength level
            var strengthLevel = 'weak';
            var strengthText = 'Yếu';
            var strengthColor = '#ef4444';

            if (strength >= 5) {
                strengthLevel = 'strong';
                strengthText = 'Mạnh';
                strengthColor = '#059669';
            } else if (strength >= 4) {
                strengthLevel = 'good';
                strengthText = 'Tốt';
                strengthColor = '#10b981';
            } else if (strength >= 3) {
                strengthLevel = 'fair';
                strengthText = 'Trung bình';
                strengthColor = '#f59e0b';
            }

            this._updatePasswordStrengthIndicator(strengthLevel, strengthText);
        },

        _updatePasswordStrengthIndicator: function (level, text) {
            var passwordField = this.$('#password');
            var existingIndicator = passwordField.siblings('.password-strength');
            
            if (existingIndicator.length === 0) {
                var indicator = $('<div class="password-strength"></div>');
                indicator.append('<div class="password-strength-bar"><div class="password-strength-fill"></div></div>');
                indicator.append('<div class="password-strength-text"></div>');
                passwordField.after(indicator);
            }

            var indicator = passwordField.siblings('.password-strength');
            var fill = indicator.find('.password-strength-fill');
            var textElement = indicator.find('.password-strength-text');

            fill.removeClass('weak fair good strong').addClass(level);
            textElement.removeClass('weak fair good strong').addClass(level).text(text);
        },

        _initFormValidation: function () {
            var self = this;
            
            // Real-time validation
            this.$('input[type="text"]').on('blur', function () {
                self._validateName($(this));
            });
            
            this.$('input[type="email"]').on('blur', function () {
                self._validateEmail($(this));
            });
            
            this.$('input[type="password"]').on('blur', function () {
                if ($(this).attr('id') === 'password') {
                    self._validatePassword($(this));
                } else if ($(this).attr('id') === 'confirm_password') {
                    self._validateConfirmPassword($(this));
                }
            });
        },

        _validateName: function (nameInput) {
            var name = nameInput.val().trim();
            
            if (!name) {
                this._showError(nameInput, 'Vui lòng nhập họ và tên');
                return false;
            } else if (name.length < 2) {
                this._showError(nameInput, 'Họ và tên phải có ít nhất 2 ký tự');
                return false;
            } else if (!/^[a-zA-ZÀ-ỹ\s]+$/.test(name)) {
                this._showError(nameInput, 'Họ và tên chỉ được chứa chữ cái và khoảng trắng');
                return false;
            } else {
                this._showSuccess(nameInput);
                return true;
            }
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

        _validatePassword: function (passwordInput) {
            var password = passwordInput.val();
            
            if (!password) {
                this._showError(passwordInput, 'Vui lòng nhập mật khẩu');
                return false;
            } else if (password.length < 8) {
                this._showError(passwordInput, 'Mật khẩu phải có ít nhất 8 ký tự');
                return false;
            } else {
                this._showSuccess(passwordInput);
                this._checkPasswordMatch();
                return true;
            }
        },

        _validateConfirmPassword: function (confirmInput) {
            var confirmPassword = confirmInput.val();
            var password = this.$('#password').val();
            
            if (!confirmPassword) {
                this._showError(confirmInput, 'Vui lòng xác nhận mật khẩu');
                return false;
            } else if (confirmPassword !== password) {
                this._showError(confirmInput, 'Mật khẩu xác nhận không khớp');
                return false;
            } else {
                this._showSuccess(confirmInput);
                this._checkPasswordMatch();
                return true;
            }
        },

        _checkPasswordMatch: function () {
            var password = this.$('#password').val();
            var confirmPassword = this.$('#confirm_password').val();
            var confirmField = this.$('#confirm_password');
            
            if (password && confirmPassword) {
                if (password === confirmPassword) {
                    this._showPasswordMatch(true);
                } else {
                    this._showPasswordMatch(false);
                }
            }
        },

        _showPasswordMatch: function (isMatch) {
            var confirmField = this.$('#confirm_password');
            var existingMatch = confirmField.siblings('.password-match');
            
            if (existingMatch.length === 0) {
                var matchIndicator = $('<div class="password-match"></div>');
                confirmField.after(matchIndicator);
            }

            var matchIndicator = confirmField.siblings('.password-match');
            
            if (isMatch) {
                matchIndicator.removeClass('invalid').addClass('valid');
                matchIndicator.html('<i class="fas fa-check"></i> Mật khẩu khớp');
            } else {
                matchIndicator.removeClass('valid').addClass('invalid');
                matchIndicator.html('<i class="fas fa-times"></i> Mật khẩu không khớp');
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
                successDiv = $('<div class="success-message">✓ Hợp lệ</div>');
                input.after(successDiv);
            }
            input.removeClass('error').addClass('success');
        },

        _hideMessages: function (input) {
            input.siblings('.error-message, .success-message').remove();
            input.removeClass('error success');
        },

        _onSubmitForm: function (e) {
            var nameInput = this.$('#name');
            var emailInput = this.$('#email');
            var passwordInput = this.$('#password');
            var confirmInput = this.$('#confirm_password');
            var termsCheckbox = this.$('input[name="terms"]');
            
            var isNameValid = this._validateName(nameInput);
            var isEmailValid = this._validateEmail(emailInput);
            var isPasswordValid = this._validatePassword(passwordInput);
            var isConfirmValid = this._validateConfirmPassword(confirmInput);
            var isTermsAccepted = termsCheckbox.is(':checked');
            
            if (!isTermsAccepted) {
                this._showTermsError();
                e.preventDefault();
                return false;
            }
            
            if (!isNameValid || !isEmailValid || !isPasswordValid || !isConfirmValid) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            var submitButton = this.$('.login-button');
            var originalText = submitButton.text();
            submitButton.text('Đang đăng ký...').prop('disabled', true);
            
            // Re-enable after a delay (in case of error)
            setTimeout(function () {
                submitButton.text(originalText).prop('disabled', false);
            }, 3000);
        },

        _showTermsError: function () {
            var termsCheckbox = this.$('input[name="terms"]');
            var errorDiv = termsCheckbox.closest('.form-options').find('.error-message');
            
            if (errorDiv.length === 0) {
                errorDiv = $('<div class="error-message">Vui lòng đồng ý với điều khoản sử dụng</div>');
                termsCheckbox.closest('.form-options').append(errorDiv);
            }
        },

        _onTogglePassword: function (e) {
            e.preventDefault();
            this._togglePasswordVisibility($(e.currentTarget));
        },

        _onSocialSignup: function (e) {
            e.preventDefault();
            var provider = $(e.currentTarget).data('provider');
            
            // Show loading state
            var button = $(e.currentTarget);
            var originalContent = button.html();
            button.html('<i class="fas fa-spinner fa-spin"></i>').prop('disabled', true);
            
            // Simulate social signup (replace with actual implementation)
            setTimeout(function () {
                button.html(originalContent).prop('disabled', false);
                console.log('Social signup with:', provider);
            }, 2000);
        },

        _onPasswordInput: function (e) {
            this._checkPasswordStrength($(e.target).val());
            this._checkPasswordMatch();
        },

        _onConfirmPasswordInput: function (e) {
            this._checkPasswordMatch();
        },

        _onNameInput: function (e) {
            var input = $(e.target);
            if (input.val().trim()) {
                this._hideMessages(input);
            }
        },

        _onEmailInput: function (e) {
            var input = $(e.target);
            if (input.val().trim()) {
                this._hideMessages(input);
            }
        }
    });

    return publicWidget.registry.CustomSignup;
}); 