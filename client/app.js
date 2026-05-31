const API_BASE = window.API_BASE || 'http://localhost:8000/api/v1';
const APPLICANT_TEMPLATE = document.getElementById('applicant-template');
const REQUEST_TIMEOUT = 10000;

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const targetId = 'tab-' + tab.dataset.tab;
        document.getElementById(targetId).classList.add('active');
    });
});

function showSpinner(spinnerId) {
    const el = document.getElementById(spinnerId);
    if (el) el.style.display = '';
}

function hideSpinner(spinnerId) {
    const el = document.getElementById(spinnerId);
    if (el) el.style.display = 'none';
}

function showMessage(containerId, message, isError = false) {
    const msgDiv = document.getElementById(containerId);
    if (!msgDiv) return;
    let displayMessage = message
        .replace(/строк/g, 'заявок')
        .replace(/предсказание/gi, 'прогноз')
        .replace(/предсказания/gi, 'прогноза')
        .replace(/предсказать/gi, 'спрогнозировать');
    msgDiv.textContent = displayMessage;
    msgDiv.className = 'message ' + (isError ? 'error' : 'success');
    msgDiv.classList.remove('hidden');
}

function clearMessage(containerId) {
    const msgDiv = document.getElementById(containerId);
    if (msgDiv) {
        msgDiv.textContent = '';
        msgDiv.classList.add('hidden');
    }
}

function showTable(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (!data || data.length === 0) return;

    const table = document.createElement('table');
    const headers = Object.keys(data[0]);
    
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headers.forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    data.forEach(row => {
        const tr = document.createElement('tr');
        headers.forEach(h => {
            const td = document.createElement('td');
            let val = row[h];
            if (h === 'predicted') {
                val = val === 1 ? 'Одобрено' : 'Отказ';
                td.style.color = val === 'Одобрено' ? '#16a34a' : '#dc2626';
                td.style.fontWeight = 'bold';
            } else if (h === 'confidence (%)') {
                val = val + '%';
            }
            td.textContent = val;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);
}

function createApplicant(index, containerId) {
    const clone = APPLICANT_TEMPLATE.content.cloneNode(true);
    const applicantDiv = clone.querySelector('.applicant');
    applicantDiv.dataset.index = index;
    applicantDiv.querySelector('.applicant-number').textContent = index + 1;
    
    const removeBtn = applicantDiv.querySelector('.btn-remove');
    removeBtn.addEventListener('click', () => {
        applicantDiv.remove();
        reindexApplicants(containerId);
    });
    
    document.getElementById(containerId).appendChild(applicantDiv);
    return applicantDiv;
}

function reindexApplicants(containerId) {
    const container = document.getElementById(containerId);
    const applicants = container.querySelectorAll('.applicant');
    applicants.forEach((app, idx) => {
        app.dataset.index = idx;
        app.querySelector('.applicant-number').textContent = idx + 1;
        const removeBtn = app.querySelector('.btn-remove');
        if (applicants.length === 1) {
            removeBtn.classList.add('hidden');
        } else {
            removeBtn.classList.remove('hidden');
        }
    });
}

function collectApplicants(containerId) {
    const applicants = document.getElementById(containerId).querySelectorAll('.applicant');
    const records = [];
    applicants.forEach(app => {
        const inputs = app.querySelectorAll('input, select');
        const record = {};
        inputs.forEach(input => {
            let value = input.value;
            if (input.type === 'number' && value !== '') {
                value = parseFloat(value);
            }
            record[input.name] = value;
        });
        records.push(record);
    });
    return records;
}

async function fetchWithTimeout(url, options, timeout = REQUEST_TIMEOUT) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    const config = { ...options, signal: controller.signal };
    try {
        const response = await fetch(url, config);
        clearTimeout(id);
        return response;
    } catch (err) {
        clearTimeout(id);
        if (err.name === 'AbortError') {
            throw new Error('Превышено время ожидания ответа от сервера');
        }
        throw err;
    }
}

const API = {
    async predictForm(records) {
        const formData = new FormData();
        formData.append('form_data', JSON.stringify(records));
        const res = await fetchWithTimeout(`${API_BASE}/predict/form`, { method: 'POST', body: formData });
        return res.json();
    },
    async predictCsv(file) {
        const formData = new FormData();
        formData.append('data_file', file);
        const res = await fetchWithTimeout(`${API_BASE}/predict/csv`, { method: 'POST', body: formData });
        return res.json();
    },
    async predictCustom(modelFile, recordsOrCsv, isCsv) {
        const formData = new FormData();
        formData.append('model_file', modelFile);
        if (isCsv) {
            formData.append('data_file', recordsOrCsv);
        } else {
            formData.append('form_data', JSON.stringify(recordsOrCsv));
        }
        const res = await fetchWithTimeout(`${API_BASE}/predict/custom`, { method: 'POST', body: formData });
        return res.json();
    },
    async health() {
        const res = await fetch(`${API_BASE.replace('/api/v1','')}/health`);
        return res.json();
    }
};

async function handlePredictRequest({ apiCall, spinnerId, msgId, tableId, resultBlock }) {
    clearMessage(msgId);
    if (document.getElementById(tableId)) {
        document.getElementById(tableId).innerHTML = '';
    }
    resultBlock.classList.remove('hidden');
    showSpinner(spinnerId);
    try {
        const response = await apiCall();
        if (response.status_code === 200) {
            showMessage(msgId, response.message, false);
            showTable(tableId, response.data);
        } else {
            showMessage(msgId, response.message || 'Ошибка сервера', true);
        }
    } catch (err) {
        showMessage(msgId, err.message || 'Неизвестная ошибка', true);
    } finally {
        hideSpinner(spinnerId);
    }
}

document.getElementById('predict-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await handlePredictRequest({
        apiCall: () => API.predictForm(collectApplicants('applicants-container')),
        spinnerId: 'form-spinner',
        msgId: 'form-message',
        tableId: 'form-table-container',
        resultBlock: document.getElementById('form-result')
    });
});

document.getElementById('csv-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('csv-file');
    const file = fileInput.files[0];
    if (!file) return;
    await handlePredictRequest({
        apiCall: () => API.predictCsv(file),
        spinnerId: 'csv-spinner',
        msgId: 'csv-message',
        tableId: 'csv-table-container',
        resultBlock: document.getElementById('csv-result')
    });
});

document.querySelectorAll('input[name="data_type"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const csvSection = document.getElementById('custom-csv-section');
        const formSection = document.getElementById('custom-form-section');
        if (this.value === 'csv') {
            csvSection.style.display = 'block';
            formSection.style.display = 'none';
        } else {
            csvSection.style.display = 'none';
            formSection.style.display = 'block';
        }
    });
});

document.getElementById('custom-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const modelFileInput = document.getElementById('model-file');
    const modelFile = modelFileInput.files[0];
    if (!modelFile) return;

    const dataType = document.querySelector('input[name="data_type"]:checked').value;
    
    let apiCall;
    if (dataType === 'csv') {
        const csvFile = document.getElementById('custom-csv-file').files[0];
        if (!csvFile) {
            showMessage('custom-message', 'Выберите CSV-файл', true);
            return;
        }
        apiCall = () => API.predictCustom(modelFile, csvFile, true);
    } else {
        const records = collectApplicants('custom-applicants-container');
        apiCall = () => API.predictCustom(modelFile, records, false);
    }

    await handlePredictRequest({
        apiCall,
        spinnerId: 'custom-spinner',
        msgId: 'custom-message',
        tableId: 'custom-table-container',
        resultBlock: document.getElementById('custom-result')
    });
});

document.addEventListener('DOMContentLoaded', () => {
    createApplicant(0, 'applicants-container');
    reindexApplicants('applicants-container');

    document.getElementById('add-applicant').addEventListener('click', () => {
        const container = document.getElementById('applicants-container');
        const count = container.querySelectorAll('.applicant').length;
        createApplicant(count, 'applicants-container');
        reindexApplicants('applicants-container');
    });

    document.getElementById('custom-add-applicant').addEventListener('click', () => {
        const container = document.getElementById('custom-applicants-container');
        const count = container.querySelectorAll('.applicant').length;
        createApplicant(count, 'custom-applicants-container');
        reindexApplicants('custom-applicants-container');
    });

    function bindFileInput(inputId, placeholderId) {
        const input = document.getElementById(inputId);
        const placeholder = document.getElementById(placeholderId);
        if (input && placeholder) {
            input.addEventListener('change', () => {
                if (input.files && input.files.length > 0) {
                    placeholder.textContent = input.files[0].name;
                } else {
                    placeholder.textContent = 'Файл не выбран';
                }
            });
        }
    }

    bindFileInput('csv-file', 'csv-placeholder');
    bindFileInput('model-file', 'model-placeholder');
    bindFileInput('custom-csv-file', 'custom-csv-placeholder');

    API.health().then(data => {
        const statusEl = document.getElementById('api-status');
        if (statusEl) statusEl.textContent = data.status === 'ok' ? 'доступен' : 'недоступен';
    }).catch(() => {
        const statusEl = document.getElementById('api-status');
        if (statusEl) statusEl.textContent = 'ошибка соединения';
    });
});