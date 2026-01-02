const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('loginBtn');
        const errorMsg = document.getElementById('errorMessage');
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        btn.disabled = true;
        btn.textContent = 'Signing in...';
        errorMsg.classList.remove('show');
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok) {
                window.location.href = data.redirect;
            } else {
                errorMsg.textContent = data.error || 'Login failed';
                errorMsg.classList.add('show');
                btn.disabled = false;
                btn.textContent = 'Sign In';
            }
        } catch (error) {
            errorMsg.textContent = 'Network error';
            errorMsg.classList.add('show');
            btn.disabled = false;
            btn.textContent = 'Sign In';
        }
    });
}

if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('registerBtn');
        const errorMsg = document.getElementById('errorMessage');
        const username = document.getElementById('username').value;
        const display_name = document.getElementById('display_name').value;
        const password = document.getElementById('password').value;
        const confirm_password = document.getElementById('confirm_password').value;
        btn.disabled = true;
        btn.textContent = 'Creating...';
        errorMsg.classList.remove('show');
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username, display_name, password, confirm_password })
            });
            const data = await response.json();
            if (response.ok) {
                window.location.href = data.redirect;
            } else {
                errorMsg.textContent = data.error || 'Registration failed';
                errorMsg.classList.add('show');
                btn.disabled = false;
                btn.textContent = 'Create Account';
            }
        } catch (error) {
            errorMsg.textContent = 'Network error';
            errorMsg.classList.add('show');
            btn.disabled = false;
            btn.textContent = 'Create Account';
        }
    });
}