"""
Ponto de configuração externo opcional na raiz do projeto.
Reexporta as configurações definidas em app.config para máxima compatibilidade.
"""
from app.config import Config, DevelopmentConfig, TestingConfig, ProductionConfig, config_by_name

__all__ = ['Config', 'DevelopmentConfig', 'TestingConfig', 'ProductionConfig', 'config_by_name']

