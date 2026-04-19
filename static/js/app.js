document.addEventListener('DOMContentLoaded', () => {
    const panels = document.querySelectorAll('.glass-panel');
    const hero = document.getElementById('hero');
    const closeBtns = document.querySelectorAll('[data-action="close"]');
    const navLinks = document.querySelectorAll('nav a[data-target]');

    let lastFocusedLink = null;

    function updateView() {
        const hash = window.location.hash.substring(1);

        let found = false;
        panels.forEach(p => {
            if (p.id === `panel-${hash}`) {
                p.classList.add('active');
                found = true;
                // Move focus to panel heading for accessibility
                const heading = p.querySelector('h2');
                if (heading) {
                    heading.setAttribute('tabindex', '-1');
                    heading.focus();
                }
            } else {
                p.classList.remove('active');
            }
        });

        navLinks.forEach(a => {
            a.classList.toggle('active', a.dataset.target === hash);
        });

        if (found) {
            hero.style.display = 'none';
        } else {
            hero.style.display = 'block';
            history.replaceState(null, null, ' ');
            // Return focus to the link that opened the panel
            if (lastFocusedLink) {
                lastFocusedLink.focus();
                lastFocusedLink = null;
            }
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            lastFocusedLink = link;
        });
    });

    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            window.location.hash = '';
        });
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && window.location.hash) {
            window.location.hash = '';
        }
    });

    window.addEventListener('hashchange', updateView);
    updateView();

    // AJAX form submission
    const form = document.getElementById('contact-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const msgBox = document.getElementById('form-msg');
            msgBox.hidden = true;
            msgBox.className = 'form-msg';

            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            if (!data['g-recaptcha-response']) {
                showMsg(msgBox, 'error', 'Please wait for reCAPTCHA to load and try again.');
                return;
            }

            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn.textContent;
            btn.textContent = 'Sending...';
            btn.disabled = true;

            try {
                const res = await fetch('/submit_form', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await res.json();

                if (res.ok) {
                    showMsg(msgBox, 'success', 'Message sent successfully. Thank you!');
                    form.reset();
                    if (typeof grecaptcha !== 'undefined' && grecaptcha.enterprise) {
                        grecaptcha.enterprise.reset();
                    }
                } else {
                    showMsg(msgBox, 'error', result.message || 'Something went wrong.');
                }
            } catch (err) {
                showMsg(msgBox, 'error', 'Network error. Please try again.');
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
    }

    function showMsg(el, type, text) {
        el.className = `form-msg ${type}`;
        el.textContent = text;
        el.hidden = false;
    }
});
