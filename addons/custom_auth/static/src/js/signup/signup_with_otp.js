odoo.define('custom_auth.signup_with_otp', function (require) {
    'use strict';

    console.log('Loading CustomSignupWithOTP widget...');

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.CustomSignupWithOTP = publicWidget.Widget.extend({
        selector: '[data-js="custom-signup"]',
        events: {
            'click .password-toggle': '_onTogglePassword',
            'submit #signup-form': '_onSubmitForm',
            'input #password': '_onPasswordInput',
            'input #confirm_password': '_onConfirmPasswordInput',
            'input #name': '_onNameInput',
            'input #email': '_onEmailInput',
            'click #close-otp-popup': '_onCloseOTPPopup',
            'click #verify-otp': '_onVerifyOTP',
            'click #resend-otp': '_onResendOTP',
            'input .otp-input': '_onOTPInput',
            'keydown .otp-input': '_onOTPKeydown'
        },

        start: function () {
            console.log('CustomSignupWithOTP widget starting...');
            this._super.apply(this, arguments);
            this._initPasswordStrength();
            this._initFormValidation();
            this._initPasswordToggle();
            this._initOTPPopup();
            console.log('CustomSignupWithOTP widget started successfully');
            return this;
        },

        _initOTPPopup: function () {
            console.log('Initializing OTP popup...');
            this.otpPopup = this.$('#otp-popup');
            this.otpInputs = this.$('.otp-input');
            this.otpError = this.$('#otp-error');
            this.otpLoading = this.$('#otp-loading');
            this.otpTimer = this.$('#otp-timer');
            this.otpEmail = this.$('#otp-email');
            this.verifyButton = this.$('#verify-otp');
            this.resendButton = this.$('#resend-otp');
            
            console.log('OTP popup elements found:', {
                popup: this.otpPopup.length,
                inputs: this.otpInputs.length,
                error: this.otpError.length,
                loading: this.otpLoading.length,
                timer: this.otpTimer.length,
                email: this.otpEmail.length,
                verify: this.verifyButton.length,
                resend: this.resendButton.length
            });
            
            this.timerInterval = null;
            this.countdown = 300; // 5 minutes
        },

        _initPasswordToggle: function () {
            var self = this;
            this.$el.on('click', '[data-action="toggle-password"]', function (e) {
                e.preventDefault();
                e.stopPropagation();
                self._togglePasswordVisibility($(this));
            });
        },

        _togglePasswordVisibility: function (toggleButton) {
            var passwordInput = toggleButton.siblings('input[type="password"], input[type="text"]');
            var icon = toggleButton.find('i');
            
            if (passwordInput.attr('type') === 'password') {
                passwordInput.attr('type', 'text');
                icon.removeClass('fa-eye-slash').addClass('fa-eye');
                toggleButton.attr('aria-label', 'Ẩn mật khẩu');
                
                setTimeout(function () {
                    if (passwordInput.attr('type') === 'text') {
                        passwordInput.attr('type', 'password');
                        icon.removeClass('fa-eye').addClass('fa-eye-slash');
                        toggleButton.attr('aria-label', 'Hiển thị mật khẩu');
                    }
                }, 3000);
                
            } else {
                passwordInput.attr('type', 'password');
                icon.removeClass('fa-eye').addClass('fa-eye-slash');
                toggleButton.attr('aria-label', 'Hiển thị mật khẩu');
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
            if (password.length >= 8) strength += 1;
            if (password.length >= 12) strength += 1;
            if (/[a-z]/.test(password)) strength += 1;
            if (/[A-Z]/.test(password)) strength += 1;
            if (/[0-9]/.test(password)) strength += 1;
            if (/[^A-Za-z0-9]/.test(password)) strength += 1;

            var strengthLevel = 'weak';
            var strengthText = 'Yếu';
            if (strength >= 5) {
                strengthLevel = 'strong';
                strengthText = 'Mạnh';
            } else if (strength >= 4) {
                strengthLevel = 'good';
                strengthText = 'Tốt';
            } else if (strength >= 3) {
                strengthLevel = 'fair';
                strengthText = 'Trung bình';
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
                errorDiv = $('<div class="error-message text-red-500 text-sm mt-1"></div>');
                input.after(errorDiv);
            }
            errorDiv.text(message);
            input.removeClass('border-green-500').addClass('border-red-500');
        },

        _showSuccess: function (input) {
            var errorDiv = input.siblings('.error-message');
            errorDiv.remove();
            input.removeClass('border-red-500').addClass('border-green-500');
        },

        _onSubmitForm: function (e) {
            console.log('Form submit intercepted by OTP widget');
            e.preventDefault();
            e.stopPropagation();
            
            var nameInput = this.$('#name');
            var emailInput = this.$('#email');
            var passwordInput = this.$('#password');
            var confirmInput = this.$('#confirm_password');
            var termsCheckbox = this.$('input[name="terms"]');
            
            console.log('Validating form...');
            var isNameValid = this._validateName(nameInput);
            var isEmailValid = this._validateEmail(emailInput);
            var isPasswordValid = this._validatePassword(passwordInput);
            var isConfirmValid = this._validateConfirmPassword(confirmInput);
            var isTermsAccepted = termsCheckbox.is(':checked');
            
            console.log('Validation results:', {
                name: isNameValid,
                email: isEmailValid,
                password: isPasswordValid,
                confirm: isConfirmValid,
                terms: isTermsAccepted
            });
            
            if (!isTermsAccepted) {
                this._showTermsError();
                return false;
            }
            
            if (!isNameValid || !isEmailValid || !isPasswordValid || !isConfirmValid) {
                console.log('Form validation failed');
                return false;
            }
            
            // Collect form data
            var formData = {
                name: nameInput.val().trim(),
                email: emailInput.val().trim(),
                phone: this.$('#phone').val().trim(),
                password: passwordInput.val(),
                confirm_password: confirmInput.val()
            };
            
            console.log('Sending OTP request with data:', formData);
            
            // Show loading state
            var submitButton = this.$('#signup-submit');
            var originalText = submitButton.text();
            submitButton.text('Đang gửi OTP...').prop('disabled', true);
            
            // Send OTP
            this._sendOTP(formData, submitButton, originalText);
        },

        _sendOTP: function (formData, submitButton, originalText) {
            var self = this;
            console.log('Making AJAX call to send OTP...');
            
            ajax.jsonRpc('/web/signup/otp', 'call', formData)
                .then(function (result) {
                    console.log('OTP response:', result);
                    if (result.success) {
                        self._showOTPPopup(formData.email, formData);
                        submitButton.text(originalText).prop('disabled', false);
                    } else {
                        self._showFormError(result.message);
                        submitButton.text(originalText).prop('disabled', false);
                    }
                })
                .fail(function (error) {
                    console.error('OTP request failed:', error);
                    self._showFormError('Có lỗi xảy ra khi gửi OTP');
                    submitButton.text(originalText).prop('disabled', false);
                });
        },

        _showOTPPopup: function (email, formData) {
            console.log('Showing OTP popup for email:', email);
            this.otpEmail.text(email);
            this.formData = formData;
            this.otpPopup.removeClass('hidden');
            this._startOTPTimer();
            this._focusFirstOTPInput();
        },

        _onCloseOTPPopup: function (e) {
            e.preventDefault();
            this._hideOTPPopup();
        },

        _hideOTPPopup: function () {
            this.otpPopup.addClass('hidden');
            this._stopOTPTimer();
            this._clearOTPInputs();
            this._hideOTPError();
        },

        _onOTPInput: function (e) {
            var input = $(e.target);
            var value = input.val();
            var index = parseInt(input.data('index'));
            
            // Only allow numbers
            if (!/^\d*$/.test(value)) {
                input.val('');
                return;
            }
            
            // Move to next input
            if (value && index < 5) {
                this.otpInputs.eq(index + 1).focus();
            }
            
            this._updateVerifyButton();
        },

        _onOTPKeydown: function (e) {
            var input = $(e.target);
            var index = parseInt(input.data('index'));
            
            // Move to previous input on backspace
            if (e.key === 'Backspace' && !input.val() && index > 0) {
                this.otpInputs.eq(index - 1).focus();
            }
        },

        _updateVerifyButton: function () {
            var otp = this._getOTPValue();
            this.verifyButton.prop('disabled', otp.length !== 6);
        },

        _getOTPValue: function () {
            var otp = '';
            this.otpInputs.each(function () {
                otp += $(this).val();
            });
            return otp;
        },

        _onVerifyOTP: function (e) {
            e.preventDefault();
            
            var otp = this._getOTPValue();
            if (otp.length !== 6) {
                this._showOTPError('Vui lòng nhập đầy đủ 6 số OTP');
                return;
            }
            
            this._showOTPLoading(true);
            this.verifyButton.prop('disabled', true);
            
            var self = this;
            ajax.jsonRpc('/web/signup/verify-otp', 'call', {otp: otp})
                .then(function (result) {
                    if (result.success) {
                        self._showSuccessMessage(result.message);
                        setTimeout(function () {
                            window.location.href = result.redirect_url;
                        }, 2000);
                    } else {
                        self._showOTPError(result.message);
                        self._showOTPLoading(false);
                        self.verifyButton.prop('disabled', false);
                    }
                })
                .fail(function (error) {
                    self._showOTPError('Có lỗi xảy ra khi xác thực OTP');
                    self._showOTPLoading(false);
                    self.verifyButton.prop('disabled', false);
                });
        },

        _onResendOTP: function (e) {
            e.preventDefault();
            
            if (this.resendButton.prop('disabled')) {
                return;
            }
            
            this.resendButton.prop('disabled', true);
            this._clearOTPInputs();
            this._hideOTPError();
            
            var self = this;
            ajax.jsonRpc('/web/signup/otp', 'call', this.formData)
                .then(function (result) {
                    if (result.success) {
                        self._startOTPTimer();
                        self._focusFirstOTPInput();
                    } else {
                        self._showOTPError(result.message);
                    }
                    self.resendButton.prop('disabled', false);
                })
                .fail(function (error) {
                    self._showOTPError('Có lỗi xảy ra khi gửi lại OTP');
                    self.resendButton.prop('disabled', false);
                });
        },

        _startOTPTimer: function () {
            this.countdown = 300; // 5 minutes
            this._updateTimer();
            
            this.timerInterval = setInterval(function () {
                this.countdown--;
                this._updateTimer();
                
                if (this.countdown <= 0) {
                    this._stopOTPTimer();
                    this._showOTPError('Mã OTP đã hết hạn. Vui lòng gửi lại.');
                }
            }.bind(this), 1000);
        },

        _stopOTPTimer: function () {
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        },

        _updateTimer: function () {
            var minutes = Math.floor(this.countdown / 60);
            var seconds = this.countdown % 60;
            this.otpTimer.text(
                (minutes < 10 ? '0' : '') + minutes + ':' + 
                (seconds < 10 ? '0' : '') + seconds
            );
        },

        _focusFirstOTPInput: function () {
            this.otpInputs.first().focus();
        },

        _clearOTPInputs: function () {
            this.otpInputs.val('');
            this._updateVerifyButton();
        },

        _showOTPError: function (message) {
            this.otpError.text(message).removeClass('hidden');
        },

        _hideOTPError: function () {
            this.otpError.addClass('hidden');
        },

        _showOTPLoading: function (show) {
            if (show) {
                this.otpLoading.removeClass('hidden');
            } else {
                this.otpLoading.addClass('hidden');
            }
        },

        _showFormError: function (message) {
            // Show error message in form
            var errorDiv = this.$('#signup-form').find('.form-error');
            if (errorDiv.length === 0) {
                errorDiv = $('<div class="form-error text-red-500 text-sm mt-2 text-center"></div>');
                this.$('#signup-form').prepend(errorDiv);
            }
            errorDiv.text(message);
        },

        _showSuccessMessage: function (message) {
            this.otpPopup.find('.bg-gradient-to-r').removeClass('from-blue-600 to-blue-700').addClass('from-green-600 to-green-700');
            this.otpPopup.find('h3').text('Thành công!');
            this.otpPopup.find('p').text(message);
            this.otpLoading.html('<div class="inline-flex items-center text-green-600"><i class="fas fa-check mr-2"></i>' + message + '</div>').removeClass('hidden');
        },

        _showTermsError: function () {
            var termsCheckbox = this.$('input[name="terms"]');
            var errorDiv = termsCheckbox.closest('div').find('.error-message');
            
            if (errorDiv.length === 0) {
                errorDiv = $('<div class="error-message text-red-500 text-sm mt-1">Vui lòng đồng ý với điều khoản sử dụng</div>');
                termsCheckbox.closest('div').append(errorDiv);
            }
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
                input.siblings('.error-message').remove();
                input.removeClass('border-red-500');
            }
        },

        _onEmailInput: function (e) {
            var input = $(e.target);
            if (input.val().trim()) {
                input.siblings('.error-message').remove();
                input.removeClass('border-red-500');
            }
        }
    });

    console.log('CustomSignupWithOTP widget defined successfully');
    return publicWidget.registry.CustomSignupWithOTP;
}); 