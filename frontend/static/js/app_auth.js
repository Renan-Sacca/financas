// Salvar fetch original
const originalFetch = window.fetch;

// Substituir window.fetch para interceptar chamadas da API
window.fetch = function(url, options = {}) {
    // Se é uma chamada para API (exceto auth), usar autenticação
    if (url.startsWith('/api/') && !url.includes('/api/auth/')) {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return Promise.reject('No token');
        }
        
        const headers = {
            'Authorization': 'Bearer ' + token,
            ...options.headers
        };
        
        return originalFetch(url, { ...options, headers })
            .then(response => {
                if (response.status === 401) {
                    localStorage.removeItem('token');
                    window.location.href = '/login';
                    throw new Error('Unauthorized');
                }
                return response;
            });
    }
    
    // Para outras URLs, usar fetch normal
    return originalFetch(url, options);
};

// Carregar app.js após configurar interceptação
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAppJS);
} else {
    loadAppJS();
}

function loadAppJS() {
    console.log('Carregando app.js...');
    const script = document.createElement('script');
    script.src = '/static/js/app.js?v=' + Date.now();
    script.onload = function() {
        console.log('app.js carregado com sucesso');
    };
    script.onerror = function() {
        console.error('Erro ao carregar app.js');
    };
    document.head.appendChild(script);
}