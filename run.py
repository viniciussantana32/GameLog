import os
from app import create_app

# Criação da instância da aplicação através da Application Factory
app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    # Inicialização do servidor embutido para ambiente de desenvolvimento local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

