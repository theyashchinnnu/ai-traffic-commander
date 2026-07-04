document.addEventListener('DOMContentLoaded', () => {
    // Check Auth
    if (!api.isLoggedIn()) {
        window.location.href = '/';
        return;
    }

    // Elements
    const currentUserSpan = document.getElementById('current-user');
    const btnLogout = document.getElementById('btn-logout');
    const formIncident = document.getElementById('form-incident');
    const historyList = document.getElementById('history-list');
    const apiKeysList = document.getElementById('api-keys-list');
    const btnGenerateKey = document.getElementById('btn-generate-key');
    const maskKeyVal = document.getElementById('mask-key-val');
    const btnCopyKey = document.getElementById('btn-copy-key');
    const pipelineSteps = document.querySelectorAll('.pipeline-step');
    
    // Sample Incident Buttons
    const btnSample1 = document.getElementById('btn-sample-1');
    const btnSample2 = document.getElementById('btn-sample-2');
    const btnSample3 = document.getElementById('btn-sample-3');

    // Agent Result Containers
    const resultsGrid = document.getElementById('results-grid');
    const cardMonitor = document.getElementById('card-monitor');
    const cardCongestion = document.getElementById('card-congestion');
    const cardRAG = document.getElementById('card-rag');
    const cardRoutes = document.getElementById('card-routes');
    const cardSignals = document.getElementById('card-signals');
    const cardNotifs = document.getElementById('card-notifs');

    // Init User Display
    const user = api.getUser();
    if (user) {
        currentUserSpan.textContent = user.username;
    }

    // Masked primary key loader
    const primaryKey = localStorage.getItem('tc_api_key');
    if (primaryKey) {
        maskKeyVal.textContent = primaryKey.substring(0, 8) + '...' + primaryKey.substring(primaryKey.length - 6);
        btnCopyKey.addEventListener('click', () => {
            navigator.clipboard.writeText(primaryKey);
            showToast('API Key copied to clipboard!', 'success');
        });
    }

    // Load Initial Data
    loadHistory();
    loadApiKeys();

    // Logout
    btnLogout.addEventListener('click', () => {
        api.logout();
        window.location.href = '/';
    });

    // Sample Incident Fillers
    const SAMPLES = {
        sample1: {
            desc: "Major multi-vehicle accident on NH-48 near Gurugram toll plaza during heavy rain. 3 lanes blocked, multiple injuries reported. Heavy traffic buildup. Time: 8:30 AM.",
            loc: "NH-48 near Gurugram toll plaza",
            type: "Accident"
        },
        sample2: {
            desc: "Waterlogging on MG Road Bangalore near Trinity Circle. 2 lanes submerged. Traffic diverted. Moderate rainfall continuing. Time: 5:00 PM.",
            loc: "MG Road near Trinity Circle, Bangalore",
            type: "Flood"
        },
        sample3: {
            desc: "Chemical tanker overturned on Mumbai-Pune Expressway near Lonavala. Hazmat spill reported. All lanes blocked. Emergency services en route. Time: 2:15 PM.",
            loc: "Mumbai-Pune Expressway near Lonavala",
            type: "Road Block"
        }
    };

    btnSample1.addEventListener('click', () => fillSample(SAMPLES.sample1));
    btnSample2.addEventListener('click', () => fillSample(SAMPLES.sample2));
    btnSample3.addEventListener('click', () => fillSample(SAMPLES.sample3));

    function fillSample(sample) {
        formIncident.description.value = sample.desc;
        formIncident.location.value = sample.loc;
        formIncident.incident_type.value = sample.type;
        showToast('Sample details loaded. Click Analyze!', 'info');
    }

    // Generate API Key
    btnGenerateKey.addEventListener('click', async () => {
        const keyName = prompt("Enter a name for this API key:", "New Key");
        if (keyName === null) return;
        try {
            const result = await api.createApiKey(keyName || "Default Key");
            alert(`Your new API key is:\n\n${result.api_key}\n\nCopy and save it now! It will not be shown again.`);
            loadApiKeys();
        } catch (error) {
            showToast(error.message, 'danger');
        }
    });

    // Submit Incident Form
    formIncident.addEventListener('submit', async (e) => {
        e.preventDefault();
        const description = formIncident.description.value.trim();
        const location = formIncident.location.value.trim() || null;
        const incidentType = formIncident.incident_type.value || null;

        if (description.length < 10) {
            showToast('Description must be at least 10 characters long.', 'warning');
            return;
        }

        // UI Reset
        resetPipeline();
        hideResultCards();
        setLoadingState(true);

        // Start Pipeline Progress Simulation
        const pipelineInterval = animatePipeline();

        try {
            const data = await api.analyzeIncident(description, location, incidentType);
            clearInterval(pipelineInterval);
            completePipeline();
            renderResults(data.results);
            loadHistory();
            showToast('Incident analysis completed!', 'success');
        } catch (error) {
            clearInterval(pipelineInterval);
            failPipeline();
            showToast(error.message || 'Error processing incident analysis.', 'danger');
        } finally {
            setLoadingState(false);
        }
    });

    // History and Key management functions
    async function loadHistory() {
        try {
            const history = await api.getHistory();
            historyList.innerHTML = '';
            if (history.length === 0) {
                historyList.innerHTML = '<li class="list-group-item bg-transparent text-muted text-center border-0 py-3">No incident history yet.</li>';
                return;
            }
            history.forEach(item => {
                const li = document.createElement('li');
                li.className = 'list-group-item bg-transparent border-bottom border-secondary text-light d-flex justify-content-between align-items-center py-3 history-item';
                li.style.cursor = 'pointer';
                
                const time = new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const date = new Date(item.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' });
                const type = item.incident_type || 'General';
                
                let badgeClass = 'bg-secondary';
                if (item.status === 'completed') badgeClass = 'bg-success';
                if (item.status === 'error') badgeClass = 'bg-danger';
                if (item.status === 'processing') badgeClass = 'bg-warning text-dark';

                li.innerHTML = `
                    <div class="overflow-hidden me-2">
                        <div class="fw-bold text-truncate">${item.description}</div>
                        <small class="text-muted">${type} | ${date} ${time}</small>
                    </div>
                    <span class="badge ${badgeClass}">${item.status}</span>
                `;

                li.addEventListener('click', async () => {
                    if (item.status !== 'completed') {
                        showToast(`This incident is ${item.status}. Cannot view results.`, 'warning');
                        return;
                    }
                    try {
                        showToast('Loading incident analysis...', 'info');
                        const fullIncident = await api.getIncident(item.id);
                        completePipeline();
                        renderResults(fullIncident.results);
                    } catch (error) {
                        showToast('Failed to load incident details.', 'danger');
                    }
                });

                historyList.appendChild(li);
            });
        } catch (error) {
            console.error('History load failed:', error);
        }
    }

    async function loadApiKeys() {
        try {
            const keys = await api.getApiKeys();
            apiKeysList.innerHTML = '';
            if (keys.length === 0) {
                apiKeysList.innerHTML = '<li class="list-group-item bg-transparent text-muted text-center border-0">No custom API keys generated yet.</li>';
                return;
            }
            keys.forEach(k => {
                const li = document.createElement('li');
                li.className = 'list-group-item bg-transparent border-bottom border-secondary text-light d-flex justify-content-between align-items-center py-2';
                
                const statusBadge = k.is_active ? '<span class="badge bg-success-glow text-success">Active</span>' : '<span class="badge bg-danger-glow text-danger">Revoked</span>';
                const revokeBtn = k.is_active ? `<button class="btn btn-sm btn-outline-danger btn-revoke" data-id="${k.id}">Revoke</button>` : '';

                li.innerHTML = `
                    <div>
                        <div class="fw-bold">${k.name}</div>
                        <small class="text-muted">Prefix: ${k.key_prefix} | ${statusBadge}</small>
                    </div>
                    <div>${revokeBtn}</div>
                `;

                const btn = li.querySelector('.btn-revoke');
                if (btn) {
                    btn.addEventListener('click', async () => {
                        if (confirm(`Are you sure you want to revoke the API key "${k.name}"?`)) {
                            try {
                                await api.revokeApiKey(k.id);
                                showToast('API key revoked successfully.', 'success');
                                loadApiKeys();
                            } catch (error) {
                                showToast(error.message, 'danger');
                            }
                        }
                    });
                }

                apiKeysList.appendChild(li);
            });
        } catch (error) {
            console.error('API key list load failed:', error);
        }
    }

    // Pipeline Animation / Management
    function resetPipeline() {
        pipelineSteps.forEach(step => {
            step.className = 'pipeline-step pending';
        });
    }

    function animatePipeline() {
        let currentStep = 0;
        pipelineSteps[currentStep].className = 'pipeline-step processing';
        
        return setInterval(() => {
            pipelineSteps[currentStep].className = 'pipeline-step completed';
            currentStep = (currentStep + 1) % pipelineSteps.length;
            pipelineSteps[currentStep].className = 'pipeline-step processing';
        }, 15000); // Wait 15s before transitioning steps in simulator (Crew takes ~60-90s)
    }

    function completePipeline() {
        pipelineSteps.forEach(step => {
            step.className = 'pipeline-step completed';
        });
    }

    function failPipeline() {
        pipelineSteps.forEach(step => {
            if (step.classList.contains('processing')) {
                step.className = 'pipeline-step failed';
            }
        });
    }

    function hideResultCards() {
        resultsGrid.style.display = 'none';
        cardMonitor.style.display = 'none';
        cardCongestion.style.display = 'none';
        cardRAG.style.display = 'none';
        cardRoutes.style.display = 'none';
        cardSignals.style.display = 'none';
        cardNotifs.style.display = 'none';
    }

    function setLoadingState(isLoading) {
        const btnSubmit = formIncident.querySelector('button[type="submit"]');
        if (isLoading) {
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing Agent Pipeline...';
        } else {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = 'Analyze Traffic Incident';
        }
    }

    // Render results in cards
    function renderResults(results) {
        if (!results) return;
        resultsGrid.style.display = 'grid';

        // 1. Traffic Monitor Card
        updateCard(cardMonitor, results.traffic_monitor);
        // 2. Congestion Analyst Card
        updateCard(cardCongestion, results.congestion_analysis);
        // 3. RAG Knowledge Card
        updateCard(cardRAG, results.rag_knowledge);
        // 4. Route Planner Card
        updateCard(cardRoutes, results.emergency_routes);
        // 5. Signal Optimizer Card
        updateCard(cardSignals, results.signal_optimization);
        // 6. Public Notification Card
        updateCard(cardNotifs, results.public_notification);
    }

    function updateCard(cardElement, data) {
        if (!data) return;
        cardElement.style.display = 'block';
        
        // Badges for tools
        const badgesContainer = cardElement.querySelector('.card-tools');
        badgesContainer.innerHTML = '';
        if (data.tools_used && data.tools_used.length > 0) {
            data.tools_used.forEach(tool => {
                const badge = document.createElement('span');
                badge.className = 'badge bg-cyan-glow text-cyan border border-cyan-light me-1 mb-1';
                badge.textContent = tool;
                badgesContainer.appendChild(badge);
            });
        } else {
            badgesContainer.innerHTML = '<span class="badge bg-secondary text-muted">No Tools</span>';
        }

        // Body content
        const bodyContent = cardElement.querySelector('.card-body-content');
        bodyContent.innerHTML = formatMarkdown(data.output);
    }

    // Simple markdown to HTML formatter for agent outputs
    function formatMarkdown(text) {
        if (!text) return '';
        
        // Sanitize HTML
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Convert bold markdown
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert list items
        html = html.replace(/^\s*-\s+(.*?)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>');
        html = html.replace(/<\/ul>\s*<ul>/g, ''); // merge lists

        // Convert headers
        html = html.replace(/^### (.*?)$/gm, '<h5 class="text-info mt-3">$1</h5>');
        html = html.replace(/^## (.*?)$/gm, '<h4 class="text-cyan mt-3">$1</h4>');
        html = html.replace(/^# (.*?)$/gm, '<h3 class="text-cyan mt-4">$1</h3>');

        // Convert line breaks
        html = html.replace(/\n/g, '<br>');

        return html;
    }

    // Toast notifications
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
