document.addEventListener('DOMContentLoaded', function() {
    const testBtn = document.getElementById('test-connection');
    const saveBtn = document.getElementById('save-button');
    const spinner = document.getElementById('test-spinner');
    const statusDiv = document.getElementById('connection-status');
    const form = document.getElementById('connector-form');

    testBtn.addEventListener('click', async function() {
        // Show loading spinner
        spinner.classList.remove('d-none');
        testBtn.disabled = true;
        statusDiv.innerHTML = '';
        
        try {
            const formData = new FormData(form);
            // Get CSRF token from the hidden input field
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;

            // Correct URL including the blueprint prefix
            const response = await fetch('/connectors/api/test-db-connection', {
                method: 'POST',
                body: formData,
                headers: {
                    // Add CSRF token to request headers
                    'X-CSRFToken': csrfToken
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                statusDiv.innerHTML = '<span class="text-success">✔ Connection successful!</span>';
                saveBtn.disabled = false;
            } else {
                statusDiv.innerHTML = `<span class="text-danger">✖ Connection failed: ${result.error}</span>`;
                saveBtn.disabled = true;
            }
        } catch (error) {
            statusDiv.innerHTML = '<span class="text-danger">✖ Error testing connection</span>';
            saveBtn.disabled = true;
        } finally {
            spinner.classList.add('d-none');
            testBtn.disabled = false;
        }
    });

    // Disable save button if form changes after successful test
    form.addEventListener('input', function() {
        if (!saveBtn.disabled) {
            saveBtn.disabled = true;
            statusDiv.innerHTML = '<span class="text-warning">⚠ Please test connection again</span>';
        }
    });
});
