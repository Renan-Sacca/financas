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
    } else if (sectionName === 'transfers') {
        loadTransfers();
    } else if (sectionName === 'categories') {
        loadCategories();
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
        document.getElementById('deposit-date').value = new Date().toISOString().split('T')[0];
        loadBanksForDeposit();
    }
}

function hideTransferForm() {
    const section = document.getElementById('transfer-form-section');
    if (section) section.style.display = 'none';
}

function showCategoryForm() {
    document.getElementById('category-form-section').style.display = 'block';
    document.getElementById('category-form').reset();
}

function hideCategoryForm() {
    document.getElementById('category-form-section').style.display = 'none';
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
    
    const transferForm = document.getElementById('transfer-form');
    if (transferForm) {
        transferForm.addEventListener('submit', handleDepositSubmit);
    }
    
    const categoryForm = document.getElementById('category-form');
    if (categoryForm) {
        categoryForm.addEventListener('submit', handleCategorySubmit);
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

async function handleDepositSubmit(e) {
    e.preventDefault();
    
    const bankId = parseInt(document.getElementById('deposit-bank').value);
    const amount = parseFloat(document.getElementById('deposit-amount').value);
    const description = document.getElementById('deposit-description').value;
    const date = document.getElementById('deposit-date').value;
    
    try {
        const response = await fetch('/api/deposits/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bank_id: bankId,
                amount: amount,
                description: description,
                date: date
            })
        });
        
        if (response.ok) {
            hideTransferForm();
            loadData();
            alert('Depósito registrado com sucesso!');
        } else {
            alert('Erro ao registrar depósito');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao registrar depósito');
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

async function handleCategorySubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('category-name').value;
    const color = document.getElementById('category-color').value;
    
    try {
        const response = await fetch(`${API_BASE}/categories/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, color })
        });
        
        if (response.ok) {
            hideCategoryForm();
            loadData();
            alert('Categoria adicionada!');
        } else {
            alert('Erro ao salvar categoria');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar categoria');
    }
}

async function handleTransactionSubmit(e) {
    e.preventDefault();
    
    const transactionId = document.getElementById('transaction-id').value;
    const cardId = parseInt(document.getElementById('card-select').value);
    const totalAmount = parseFloat(document.getElementById('amount').value);
    const description = document.getElementById('description').value;
    const date = document.getElementById('transaction-date').value;
    const categoryId = document.getElementById('category-select').value || null;
    const installments = parseInt(document.getElementById('installments').value) || 1;
    
    try {
        if (transactionId) {
            if (transactionId.startsWith('group:')) {
                // Editar grupo de parcelas
                const groupId = transactionId.replace('group:', '');
                const response = await fetch(`${API_BASE}/transactions/update-group`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        group_id: groupId,
                        card_id: cardId, 
                        total_amount: totalAmount, 
                        description: description, 
                        date: date,
                        category_id: categoryId,
                        installments: installments
                    })
                });
                
                if (response.ok) {
                    hideTransactionForm();
                    loadData();
                    alert('Compra parcelada atualizada com sucesso!');
                } else {
                    alert('Erro ao atualizar compra parcelada');
                }
            } else {
                // Editar transação única
                const response = await fetch(`${API_BASE}/transactions/${transactionId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        card_id: cardId, 
                        amount: totalAmount, 
                        type: 'expense', 
                        description: description, 
                        date: date,
                        category_id: categoryId
                    })
                });
                
                if (response.ok) {
                    hideTransactionForm();
                    loadData();
                    alert('Compra atualizada com sucesso!');
                } else {
                    alert('Erro ao atualizar compra');
                }
            }
        } else {
            // Buscar dados do cartão para calcular vencimento
            const cardResponse = await fetch(`${API_BASE}/cards/`);
            const cards = await cardResponse.json();
            const selectedCard = cards.find(c => c.id === cardId);
            
            const installmentAmount = totalAmount / installments;
            const [year, month, day] = date.split('-').map(Number);
            
            // Gerar ID único para agrupar parcelas
            const groupId = installments > 1 ? `group_${Date.now()}_${Math.random().toString(36).substr(2, 9)}` : null;
            
            // Calcular primeira data de vencimento
            let firstDueYear = year;
            let firstDueMonth = month;
            const dueDay = selectedCard && selectedCard.due_day ? selectedCard.due_day : 1;
            
            // Se a compra foi depois do vencimento, vai para o próximo mês
            if (day > dueDay) {
                firstDueMonth += 1;
                if (firstDueMonth > 12) {
                    firstDueMonth = 1;
                    firstDueYear += 1;
                }
            }
            
            for (let i = 0; i < installments; i++) {
                let installmentYear = firstDueYear;
                let installmentMonth = firstDueMonth + i;
                
                while (installmentMonth > 12) {
                    installmentMonth -= 12;
                    installmentYear += 1;
                }
                
                const installmentDateStr = `${installmentYear}-${String(installmentMonth).padStart(2, '0')}-${String(dueDay).padStart(2, '0')}`;
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
                        date: installmentDateStr,
                        purchase_date: date,
                        category_id: categoryId,
                        group_id: groupId,
                        installment_number: installments > 1 ? i + 1 : null,
                        total_installments: installments > 1 ? installments : null
                    })
                });
            }
            
            // Limpar apenas campos específicos, manter cartão e data
            document.getElementById('amount').value = '';
            document.getElementById('description').value = '';
            document.getElementById('installments').value = '1';
            loadData();
            alert(`Compra ${installments > 1 ? `parcelada em ${installments}x` : ''} adicionada com sucesso!`);
            // Focar no campo valor para próxima entrada
            document.getElementById('amount').focus();
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
        loadCategories(),
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
                    <h6 class="mb-3">Saldos por Banco:</h6>
        `;
        
        data.banks.forEach(bank => {
            const balanceClass = bank.balance >= 0 ? 'text-success' : 'text-danger';
            html += `
                <div class="bank-balance-item">
                    <span class="bank-balance-name">${bank.bank_name}</span>
                    <span class="bank-balance-value ${balanceClass}">R$ ${bank.balance.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                </div>
            `;
        });
        
        html += `
                </div>
                <div class="col-md-4">
                    <div class="summary-card">
                        <h6>Total Geral</h6>
                        <h4>R$ ${data.total_balance.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</h4>
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

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories/`);
        const categories = await response.json();
        
        let html = '';
        categories.forEach(category => {
            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="d-flex align-items-center">
                                <div class="category-color" style="width: 20px; height: 20px; background-color: ${category.color}; border-radius: 50%; margin-right: 10px;"></div>
                                <h6 class="mb-0">${category.name}</h6>
                            </div>
                            <div>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${category.id})">
                                    Excluir
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        document.getElementById('categories-list').innerHTML = html || '<p class="text-muted">Nenhuma categoria cadastrada.</p>';
        
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

async function deleteCategory(categoryId) {
    if (!confirm('Tem certeza que deseja excluir esta categoria?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/categories/${categoryId}`, { method: 'DELETE' });
        if (response.ok) {
            loadData();
            alert('Categoria excluída com sucesso!');
        } else {
            alert('Erro ao excluir categoria');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao excluir categoria');
    }
}

async function editGroup(groupId) {
    try {
        const response = await fetch(`${API_BASE}/transactions/`);
        const transactions = await response.json();
        const groupTransactions = transactions.filter(t => t.group_id === groupId);
        
        if (groupTransactions.length > 0) {
            const firstTransaction = groupTransactions[0];
            const totalAmount = groupTransactions.reduce((sum, t) => sum + t.amount, 0);
            
            await loadEditModalData();
            
            document.getElementById('editModalTitle').textContent = 'Editar Compra Parcelada';
            document.getElementById('edit-transaction-id').value = `group:${groupId}`;
            document.getElementById('edit-card-select').value = firstTransaction.card_id;
            document.getElementById('edit-amount').value = totalAmount;
            document.getElementById('edit-description').value = firstTransaction.description.replace(/ \(\d+\/\d+\)$/, '');
            document.getElementById('edit-transaction-date').value = firstTransaction.purchase_date || firstTransaction.date;
            document.getElementById('edit-category-select').value = firstTransaction.category_id || '';
            document.getElementById('edit-installments').value = firstTransaction.total_installments;
            
            toggleEditInstallments();
            new bootstrap.Modal(document.getElementById('editModal')).show();
        }
    } catch (error) {
        console.error('Erro ao carregar grupo:', error);
        alert('Erro ao carregar dados do grupo');
    }
}

async function editTransaction(transactionId) {
    try {
        const response = await fetch(`${API_BASE}/transactions/`);
        const transactions = await response.json();
        const transaction = transactions.find(t => t.id === transactionId);
        
        if (transaction) {
            await loadEditModalData();
            
            document.getElementById('editModalTitle').textContent = 'Editar Compra';
            document.getElementById('edit-transaction-id').value = transaction.id;
            document.getElementById('edit-card-select').value = transaction.card_id;
            document.getElementById('edit-amount').value = transaction.amount;
            document.getElementById('edit-description').value = transaction.description;
            document.getElementById('edit-transaction-date').value = transaction.date;
            document.getElementById('edit-category-select').value = transaction.category_id || '';
            
            toggleEditInstallments();
            new bootstrap.Modal(document.getElementById('editModal')).show();
        }
    } catch (error) {
        console.error('Erro ao carregar transação:', error);
        alert('Erro ao carregar dados da transação');
    }
}

async function loadEditModalData() {
    const cardsResponse = await fetch('/api/cards/');
    const cards = await cardsResponse.json();
    
    const cardSelect = document.getElementById('edit-card-select');
    cardSelect.innerHTML = '<option value="">Selecione um cartão</option>';
    cards.forEach(card => {
        const option = document.createElement('option');
        option.value = card.id;
        option.textContent = `${card.name} (${card.type === 'credit' ? 'Crédito' : 'Débito'})`;
        cardSelect.appendChild(option);
    });
    
    const categoriesResponse = await fetch('/api/categories/');
    const categories = await categoriesResponse.json();
    
    const categorySelect = document.getElementById('edit-category-select');
    categorySelect.innerHTML = '<option value="">Sem categoria</option>';
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        categorySelect.appendChild(option);
    });
}

function toggleEditInstallments() {
    const select = document.getElementById('edit-card-select');
    const field = document.getElementById('edit-installments-field');
    if (select.value) {
        fetch('/api/cards/').then(r => r.json()).then(cards => {
            const card = cards.find(c => c.id == select.value);
            field.style.display = card && card.type === 'credit' ? 'block' : 'none';
        });
    } else {
        field.style.display = 'none';
    }
}

async function saveEdit() {
    const transactionId = document.getElementById('edit-transaction-id').value;
    const cardId = parseInt(document.getElementById('edit-card-select').value);
    const totalAmount = parseFloat(document.getElementById('edit-amount').value);
    const description = document.getElementById('edit-description').value;
    const date = document.getElementById('edit-transaction-date').value;
    const categoryId = document.getElementById('edit-category-select').value || null;
    const installments = parseInt(document.getElementById('edit-installments').value) || 1;
    
    try {
        if (transactionId.startsWith('group:')) {
            const groupId = transactionId.replace('group:', '');
            const response = await fetch(`${API_BASE}/transactions/update-group`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    group_id: groupId,
                    card_id: cardId, 
                    total_amount: totalAmount, 
                    description: description, 
                    date: date,
                    category_id: categoryId,
                    installments: installments
                })
            });
            
            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
                loadData();
                alert('Compra parcelada atualizada com sucesso!');
            } else {
                alert('Erro ao atualizar compra parcelada');
            }
        } else {
            const response = await fetch(`${API_BASE}/transactions/${transactionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    card_id: cardId, 
                    amount: totalAmount, 
                    type: 'expense', 
                    description: description, 
                    date: date,
                    category_id: categoryId
                })
            });
            
            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
                loadData();
                alert('Compra atualizada com sucesso!');
            } else {
                alert('Erro ao atualizar compra');
            }
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar alterações');
    }
}

async function deleteGroup(groupId) {
    if (!confirm('Tem certeza que deseja excluir TODAS as parcelas desta compra?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/transactions/delete-group/${groupId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadData();
            alert('Todas as parcelas foram excluídas com sucesso!');
        } else {
            alert('Erro ao excluir parcelas');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao excluir parcelas');
    }
}

let selectedTransactions = new Set();

async function loadTransactionsData() {
    try {
        const params = new URLSearchParams();
        const dateFrom = document.getElementById('filter-date-from')?.value;
        const dateTo = document.getElementById('filter-date-to')?.value;
        const bankId = document.getElementById('filter-bank')?.value;
        const status = document.getElementById('filter-status')?.value;
        
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        if (bankId) params.append('bank_id', bankId);
        if (status) params.append('status', status);
        
        const url = '/api/transactions/' + (params.toString() ? '?' + params.toString() : '');
        const response = await fetch(url);
        const transactions = await response.json();
        
        const tbody = document.getElementById('transactions-list');
        tbody.innerHTML = '';
        
        if (transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11">Nenhuma transação encontrada</td></tr>';
            return;
        }
        
        transactions.forEach(t => {
            const purchaseDate = t.purchase_date ? new Date(t.purchase_date + 'T12:00:00').toLocaleDateString('pt-BR') : '-';
            const billDate = new Date(t.date + 'T12:00:00').toLocaleDateString('pt-BR');
            const categoryName = t.category_name || '-';
            const installmentInfo = (t.total_installments && t.total_installments > 1) ? `${t.installment_number}/${t.total_installments}` : '-';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="checkbox" class="transaction-checkbox" value="${t.id}" onchange="toggleTransactionSelection(${t.id})"></td>
                <td>${purchaseDate}</td>
                <td>${billDate}</td>
                <td>${t.bank_name}</td>
                <td>${t.card_name}</td>
                <td>${categoryName}</td>
                <td>${t.description}</td>
                <td>R$ ${t.amount.toFixed(2)}</td>
                <td>${installmentInfo}</td>
                <td>${t.is_paid ? 'Pago' : 'Pendente'}</td>
                <td>
                    ${t.group_id ? `<button class="btn btn-sm btn-outline-info" onclick="editGroup('${t.group_id}')" title="Editar Grupo">🔗</button> ` : ''}<button class="btn btn-sm btn-outline-primary" onclick="editTransaction(${t.id})" title="Editar">✏️</button>
                    <button class="btn btn-sm btn-outline-success" onclick="togglePayment(${t.id})" title="Alterar Status">✓</button>
                    ${t.group_id ? `<button class="btn btn-sm btn-outline-warning" onclick="deleteGroup('${t.group_id}')" title="Excluir Todas Parcelas">🗗</button> ` : ''}<button class="btn btn-sm btn-outline-danger" onclick="deleteTransaction(${t.id})" title="Excluir">🗑️</button>
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
        
        // Carregar categorias para o formulário
        const categoriesResponse = await fetch('/api/categories/');
        const categories = await categoriesResponse.json();
        
        const categorySelect = document.getElementById('category-select');
        if (categorySelect) {
            categorySelect.innerHTML = '<option value="">Sem categoria</option>';
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
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
            
            // Adicionar evento para filtrar cartões por banco
            dashBankSelect.addEventListener('change', function() {
                updateDashboardCardFilter(cards);
            });
        }
        
        // Adicionar evento para controlar filtro de mês baseado no ano
        const dashYearSelect = document.getElementById('dash-filter-year');
        const dashMonthSelect = document.getElementById('dash-filter-month');
        
        if (dashYearSelect && dashMonthSelect) {
            dashYearSelect.addEventListener('change', function() {
                if (!this.value) {
                    dashMonthSelect.value = '';
                    dashMonthSelect.disabled = true;
                } else {
                    dashMonthSelect.disabled = false;
                }
            });
            
            // Inicializar estado do filtro de mês
            dashMonthSelect.disabled = !dashYearSelect.value;
        }
        
        updateDashboardCardFilter(cards);
        
        // Carregar bancos para o filtro do gráfico de pizza
        const pieBankSelect = document.getElementById('pie-filter-bank');
        if (pieBankSelect) {
            pieBankSelect.innerHTML = '<option value="">Todos os bancos</option>';
            banks.forEach(bank => {
                const option = document.createElement('option');
                option.value = bank.id;
                option.textContent = bank.name;
                pieBankSelect.appendChild(option);
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
    document.getElementById('filter-status').value = '';
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

// Função para marcar compras anteriores como pagas
async function markPreviousAsPaid() {
    if (!confirm('Deseja marcar todas as compras de datas anteriores ao dia atual como pagas?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/transactions/mark-previous-as-paid`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const result = await response.json();
            clearSelection();
            loadData();
            alert(result.message);
        } else {
            alert('Erro ao marcar compras como pagas');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao marcar compras como pagas');
    }
}

// Expor funções globalmente
window.bulkUpdateStatus = bulkUpdateStatus;
window.clearSelection = clearSelection;
window.markPreviousAsPaid = markPreviousAsPaid;

async function loadBanksForDeposit() {
    try {
        const response = await fetch('/api/banks/');
        const banks = await response.json();
        
        const bankSelect = document.getElementById('deposit-bank');
        if (bankSelect) {
            bankSelect.innerHTML = '<option value="">Selecione o banco</option>';
            banks.forEach(bank => {
                const option = document.createElement('option');
                option.value = bank.id;
                option.textContent = bank.name;
                bankSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar bancos:', error);
    }
}

async function loadTransfers() {
    try {
        const response = await fetch('/api/deposits/');
        const deposits = await response.json();
        
        const tbody = document.getElementById('transfers-list');
        tbody.innerHTML = '';
        
        if (deposits.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">Nenhum depósito encontrado</td></tr>';
            return;
        }
        
        deposits.forEach(deposit => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(deposit.date).toLocaleDateString('pt-BR')}</td>
                <td>${deposit.bank_name}</td>
                <td>${deposit.description}</td>
                <td class="text-success">R$ ${deposit.amount.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Erro ao carregar depósitos:', error);
    }
}

// Funções do Dashboard
let expenseChart = null;

async function loadDashboard() {
    await loadTransactionFilters();
    await loadYearFilter();
    await loadExpenseChart();
    await loadCardPieChart();
}

async function loadYearFilter() {
    try {
        const response = await fetch('/api/transactions/');
        const transactions = await response.json();
        
        const years = new Set();
        transactions.forEach(t => {
            const year = new Date(t.date).getFullYear();
            years.add(year);
        });
        
        const yearSelect = document.getElementById('dash-filter-year');
        if (yearSelect) {
            yearSelect.innerHTML = '<option value="">Todos os anos</option>';
            Array.from(years).sort((a, b) => b - a).forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                yearSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar anos:', error);
    }
}

async function loadExpenseChart() {
    try {
        const params = new URLSearchParams();
        const bankId = document.getElementById('dash-filter-bank')?.value;
        const cardId = document.getElementById('dash-filter-card')?.value;
        const year = document.getElementById('dash-filter-year')?.value;
        const month = document.getElementById('dash-filter-month')?.value;
        
        // Validar se mês foi selecionado sem ano
        if (month && !year) {
            alert('Por favor, selecione um ano antes de escolher um mês específico.');
            document.getElementById('dash-filter-month').value = '';
            return;
        }
        
        if (bankId) params.append('bank_id', bankId);
        if (cardId) params.append('card_id', cardId);
        if (year) params.append('year', year);
        if (month) params.append('month', month);
        
        const url = '/api/summary/monthly-expenses' + (params.toString() ? '?' + params.toString() : '');
        const response = await fetch(url);
        let data = await response.json();
        
        // Determinar se estamos mostrando dias ou meses
        const showingDays = month && year;
        const chartTitle = showingDays ? 'Gastos Diários' : 'Gastos Mensais';
        
        // Atualizar título e badge
        const titleElement = document.getElementById('chart-title');
        const modeElement = document.getElementById('chart-mode');
        
        if (titleElement) {
            titleElement.textContent = chartTitle;
        }
        
        if (modeElement) {
            if (showingDays) {
                const monthNames = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                                  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
                modeElement.textContent = `${monthNames[parseInt(month)]} ${year}`;
                modeElement.style.display = 'inline';
            } else {
                modeElement.style.display = 'none';
            }
        }
        
        // Calcular total do período
        const periodTotal = data.reduce((sum, item) => sum + item.total, 0);
        const totalElement = document.getElementById('period-total');
        if (totalElement) {
            totalElement.textContent = 'R$ ' + periodTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
        }
        
        // Verificar se há dados
        if (data.length === 0) {
            const ctx = document.getElementById('expenseChart').getContext('2d');
            
            if (expenseChart) {
                expenseChart.destroy();
            }
            
            // Mostrar mensagem de sem dados
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.font = '16px Arial';
            ctx.fillStyle = '#6c757d';
            ctx.textAlign = 'center';
            ctx.fillText('Nenhum gasto encontrado para o período selecionado', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }
        
        const ctx = document.getElementById('expenseChart').getContext('2d');
        
        if (expenseChart) {
            expenseChart.destroy();
        }
        
        expenseChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.month),
                datasets: [{
                    label: chartTitle + ' (R$)',
                    data: data.map(item => item.total),
                    backgroundColor: showingDays ? 'rgba(255, 99, 132, 0.6)' : 'rgba(54, 162, 235, 0.6)',
                    borderColor: showingDays ? 'rgba(255, 99, 132, 1)' : 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'R$ ' + context.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
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
    document.getElementById('dash-filter-year').value = '';
    document.getElementById('dash-filter-month').value = '';
    
    // Reabilitar filtro de mês
    const dashMonthSelect = document.getElementById('dash-filter-month');
    if (dashMonthSelect) {
        dashMonthSelect.disabled = true;
    }
    
    loadExpenseChart();
}

function updateDashboardCardFilter(allCards) {
    const dashBankSelect = document.getElementById('dash-filter-bank');
    const dashCardSelect = document.getElementById('dash-filter-card');
    
    if (!dashCardSelect) return;
    
    const selectedBankId = dashBankSelect ? dashBankSelect.value : '';
    const filteredCards = selectedBankId ? 
        allCards.filter(card => card.bank_id.toString() === selectedBankId) : 
        allCards;
    
    dashCardSelect.innerHTML = '<option value="">Todos os cartões</option>';
    filteredCards.forEach(card => {
        const option = document.createElement('option');
        option.value = card.id;
        option.textContent = card.name;
        dashCardSelect.appendChild(option);
    });
}

let cardPieChart = null;

async function loadCardPieChart() {
    try {
        const params = new URLSearchParams();
        const bankId = document.getElementById('pie-filter-bank')?.value;
        const dateFrom = document.getElementById('pie-filter-date-from')?.value;
        const dateTo = document.getElementById('pie-filter-date-to')?.value;
        
        if (bankId) params.append('bank_id', bankId);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        
        const url = '/api/summary/card-expenses' + (params.toString() ? '?' + params.toString() : '');
        const response = await fetch(url);
        const data = await response.json();
        
        const ctx = document.getElementById('cardPieChart').getContext('2d');
        
        if (cardPieChart) {
            cardPieChart.destroy();
        }
        
        if (data.length === 0) {
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            ctx.font = '16px Arial';
            ctx.fillStyle = '#6c757d';
            ctx.textAlign = 'center';
            ctx.fillText('Nenhum gasto encontrado para o período selecionado', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }
        
        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ];
        
        cardPieChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(item => item.card),
                datasets: [{
                    data: data.map(item => item.total),
                    backgroundColor: colors.slice(0, data.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': R$ ' + context.parsed.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Erro ao carregar gráfico de pizza:', error);
    }
}

function applyPieFilters() {
    loadCardPieChart();
}

function clearPieFilters() {
    document.getElementById('pie-filter-bank').value = '';
    document.getElementById('pie-filter-date-from').value = '';
    document.getElementById('pie-filter-date-to').value = '';
    loadCardPieChart();
}

// Expor funções globalmente
window.applyDashboardFilters = applyDashboardFilters;
window.clearDashboardFilters = clearDashboardFilters;
window.loadDashboard = loadDashboard;
window.updateDashboardCardFilter = updateDashboardCardFilter;
window.applyPieFilters = applyPieFilters;
window.clearPieFilters = clearPieFilters;
window.showCategoryForm = showCategoryForm;
window.hideCategoryForm = hideCategoryForm;
window.deleteCategory = deleteCategory;
window.editTransaction = editTransaction;
window.editGroup = editGroup;
window.saveEdit = saveEdit;
window.toggleEditInstallments = toggleEditInstallments;
window.deleteGroup = deleteGroup;