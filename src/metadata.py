"""
Lectura y manejo de metadatos de archivos Noraxon.
"""

from typing import Optional, Dict, Any
import pandas as pd


def read_metadata(file_path: str, default_mass_kg: Optional[float] = None) -> Dict[str, Any]:
    """
    Lee metadatos de la hoja 'MetaData_&_Parameters' en un archivo Excel Noraxon.
    
    Estructura esperada:
    - Row 1: [empty, Codigo]
    - Row 2: [empty, Altura]
    - Row 3: [empty, Peso_kg]
    - Row 4: [empty, Test]
    - Row 5: [empty, Fecha_Test]
    - Row 6: [empty, Altura_silla]
    
    Args:
        file_path: Ruta del archivo Excel.
        default_mass_kg: Masa por defecto si no se encuentra en Excel.
        
    Returns:
        Dict con metadatos.
    """
    metadata = {
        'Codigo': None,
        'Altura': None,
        'Peso_kg': default_mass_kg,
        'Altura_silla': None,
        'Test': None,
        'Fecha_Test': None,
    }
    
    try:
        meta_df = pd.read_excel(
            file_path,
            sheet_name='MetaData_&_Parameters',
            engine='openpyxl',
            header=None
        )
        
        # Índices 1-based del Excel
        if meta_df.shape[0] > 1 and meta_df.shape[1] > 1:
            metadata['Codigo'] = meta_df.iloc[1, 1]
        if meta_df.shape[0] > 2 and meta_df.shape[1] > 1:
            metadata['Altura'] = meta_df.iloc[2, 1]
        if meta_df.shape[0] > 3 and meta_df.shape[1] > 1:
            peso = meta_df.iloc[3, 1]
            if peso is not None:
                metadata['Peso_kg'] = peso
        if meta_df.shape[0] > 4 and meta_df.shape[1] > 1:
            metadata['Test'] = meta_df.iloc[4, 1]
        if meta_df.shape[0] > 5 and meta_df.shape[1] > 1:
            metadata['Fecha_Test'] = meta_df.iloc[5, 1]
        if meta_df.shape[0] > 6 and meta_df.shape[1] > 1:
            metadata['Altura_silla'] = meta_df.iloc[6, 1]
    
    except Exception:
        pass  # Si falla, usamos valores por defecto
    
    return metadata
