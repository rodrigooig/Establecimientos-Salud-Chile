import pandas as pd
import re
import unicodedata
import os
import sys
from datetime import datetime

def normalize_text(text):
    """
    Normaliza un texto:
    - Elimina espacios adicionales
    - Normaliza acentos y caracteres especiales
    - Normaliza mayúsculas/minúsculas en palabras clave
    """
    if pd.isna(text) or text == '':
        return text
    
    # Convertir a string si no lo es
    text = str(text)
    
    # Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Normalizar palabras como "Región"
    text = text.replace('Region ', 'Región ')
    
    # Para palabras como "Del", "De", etc. después de "Región"
    text = re.sub(r'Región\s+Del\s+', 'Región De ', text, flags=re.IGNORECASE)
    text = re.sub(r'Región\s+de\s+la\s+', 'Región De La ', text, flags=re.IGNORECASE)
    text = re.sub(r'Región\s+de\s+los\s+', 'Región De Los ', text, flags=re.IGNORECASE)
    
    # Normalizar otras preposiciones y artículos comunes
    words = text.split()
    for i, word in enumerate(words):
        if i > 0 and word.lower() in ['de', 'del', 'la', 'las', 'los', 'y']:
            words[i] = word.lower()
            if word.lower() == 'y':  # Para casos como "Metropolitana de Santiago"
                words[i] = 'y'
        elif i > 0 and word.lower() == 'del':
            words[i] = 'de' if words[i-1].lower() != 'región' else 'De'
    
    return ' '.join(words)

def normalize_columns(df):
    """
    Aplica normalización a columnas específicas del dataframe
    """
    text_columns = [
        'EstablecimientoGlosa', 'RegionGlosa', 'SeremiSaludGlosa_ServicioDeSaludGlosa',
        'TipoPertenenciaEstabGlosa', 'TipoEstablecimientoGlosa', 'AmbitoFuncionamiento',
        'DependenciaAdministrativa', 'NivelAtencionEstabglosa', 'ComunaGlosa',
        'TipoViaGlosa', 'NombreVia', 'TipoUrgencia', 'ClasificacionTipoSapu',
        'TipoSistemaSaludGlosa', 'EstadoFuncionamiento', 'NivelComplejidadEstabGlosa',
        'TipoAtencionEstabGlosa'
    ]
    
    total_columns = len(text_columns)
    for i, col in enumerate(text_columns):
        if col in df.columns:
            print(f"[{i+1}/{total_columns}] Normalizando columna: {col}")
            df[col] = df[col].apply(normalize_text)
            # Mostrar algunos ejemplos después de la normalización
            unique_values = df[col].dropna().drop_duplicates().head(3).tolist()
            if unique_values:
                print(f"  Ejemplos después de normalización: {unique_values}")
    
    return df

def main():
    input_file = 'data/establecimientos_20250225.csv'
    output_file = 'data/establecimientos_cleaned.csv'
    
    # Verificar si el archivo existe
    if not os.path.exists(input_file):
        print(f"Error: El archivo {input_file} no existe.")
        sys.exit(1)
    
    print(f"Iniciando proceso de limpieza: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Tamaño del archivo: {os.path.getsize(input_file) / (1024*1024):.2f} MB")
    
    try:
        print("Leyendo archivo CSV...")
        # Usar chunksize para archivos grandes
        df = pd.read_csv(input_file, sep=';', encoding='utf-8', dtype=str, low_memory=False)
        
        print(f"Filas antes de limpieza: {len(df)}")
        print(f"Columnas: {', '.join(df.columns.tolist())}")
        
        # Mostrar algunos ejemplos de regiones antes de la normalización
        if 'RegionGlosa' in df.columns:
            print("\nEjemplos de regiones antes de normalización:")
            region_examples = df['RegionGlosa'].drop_duplicates().tolist()
            for r in region_examples:
                print(f"  - {r}")
        
        # Aplicar normalización
        print("\nAplicando normalización a los datos...")
        df = normalize_columns(df)
        
        # Mostrar algunos ejemplos después de la normalización
        if 'RegionGlosa' in df.columns:
            print("\nEjemplos de regiones después de normalización:")
            region_examples = df['RegionGlosa'].drop_duplicates().tolist()
            for r in region_examples:
                print(f"  - {r}")
        
        # Guardar el archivo limpio
        print(f"\nGuardando archivo limpio en {output_file}...")
        df.to_csv(output_file, sep=';', index=False, encoding='utf-8')
        
        print(f"Proceso completado: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Archivo guardado como '{output_file}'")
        print(f"Filas después de limpieza: {len(df)}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 