import pandas as pd
import re
import unicodedata
import os
import sys
from datetime import datetime

# Define the columns needed by the Streamlit app
COLUMNS_TO_KEEP = [
    "RegionGlosa",
    "TipoEstablecimientoGlosa",
    "TipoSistemaSaludGlosa",
    "EstadoFuncionamiento",
    "TieneServicioUrgencia",
    "NivelAtencionEstabglosa",
    "NivelComplejidadEstabGlosa",
    "FechaInicioFuncionamientoEstab",
    "Latitud",
    "Longitud",
    "EstablecimientoGlosa",
    "ComunaGlosa"
]

def normalize_text(text, capitalize_minor_words=False):
    """
    Normaliza un texto:
    - Elimina espacios adicionales.
    - Normaliza acentos y caracteres especiales (handled by default string methods/regex flags where needed).
    - Aplica capitalización específica:
        - Title Case para la mayoría de palabras.
        - Minúsculas para artículos/preposiciones específicos (default) O Title Case.
        - Mantiene siglas/acrónimos en mayúsculas.

    Args:
        text (str): El texto a normalizar.
        capitalize_minor_words (bool): Si es True, capitaliza también las palabras menores.
                                      Si es False (default), las mantiene en minúsculas.
    """
    if pd.isna(text) or text == '':
        return text

    text = str(text)

    # 1. Normalizar espacios múltiples y trim inicial
    text = re.sub(r'\s+', ' ', text.strip())

    # 2. Corregir "Region" a "Región"
    text = text.replace('Region ', 'Región ')

    # 3. Aplicar Capitalización Específica
    words = text.split(' ')
    normalized_words = []
    minor_words = ['de', 'del', 'la', 'las', 'los', 'y', 'en']

    for i, word in enumerate(words):
        if not word:
            continue

        is_acronym = len(word) >= 2 and word.isupper()
        is_minor_word = word.lower() in minor_words

        if i == 0:
            # Capitalize the first word (unless it's an acronym)
            normalized_words.append(word if is_acronym else word.capitalize())
        elif is_acronym:
            # Keep acronyms uppercase
            normalized_words.append(word)
        elif is_minor_word and not capitalize_minor_words:
            # Keep minor words lowercase (default behavior)
            normalized_words.append(word.lower())
        else:
            # Capitalize other words (or minor words if capitalize_minor_words is True)
            normalized_words.append(word.capitalize())

    text = ' '.join(normalized_words)

    # 4. Final check for double spaces (just in case) and strip
    text = re.sub(r'\s+', ' ', text.strip())

    return text

def normalize_columns(df):
    """
    Aplica normalización a columnas específicas del dataframe
    """
    # Original list of columns that *might* need text normalization
    potential_text_columns = [
        'EstablecimientoGlosa', 'RegionGlosa', 'SeremiSaludGlosa_ServicioDeSaludGlosa',
        'TipoPertenenciaEstabGlosa', 'TipoEstablecimientoGlosa', 'AmbitoFuncionamiento',
        'DependenciaAdministrativa', 'NivelAtencionEstabglosa', 'ComunaGlosa',
        'TipoViaGlosa', 'NombreVia', 'TipoUrgencia', 'ClasificacionTipoSapu',
        'TipoSistemaSaludGlosa', 'EstadoFuncionamiento', 'NivelComplejidadEstabGlosa',
        'TipoAtencionEstabGlosa'
    ]

    # Filter this list to only include columns that we actually kept
    text_columns_to_normalize = [col for col in potential_text_columns if col in df.columns]

    region_col_name = 'RegionGlosa'
    total_columns = len(text_columns_to_normalize)
    processed_count = 0

    for col in text_columns_to_normalize:
        processed_count += 1
        print(f"[{processed_count}/{total_columns}] Normalizando columna: {col}")

        # Choose the normalization behavior based on the column
        if col == region_col_name:
            print(f"  Aplicando capitalización total (Title Case) a '{col}'")
            df[col] = df[col].apply(lambda x: normalize_text(x, capitalize_minor_words=True))
        else:
            df[col] = df[col].apply(normalize_text)

        # Mostrar algunos ejemplos después de la normalización
        unique_values = df[col].dropna().drop_duplicates().head(3).tolist()
        if unique_values:
            print(f"  Ejemplos después de normalización: {unique_values}")

    return df

def main():
    input_file = 'data/establecimientos.csv'
    output_file = 'data/establecimientos_cleaned.csv'

    if not os.path.exists(input_file):
        print(f"Error: El archivo {input_file} no existe.")
        sys.exit(1)

    print(f"Iniciando proceso de limpieza: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Columnas a mantener: {COLUMNS_TO_KEEP}")

    try:
        print("Leyendo archivo CSV (solo columnas necesarias)...")
        # Use usecols to load only necessary data
        df = pd.read_csv(
            input_file,
            sep=';',
            encoding='utf-8',
            dtype=str, # Read all as string initially to handle mixed types
            low_memory=False,
            usecols=COLUMNS_TO_KEEP
        )

        print(f"Filas leídas: {len(df)}")
        print(f"Columnas cargadas: {df.columns.tolist()}")

        # Convert Lat/Lon to numeric after loading as string (handle potential errors)
        for col in ['Latitud', 'Longitud']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')

        if 'RegionGlosa' in df.columns:
            print("\nEjemplos de regiones ANTES de normalización:")
            print(df['RegionGlosa'].drop_duplicates().head(10).tolist())

        print("\nAplicando normalización a los datos...")
        df = normalize_columns(df)

        if 'RegionGlosa' in df.columns:
            print("\nEjemplos de regiones DESPUÉS de normalización:")
            print(df['RegionGlosa'].drop_duplicates().head(10).tolist())

        print(f"\nGuardando archivo limpio en {output_file}...")
        df.to_csv(output_file, sep=';', index=False, encoding='utf-8')

        print(f"Proceso completado: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Archivo guardado como '{output_file}' con {len(df.columns)} columnas.")

    except ValueError as e:
        if "'usecols' do not match columns" in str(e):
            print(f"\nError: Las columnas especificadas en COLUMNS_TO_KEEP no coinciden exactamente con las cabeceras del archivo CSV.")
            print("Verifica los nombres en COLUMNS_TO_KEEP y en el archivo CSV.")
        else:
            print(f"Error durante el procesamiento: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 