// Definir funções globalmente IMEDIATAMENTE
function showSection(sectionName) {
    console.log('showSection chamada:', sectionName);
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    if (sectionName === 'transactions') {
        setTimeout(() => {
            loadTransactions();
        }, 100);
    } else if (sectionName === 'dashboard') {
        loadDashboard();
    } else if (typeof loadData === 'function') {
        loadData();
    }
}

function showBankForm() {
    document.getElementById('bank-form-section').style.display = 'block';
    document.getElementById('bank-form-title').textContent = 'Adicionar Banco';
    document.getElementById('bank-form').reset();
}

function hideBankForm() {
    document.getElementById('bank-form-section').style.display = 'none';
}

function showCardForm() {
    document.getElementById('card-form-section').style.display = 'block';
    document.getElementById('card-form').reset();
}

function hideCardForm() {
    document.getElementById('card-form-section').style.display = 'none';
}

function showTransactionForm() {
    const section = document.getElementById('transaction-form-section');
    if (section) {
        section.style.display = 'block';
        document.getElementById('transaction-form').reset();
        document.getElementById('transaction-date').value = new Date().toISOString().split('T')[0];
    }
}

function hideTransactionForm() {
    const section = document.getElementById('transaction-form-section');
    if (section) section.style.display = 'none';
}

function showTransferForm() {
    const section = document.getElementById('transfer-form-section');
    if (section) {
        section.style.display = 'block';
        document.getElementById('transfer-form').reset();
        document.getElementById('transfer-date').value = new Date().toISOString().split('T')[0];
    }
}

function hideTransferForm() {
    const section = document.getElementById('transfer-form-section');
    if (section) section.style.display = 'none';
}

function editBank(bankId) {
    fetch('/api/banks/' + bankId)
        .then(response => response.json())
        .then(bank => {
            document.getElementById('bank-form-section').style.display = 'block';
            document.getElementById('bank-form-title').textContent = 'Editar Banco';
            document.getElementById('bank-id').value = bank.id;
            document.getElementById('bank-name').value = bank.name;
            document.getElementById('initial-balance').value = bank.initial_balance;
        });
}

function deleteBank(bankId) {
    if (!confirm('Tem certeza que deseja excluir este banco?')) return;
    
    fetch('/api/banks/' + bankId, { method: 'DELETE' })
        .then(response => {
            if (response.ok) {
                loadData();
                alert('Banco excluído com sucesso!');
            } else {
                alert('Erro ao excluir banco');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao excluir banco');
        });
}

console.log('JavaScript carregado com sucesso!');

const API_BASE = '/api';
let currentEditingBank = null;

// Carregar dados quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado');
    showSection('dashboard');
    loadData();
    
    // Event listeners para formulários
    const bankForm = document.getElementById('bank-form');
    if (bankForm) {
        bankForm.addEventListener('submit', handleBankSubmit);
    }
    
    const cardForm = document.getElementById('card-form');
    if (cardForm) {
        cardForm.addEventListener('submit', handleCardSubmit);
    }
    
    const transactionForm = document.getElementById('transaction-form');
    if (transactionForm) {
        transactionForm.addEventListener('submit', handleTransactionSubmit);
    }
});



// Handlers dos formulários
async function handleBankSubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('bank-name').value;
    const initialBalance = parseFloat(document.getElementById('initial-balance').value) || 0;
    const bankId = document.getElementById('bank-id').value;
    
    try {
        let response;
        if (bankId) {
            response = await fetch(`${API_BASE}/banks/${bankId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, initial_balance: initialBalance })
            });
        } else {
            response = await fetch(`${API_BASE}/banks/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, initial_balance: initialBalance })
            });
        }
        
        if (response.ok) {
            hideBankForm();
            loadData();
            alert(bankId ? 'Banco atualizado!' : 'Banco adicionado!');
        } else {
            alert('Erro ao salvar banco');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar banco');
    }
}

async function handleCardSubmit(e) {
    e.preventDefault();
    
    const cardId = document.getElementById('card-id').value;
    const bankId = parseInt(document.getElementById('card-bank-select').value);
    const name = document.getElementById('card-name').value;
    const type = document.getElementById('card-type').value;
    const limitAmount = parseFloat(document.getElementById('card-limit').value) || null;
    const dueDay = parseInt(document.getElementById('card-due-day').value) || null;
    
    try {
        let response;
        if (cardId) {
            response = await fetch(`${API_BASE}/cards/${cardId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, type, limit_amount: limitAmount, due_day: dueDay })
            });
        } else {
            response = await fetch(`${API_BASE}/banks/${bankId}/cards`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, type, limit_amount: limitAmount, due_day: dueDay })
            });
        }
        
        if (response.ok) {
            hideCardForm();
            loadData();
            alert(cardId ? 'Cartão atualizado!' : 'Cartão adicionado!');
        } else {
            alert('Erro ao salvar cartão');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar cartão');
    }
}

async function handleTransactionSubmit(e) {
    e.preventDefault();
    
    const transactionId = document.getElementById('transaction-id').value;
    const cardId = parseInt(document.getElementById('card-select').value);
    const totalAmount = parseFloat(document.getElementById('amount').value);
    const description = document.getElementById('description').value;
    const date = document.getElementById('transaction-date').value;
    const installments = parseInt(document.getElementById('installments').value) || 1;
    
    try {
        if (transactionId) {
            // Editar transação existente
            const response = await fetch(`${API_BASE}/transactions/${transactionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    card_id: cardId, 
                    amount: totalAmount, 
                    type: 'expense', 
                    description: description, 
                    date: date
                })
            });
            
            if (response.ok) {
                hideTransactionForm();
                loadData();
                alert('Compra atualizada com sucesso!');
            } else {
                alert('Erro ao atualizar compra');
            }
        } else {
            // Criar nova transação com parcelamento
            const installmentAmount = totalAmount / installments;
            const purchaseDate = new Date(date);
            
            for (let i = 0; i < installments; i++) {
                const installmentDate = new Date(purchaseDate);
                installmentDate.setMonth(installmentDate.getMonth() + i);
                
                const installmentDescription = installments > 1 
                    ? `${description} (${i + 1}/${installments})`
                    : description;
                
                await fetch(`${API_BASE}/transactions/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        card_id: cardId, 
                        amount: installmentAmount, 
                        type: 'expense', 
                        description: installmentDescription, 
                        date: installmentDate.toISOString().split('T')[0]
                    })
                });
            }
            
            hideTransactionForm();
            loadData();
            alert(`Compra ${installments > 1 ? `parcelada em ${installments}x` : ''} adicionada com sucesso!`);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao processar compra');
    }
}

// Resto das funções...
async function loadData() {
    await Promise.all([
        loadSummary(),
        loadBanks(),
        loadCards(),
        loadTransfers()
    ]);
    
    // Carregar transações apenas se estivermos na seção de transações
    const transactionsSection = document.getElementById('transactions-section');
    if (transactionsSection && transactionsSection.style.display !== 'none') {
        if (typeof loadTransactionsData === 'function') {
            loadTransactionsData();
        }
    }
}

async function loadSummary() {
    try {
        const response = await fetch(`${API_BASE}/summary/`);
        const data = await response.json();
        
        let html = `
            <div class="row">
                <div class="col-md-8">
                    <h6>Saldos por Banco:</h6>
        `;
        
        data.banks.forEach(bank => {
            const balanceClass = bank.balance >= 0 ? 'text-success' : 'text-danger';
            html += `
                <div class="d-flex justify-content-between">
                    <span>${bank.bank_name}:</span>
                    <span class="${balanceClass}">R$ ${bank.balance.toFixed(2)}</span>
                </div>
            `;
        });
        
        html += `
                </div>
                <div class="col-md-4">
                    <div class="bg-primary text-white p-3 rounded text-center">
                        <h6>Total Geral</h6>
                        <h4>R$ ${data.total_balance.toFixed(2)}</h4>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('summary-section').innerHTML = html;
    } catch (error) {
        console.error('Erro ao carregar resumo:', error);
    }
}

async function loadBanks() {
    try {
        const response = await fetch(`${API_BASE}/banks/`);
        const banks = await response.json();
        
        let html = '';
        banks.forEach(bank => {
            const balanceClass = bank.current_balance >= 0 ? 'text-success' : 'text-danger';
            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6>${bank.name}</h6>
                                <small class="text-muted">Saldo inicial: R$ ${bank.initial_balance.toFixed(2)}</small>
                            </div>
                            <div class="text-end">
                                <div class="${balanceClass} h5">R$ ${bank.current_balance.toFixed(2)}</div>
                                <div class="mt-2">
                                    <button class="btn btn-sm btn-outline-primary" onclick="editBank(${bank.id})">
                                        Editar
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="deleteBank(${bank.id})">
                                        Excluir
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        document.getElementById('banks-list').innerHTML = html || '<p class="text-muted">Nenhum banco cadastrado.</p>';
    } catch (error) {
        console.error('Erro ao carregar bancos:', error);
    }
}

async function loadCards() {
    try {
        const response = await fetch(`${API_BASE}/cards/`);
        const cards = await response.json();
        
        // Buscar bancos para agrupar
        const banksResponse = await fetch(`${API_BASE}/banks/`);
        const banks = await banksResponse.json();
        const banksMap = {};
        banks.forEach(bank => {
            banksMap[bank.id] = bank.name;
        });
        
        let html = '';
        const cardsByBank = {};
        cards.forEach(card => {
            if (!cardsByBank[card.bank_id]) {
                cardsByBank[card.bank_id] = [];
            }
            cardsByBank[card.bank_id].push(card);
        });
        
        for (const bankId in cardsByBank) {
            const bankCards = cardsByBank[bankId];
            const bankName = banksMap[bankId] || 'Banco';
            
            html += `
                <div class="card mb-3">
                    <div class="card-header">
                        <h6>${bankName}</h6>
                    </div>
                    <div class="card-body">
            `;
            
            bankCards.forEach(card => {
                html += `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>
                            <span>${card.name}</span>
                            <span class="badge ${card.type === 'credit' ? 'bg-primary' : 'bg-secondary'} ms-2">
                                ${card.type === 'credit' ? 'Crédito' : 'Débito'}
                            </span>
                            ${card.limit_amount ? `<small class="text-muted ms-2">Limite: R$ ${card.limit_amount.toFixed(2)}</small>` : ''}
                            ${card.due_day ? `<small class="text-muted ms-2">Venc: ${card.due_day}</small>` : ''}
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary" onclick="editCard(${card.id})">
                                Editar
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteCard(${card.id})">
                                Excluir
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        document.getElementById('cards-list').innerHTML = html || '<p class="text-muted">Nenhum cartão cadastrado.</p>';
        
        // Atualizar select de bancos no formulário de cartão
        const bankSelect = document.getElementById('card-bank-select');
        bankSelect.innerHTML = '<option value="">Selecione um banco</option>';
        banks.forEach(bank => {
            const option = document.createElement('option');
            option.value = bank.id;
            option.textContent = bank.name;
            bankSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('Erro ao carregar cartões:', error);
    }
}

let selectedTransactions = new Set();

async function loadTransactionsData() {
    try {
        const params = new URLSearchParams();
        const dateFrom = document.getElementById('filter-date-from')?.value;
        const dateTo = document.getElementById('filter-date-to')?.value;
        const bankId = document.getElementById('filter-bank')?.value;
        
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        if (bankId) params.append('bank_id', bankId);
        
        const url = '/api/transactions/' + (params.toString() ? '?' + params.toString() : '');
        const response = await fetch(url);
        const transactions = await response.json();
        
        const tbody = document.getElementById('transactions-list');
        tbody.innerHTML = '';
        
        if (transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9">Nenhuma transação encontrada</td></tr>';
            return;
        }
        
        transactions.forEach(t => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="checkbox" class="transaction-checkbox" value="${t.id}" onchange="toggleTransactionSelection(${t.id})"></td>
                <td>${new Date(t.date).toLocaleDateString('pt-BR')}</td>
                <td>${t.bank_name}</td>
                <td>${t.card_name}</td>
                <td>${t.description}</td>
                <td>R$ ${t.amount.toFixed(2)}</td>
                <td>-</td>
                <td>${t.is_paid ? 'Pago' : 'Pendente'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-success" onclick="togglePayment(${t.id})" title="Alterar Status">✓</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteTransaction(${t.id})" title="Excluir">🗑️</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Erro ao carregar transações:', error);
    }
}

async function loadTransactionFilters() {
    try {
        // Carregar bancos para o filtro
        const banksResponse = await fetch('/api/banks/');
        const banks = await banksResponse.json();
        
        const bankFilterSelect = document.getElementById('filter-bank');
        if (bankFilterSelect) {
            const currentValue = bankFilterSelect.value;
            bankFilterSelect.innerHTML = '<option value="">Todos os bancos</option>';
            banks.forEach(bank => {
                const option = document.createElement('option');
                option.value = bank.id;
                option.textContent = bank.name;
                if (bank.id.toString() === currentValue) {
                    option.selected = true;
                }
                bankFilterSelect.appendChild(option);
            });
        }
        
        // Carregar cartões para o formulário
        const cardsResponse = await fetch('/api/cards/');
        const cards = await cardsResponse.json();
        
        const cardSelect = document.getElementById('card-select');
        if (cardSelect) {
            cardSelect.innerHTML = '<option value="">Selecione um cartão</option>';
            cards.forEach(card => {
                const option = document.createElement('option');
                option.value = card.id;
                option.textContent = `${card.name} (${card.type === 'credit' ? 'Crédito' : 'Débito'})`;
                cardSelect.appendChild(option);
            });
        }
        
        // Carregar bancos e cartões para o dashboard
        const dashBankSelect = document.getElementById('dash-filter-bank');
        if (dashBankSelect) {
            dashBankSelect.innerHTML = '<option value="">Todos os bancos</option>';
            banks.forEach(bank => {
                const option = document.createElement('option');
                option.value = bank.id;
                option.textContent = bank.name;
                dashBankSelect.appendChild(option);
            });
        }
        
        const dashCardSelect = document.getElementById('dash-filter-card');
        if (dashCardSelect) {
            dashCardSelect.innerHTML = '<option value="">Todos os cartões</option>';
            cards.forEach(card => {
                const option = document.createElement('option');
                option.value = card.id;
                option.textContent = card.name;
                dashCardSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Erro ao carregar filtros:', error);
    }
}

function clearFiltersInline() {
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    document.getElementById('filter-bank').value = '';
    clearSelection();
    loadTransactionsData();
    loadTransactionFilters();
}

function loadTransactions() {
    loadTransactionsData();
    loadTransactionFilters();
}

function getTransactionTypeText(type) {
    const types = {
        'expense': 'Despesa',
        'payment': 'Pagamento',
        'refund': 'Reembolso',
        'deposit': 'Depósito',
        'transfer_out': 'Transferência Saída',
        'transfer_in': 'Transferência Entrada'
    };
    return types[type] || type;
}

function getTransactionTypeClass(type) {
    const classes = {
        'expense': 'bg-danger',
        'payment': 'bg-success',
        'refund': 'bg-info',
        'deposit': 'bg-primary',
        'transfer_out': 'bg-warning',
        'transfer_in': 'bg-success'
    };
    return classes[type] || 'bg-secondary';
}

// Funções de filtro
function applyFilters() {
    clearSelection();
    loadTransactionsData();
}

function clearFilters() {
    clearFiltersInline();
}

// Expor funções globalmente
window.applyFilters = applyFilters;
window.clearFilters = clearFilters;

// Funções de seleção múltipla
function toggleTransactionSelection(transactionId) {
    const checkbox = document.querySelector(`input[value="${transactionId}"]`);
    const row = checkbox ? checkbox.closest('tr') : null;
    
    if (selectedTransactions.has(transactionId)) {
        selectedTransactions.delete(transactionId);
        if (row) row.classList.remove('table-active');
    } else {
        selectedTransactions.add(transactionId);
        if (row) row.classList.add('table-active');
    }
    updateSelectionCounter();
    updateSelectAllCheckbox();
}

function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.transaction-checkbox');
    
    if (selectAllCheckbox.checked) {
        checkboxes.forEach(checkbox => {
            const transactionId = parseInt(checkbox.value);
            selectedTransactions.add(transactionId);
            checkbox.checked = true;
            // Adicionar classe visual diretamente
            const row = checkbox.closest('tr');
            if (row) row.classList.add('table-active');
        });
    } else {
        selectedTransactions.clear();
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            // Remover classe visual diretamente
            const row = checkbox.closest('tr');
            if (row) row.classList.remove('table-active');
        });
    }
    
    updateSelectionCounter();
}

// Expor funções globalmente
window.toggleTransactionSelection = toggleTransactionSelection;
window.toggleSelectAll = toggleSelectAll;

function updateSelectionCounter() {
    const count = selectedTransactions.size;
    const counterElement = document.getElementById('selected-count');
    const bulkActionsElement = document.getElementById('bulk-actions');
    
    if (counterElement) {
        counterElement.textContent = `${count} transação${count !== 1 ? 'ões' : ''} selecionada${count !== 1 ? 's' : ''}`;
    }
    
    if (bulkActionsElement) {
        bulkActionsElement.style.display = count > 0 ? 'block' : 'none';
    }
}

function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.transaction-checkbox');
    const checkedCount = document.querySelectorAll('.transaction-checkbox:checked').length;
    
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = checkboxes.length > 0 && checkedCount === checkboxes.length;
        selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    }
}

function clearSelection() {
    selectedTransactions.clear();
    document.querySelectorAll('.transaction-checkbox').forEach(checkbox => {
        checkbox.checked = false;
        const row = checkbox.closest('tr');
        if (row) row.classList.remove('table-active');
    });
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
    updateSelectionCounter();
}

// Função para atualização em lote
async function bulkUpdateStatus(isPaid) {
    if (selectedTransactions.size === 0) {
        alert('Nenhuma transação selecionada');
        return;
    }
    
    const action = isPaid ? 'marcar como pagas' : 'marcar como pendentes';
    if (!confirm(`Deseja ${action} ${selectedTransactions.size} transação${selectedTransactions.size !== 1 ? 'ões' : ''}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/transactions/bulk-update-status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transaction_ids: Array.from(selectedTransactions),
                is_paid: isPaid
            })
        });
        
        if (response.ok) {
            clearSelection();
            loadData();
            alert(`Status atualizado com sucesso!`);
        } else {
            alert('Erro ao atualizar status das transações');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao atualizar status das transações');
    }
}

// Expor funções globalmente
window.bulkUpdateStatus = bulkUpdateStatus;
window.clearSelection = clearSelection;

async function loadTransfers() {
    // Implementar depois
}

// Funções do Dashboard
let expenseChart = null;

async function loadDashboard() {
    await loadTransactionFilters();
    await loadExpenseChart();
}

async function loadExpenseChart() {
    try {
        const params = new URLSearchParams();
        const bankId = document.getElementById('dash-filter-bank')?.value;
        const cardId = document.getElementById('dash-filter-card')?.value;
        
        if (bankId) params.append('bank_id', bankId);
        if (cardId) params.append('card_id', cardId);
        
        const url = '/api/summary/monthly-expenses' + (params.toString() ? '?' + params.toString() : '');
        const response = await fetch(url);
        const data = await response.json();
        
        const ctx = document.getElementById('expenseChart').getContext('2d');
        
        if (expenseChart) {
            expenseChart.destroy();
        }
        
        expenseChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.month),
                datasets: [{
                    label: 'Gastos Mensais',
                    data: data.map(item => item.total),
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Erro ao carregar gráfico:', error);
    }
}

function applyDashboardFilters() {
    loadExpenseChart();
}

function clearDashboardFilters() {
    document.getElementById('dash-filter-bank').value = '';
    document.getElementById('dash-filter-card').value = '';
    loadExpenseChart();
}

// Expor funções globalmente
window.applyDashboardFilters = applyDashboardFilters;
window.clearDashboardFilters = clearDashboardFilters;
window.loadDashboard = loadDashboard;