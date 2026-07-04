document.addEventListener('DOMContentLoaded', () => {
    // Redirect if already logged in
    if (api.isLoggedIn()) {
        window.location.href = '/dashboard';
        return;
    }

    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');

    // Switch Tab Logic
    tabLogin.addEventListener('click', () => {
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        formLogin.style.display = 'block';
        formRegister.style.display = 'none';
        clearErrors();
    });

    tabRegister.addEventListener('click', () => {
        tabRegister.classList.add('active');
        tabLogin.classList.remove('active');
        formRegister.style.display = 'block';
        formLogin.style.display = 'none';
        clearErrors();
    });

    // Login Form Submit
    formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = formLogin.username.value.trim();
        const password = formLogin.password.value;

        if (!username || !password) {
            showError('form-login', 'Please fill in all fields');
            return;
        }

        setLoading(formLogin, true);

        try {
            await api.login(username, password);
            showToast('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } catch (error) {
            setLoading(formLogin, false);
            showError('form-login', error.message || 'Invalid username or password');
        }
    });

    // Register Form Submit
    formRegister.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = formRegister.username.value.trim();
        const email = formRegister.email.value.trim();
        const password = formRegister.password.value;
        const confirmPassword = formRegister.confirmPassword.value;

        if (!username || !email || !password || !confirmPassword) {
            showError('form-register', 'Please fill in all fields');
            return;
        }

        if (password !== confirmPassword) {
            showError('form-register', 'Passwords do not match');
            return;
        }

        if (password.length < 6) {
            showError('form-register', 'Password must be at least 6 characters');
            return;
        }

        setLoading(formRegister, true);

        try {
            await api.register(username, email, password);
            showToast('Registration successful! Please login.', 'success');
            setLoading(formRegister, false);
            formRegister.reset();
            tabLogin.click();
        } catch (error) {
            setLoading(formRegister, false);
            showError('form-register', error.message || 'Registration failed');
        }
    });

    // Helpers
    function showError(formId, message) {
        const form = document.getElementById(formId);
        let errorDiv = form.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message alert alert-danger';
            form.prepend(errorDiv);
        }
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    function clearErrors() {
        document.querySelectorAll('.error-message').forEach(el => {
            el.style.display = 'none';
            el.textContent = '';
        });
    }

    function setLoading(form, isLoading) {
        const btn = form.querySelector('button[type="submit"]');
        if (isLoading) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Loading...';
        } else {
            btn.disabled = false;
            if (form.id === 'form-login') {
                btn.innerHTML = 'Sign In';
            } else {
                btn.innerHTML = 'Register';
            }
        }
    }

    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast-message toast-${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
});
