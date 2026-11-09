/**
 * Meus Jogos - Scripts Específicos da Área de Jogos (games.js)
 * Gerenciamento do Modal de Confirmação de Exclusão e Interações com Jogos
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Gerenciamento do Modal de Exclusão
    const deleteModal = document.getElementById('deleteModal');
    const deleteForm = document.getElementById('deleteForm');
    const deleteGameTitle = document.getElementById('deleteGameTitle');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const closeDeleteModalBtn = document.getElementById('closeDeleteModalBtn');

    // Abre o modal ao clicar em qualquer botão com a classe .btn-trigger-delete
    const triggerButtons = document.querySelectorAll('.btn-trigger-delete');
    triggerButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const gameId = button.getAttribute('data-id');
            const gameTitle = button.getAttribute('data-title');

            if (deleteModal && deleteForm) {
                // Atualiza a action do formulário com a rota de exclusão do jogo
                deleteForm.action = `/jogos/${gameId}/excluir`;
                
                if (deleteGameTitle) {
                    deleteGameTitle.textContent = gameTitle || 'este jogo';
                }

                // Exibe o modal
                deleteModal.classList.add('active');
            }
        });
    });

    // Função para fechar o modal
    const fecharModal = () => {
        if (deleteModal) {
            deleteModal.classList.remove('active');
        }
    };

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', fecharModal);
    }

    if (closeDeleteModalBtn) {
        closeDeleteModalBtn.addEventListener('click', fecharModal);
    }

    // Fechar ao clicar no fundo escuro do modal
    if (deleteModal) {
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                fecharModal();
            }
        });
    }

    // 2. Auxiliar visual para campo de nota no formulário (create/edit)
    const notaInput = document.getElementById('nota');
    if (notaInput) {
        notaInput.addEventListener('input', () => {
            let val = parseFloat(notaInput.value);
            if (val > 10) notaInput.value = 10;
            if (val < 0) notaInput.value = 0;
        });
    }
});

