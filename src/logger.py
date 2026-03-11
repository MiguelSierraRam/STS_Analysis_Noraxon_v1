# src/logger.py
# -*- coding: utf-8 -*-
"""
Módulo para logging centralizado y profesional.

Proporciona loggers pre-configurados para toda la aplicación.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_config


class LoggerManager:
    """Gestor centralizado de logging."""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def configure(cls, log_dir: Optional[str] = None):
        """
        Configurar logging basándose en config.yaml.
        
        Args:
            log_dir: Directorio custom para logs (override config.yaml)
        """
        if cls._configured:
            return
        
        config = get_config()
        log_config = config.get('logging', {})
        
        # Directorio de logs
        log_directory = log_dir or config.get('log_directory', 'data/logs')
        os.makedirs(log_directory, exist_ok=True)
        
        # Nivel de logging
        level_str = log_config.get('level', 'INFO')
        level = getattr(logging, level_str.upper(), logging.INFO)
        
        # Formato
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter(log_format)
        
        # Configurar root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()  # Limpiar handlers previos
        
        # Handler para archivo (rotating)
        log_file = os.path.join(log_directory, 'sts_analysis.log')
        max_bytes = log_config.get('file_size_mb', 10) * 1024 * 1024
        backup_count = log_config.get('backup_count', 5)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Handler para consola (si está habilitado)
        if log_config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        cls._configured = True
        
        # Log inicial
        root_logger.info("=" * 70)
        root_logger.info("STS Analysis Tool inicializado")
        root_logger.info(f"Nivel de logging: {level_str}")
        root_logger.info(f"Logs guardados en: {log_file}")
        root_logger.info("=" * 70)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtener logger para un módulo.
        
        Args:
            name: Nombre del módulo (__name__)
            
        Returns:
            Logger configurado
        """
        if not cls._configured:
            cls.configure()
        
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Función global para obtener loggers."""
    return LoggerManager.get_logger(name)
