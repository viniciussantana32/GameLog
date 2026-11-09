document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('catalogLoadMore');
    const grid = document.getElementById('apiGamesGrid');
    const errorMessage = document.getElementById('catalogLoadMoreError');

    if (!button || !grid || !errorMessage) {
        return;
    }

    button.addEventListener('click', async () => {
        if (button.disabled) {
            return;
        }

        button.disabled = true;
        button.textContent = 'Carregando...';

        const params = new URLSearchParams({
            busca: button.dataset.busca || '',
            categoria: button.dataset.categoria || '',
            plataforma: button.dataset.plataforma || '',
            ordenacao: button.dataset.ordenacao || '',
            offset: button.dataset.offset || '0'
        });

        try {
            const response = await fetch(`${button.dataset.url}?${params}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!response.ok) {
                throw new Error(`Falha ao carregar mais jogos (${response.status}).`);
            }

            const result = await response.json();
            errorMessage.hidden = true;
            errorMessage.textContent = '';
            const fragment = document.createElement('template');
            fragment.innerHTML = result.html;
            const existingIds = new Set(
                Array.from(grid.querySelectorAll('[data-game-id]'))
                    .map(card => card.dataset.gameId)
            );

            Array.from(fragment.content.querySelectorAll('[data-game-id]')).forEach(card => {
                if (!existingIds.has(card.dataset.gameId)) {
                    grid.append(card);
                    existingIds.add(card.dataset.gameId);
                }
            });

            button.dataset.offset = String(Number(button.dataset.offset || 0) + result.count);
            button.hidden = !result.has_more;
        } catch (error) {
            console.error(error);
            errorMessage.textContent = 'Não foi possível carregar mais jogos. Verifique sua conexão e tente novamente.';
            errorMessage.hidden = false;
            button.textContent = 'Tentar novamente';
            return;
        } finally {
            button.disabled = false;
        }

        button.textContent = 'Carregar mais';
    });
});
