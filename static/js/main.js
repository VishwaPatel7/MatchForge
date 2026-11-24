// MatchForge Universal JavaScript Utilities

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0 show`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.marginBottom = '0.5rem';

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4500);
}

// Toggle Opportunity Bookmark
async function toggleSaveOpportunity(oppId, btnElement) {
    try {
        const resp = await fetch(`/api/v1/opportunities/${oppId}/save/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            }
        });
        const data = await resp.json();
        if (resp.ok) {
            if (data.saved) {
                btnElement.innerHTML = '<i class="bi bi-bookmark-fill text-primary"></i> Saved';
                showToast("Opportunity bookmarked!", "success");
            } else {
                btnElement.innerHTML = '<i class="bi bi-bookmark"></i> Save';
                showToast("Removed from bookmarks.", "info");
            }
        } else {
            showToast(data.error || "Failed to update bookmark.", "error");
        }
    } catch (err) {
        showToast("Network error. Please try again.", "error");
    }
}
