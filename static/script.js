let currentJobId = null;
let pollInterval = null;
const form = document.getElementById('generateForm');
const generateBtn = document.getElementById('generateBtn');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const statusBadge = document.getElementById('statusBadge');
const progressPercent = document.getElementById('progressPercent');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultVideo = document.getElementById('resultVideo');
const downloadVideo = document.getElementById('downloadVideo');
const downloadThumbnail = document.getElementById('downloadThumbnail');
const newVideoBtn = document.getElementById('newVideoBtn');
const historyList = document.getElementById('historyList');
const refreshHistory = document.getElementById('refreshHistory');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = document.getElementById('prompt').value;
    const size = document.getElementById('size').value;
    const duration = parseInt(document.getElementById('duration').value);
    generateBtn.disabled = true;
    generateBtn.textContent = 'Starting...';
    resultSection.style.display = 'none';
    progressSection.style.display = 'block';
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt, size, duration })
        });
        const data = await response.json();
        if (response.ok) {
            currentJobId = data.job_id;
            startPolling();
        } else {
            throw new Error(data.error || 'Failed');
        }
    } catch (error) {
        alert('Error: ' + error.message);
        resetForm();
    }
});

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${currentJobId}`);
            const job = await response.json();
            updateProgress(job);
            if (job.status === 'completed') {
                stopPolling();
                showResult(job);
                loadHistory();
            } else if (job.status === 'failed') {
                stopPolling();
                alert('Failed: ' + job.error);
                resetForm();
                loadHistory();
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function updateProgress(job) {
    statusBadge.textContent = job.status.replace('_', ' ');
    statusBadge.className = 'status-badge ' + job.status;
    const progress = job.progress || 0;
    progressPercent.textContent = Math.round(progress) + '%';
    progressFill.style.width = progress + '%';
    progressText.textContent = 'Processing...';
}

function showResult(job) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    resultVideo.src = `/download/${job.id}/video`;
    downloadVideo.onclick = () => window.location.href = `/download/${job.id}/video`;
    downloadThumbnail.onclick = () => window.location.href = `/download/${job.id}/thumbnail`;
}

newVideoBtn.addEventListener('click', () => {
    resetForm();
    document.getElementById('prompt').focus();
});

function resetForm() {
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate Video';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
}

async function loadHistory() {
    try {
        const response = await fetch('/history');
        const jobs = await response.json();
        if (jobs.length === 0) {
            historyList.innerHTML = '<p class="empty-state">No videos yet</p>';
            return;
        }
        historyList.innerHTML = jobs.map(job => `
            <div class="history-item" onclick="loadHistoryItem('${job.id}')">
                <div class="history-item-prompt">${escapeHtml(job.prompt)}</div>
                <div class="history-item-meta">
                    <span>${job.size} • ${job.duration}s</span>
                    <span class="status-badge ${job.status}">${job.status}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function loadHistoryItem(jobId) {
    currentJobId = jobId;
    fetch(`/status/${jobId}`)
        .then(r => r.json())
        .then(job => {
            if (job.status === 'completed') {
                showResult(job);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

refreshHistory.addEventListener('click', loadHistory);
loadHistory();
setInterval(loadHistory, 30000);