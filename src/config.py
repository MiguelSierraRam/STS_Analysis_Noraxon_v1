# src/config.py
# -*- coding: utf-8 -*-
"""
Módulo para manejo centralizado de configuración.

Carga parámetros desde config.yaml y permite overrides desde CLI.
"""

import os
from typing import Dict, Any, Optional
import yaml


class Config:
    """Gestor centralizado de configuración."""
    
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        """Singleton pattern para Config."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializar configuración desde config.yaml."""
        if hasattr(self, '_loaded'):
            return
        
        self._loaded = True
        self._config: Dict[str, Any] = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Cargar configuración por defecto desde config.yaml."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: No se pudo cargar config.yaml: {e}")
                self._config = {}
        else:
            print(f"Warning: No se encontró config.yaml en {config_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración.
        
        Args:
            key: Clave (puede usar notación dot: 'logging.level')
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        if '.' in key:
            keys = key.split('.')
            value = self._config
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
            return value if value is not None else default
        
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Establecer valor de configuración (para overrides CLI).
        
        Args:
            key: Clave de configuración
            value: Nuevo valor
        """
        if '.' in key:
            keys = key.split('.')
            config = self._config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
        else:
            self._config[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Retornar configuración completa como dict."""
        return dict(self._config)
    
    def __repr__(self) -> str:
        return f"Config({self._config})"


def load_config(config_file: Optional[str] = None) -> Config:
    """
    Cargar configuración.
    
    Args:
        config_file: Ruta personalizada a config.yaml (opcional)
        
    Returns:
        Instancia de Config (singleton)
    """
    config = Config()
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                custom = yaml.safe_load(f) or {}
                for key, value in custom.items():
                    config.set(key, value)
        except Exception as e:
            print(f"Warning: No se pudo cargar {config_file}: {e}")
    return config


def get_config() -> Config:
    """Obtener instancia global de Config."""
    return Config()
