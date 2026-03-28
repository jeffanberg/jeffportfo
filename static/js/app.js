document.addEventListener('DOMContentLoaded', () => {
    const panels = document.querySelectorAll('.glass-panel');
    const hero = document.getElementById('hero');
    const closeBtns = document.querySelectorAll('[data-action="close"]');

    function updateView() {
        const hash = window.location.hash.substring(1);
        
        let found = false;
        panels.forEach(p => {
            if (p.id === `panel-${hash}`) {
                p.classList.add('active');
                found = true;
            } else {
                p.classList.remove('active');
            }
        });

        if (found) {
            hero.style.display = 'none';
        } else {
            hero.style.display = 'block';
            history.replaceState(null, null, ' '); // remove hash cleanly
        }
    }

    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            window.location.hash = '';
        });
    });

    window.addEventListener('hashchange', updateView);
    updateView(); // Initial call to handle direct links

    // AJAX form submission
    const form = document.getElementById('contact-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const msgBox = document.getElementById('form-msg');
            msgBox.style.display = 'none';
            
            const btn = form.querySelector('button[type="submit"]');
            const originalText = btn.textContent;
            btn.textContent = 'Sending...';
            btn.disabled = true;

            grecaptcha.enterprise.ready(async () => {
                try {
                    const token = await grecaptcha.enterprise.execute('6Lf_GJwsAAAAACLncXT--_qoUYj2n83Nc9eXBZ02', {action: 'contact_form_submit'});
                    const formData = new FormData(form);
                    const data = Object.fromEntries(formData.entries());
                    
                    data['g-recaptcha-response'] = token;

                    try {
                        const res = await fetch('/submit_form', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(data)
                        });
                        
                        const result = await res.json();
                        
                        msgBox.style.display = 'block';
                        if (res.ok) {
                            msgBox.style.backgroundColor = 'rgba(34, 197, 94, 0.2)';
                            msgBox.style.color = '#86efac';
                            msgBox.textContent = 'Message sent successfully. Thank you!';
                            form.reset();
                        } else {
                            msgBox.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                            msgBox.style.color = '#fca5a5';
                            msgBox.textContent = result.message || 'Something went wrong.';
                        }
                    } catch (err) {
                        msgBox.style.display = 'block';
                        msgBox.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                        msgBox.style.color = '#fca5a5';
                        msgBox.textContent = 'Network error. Please try again.';
                    } finally {
                        btn.textContent = originalText;
                        btn.disabled = false;
                    }
                } catch (err) {
                    msgBox.style.display = 'block';
                    msgBox.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                    msgBox.style.color = '#fca5a5';
                    msgBox.textContent = 'reCAPTCHA initialization failed. Please try again.';
                    btn.textContent = originalText;
                    btn.disabled = false;
                }
            });
        });
    }
});
