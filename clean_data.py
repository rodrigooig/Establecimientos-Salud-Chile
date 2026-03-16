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
    "ComunaGlosa",
    "DependenciaAdministrativa",
    "TipoAtencionEstabGlosa",
    "TipoUrgencia"
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

    def smart_capitalize(w):
        """Capitaliza respetando prefijos no-alfabéticos como paréntesis."""
        match = re.match(r'^([^a-zA-ZáéíóúñÁÉÍÓÚÑ]*)(.*)', w)
        if match and match.group(2):
            prefix, rest = match.group(1), match.group(2)
            return prefix + rest.capitalize()
        return w.capitalize()

    for i, word in enumerate(words):
        if not word:
            continue

        # Strip non-alpha prefix for checks
        alpha_part = re.sub(r'^[^a-zA-ZáéíóúñÁÉÍÓÚÑ]+', '', word)
        is_acronym = len(alpha_part) >= 2 and alpha_part.isupper()
        is_minor_word = alpha_part.lower() in minor_words

        if i == 0:
            normalized_words.append(word if is_acronym else smart_capitalize(word))
        elif is_acronym:
            normalized_words.append(word)
        elif is_minor_word and not capitalize_minor_words:
            normalized_words.append(word.lower())
        else:
            normalized_words.append(smart_capitalize(word))

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


def add_plaza_edf(df, plazas_file='data/Plazas RM - Hoja 1.csv'):
    """
    Cruza los establecimientos con el dataset de Plazas EDF de la RM.
    Agrega columna booleana PlazaEDF al dataframe.
    """
    if not os.path.exists(plazas_file):
        print(f"Archivo de plazas no encontrado: {plazas_file}, saltando cruce.")
        df['PlazaEDF'] = False
        return df

    def norm_match(s):
        if pd.isna(s): return ''
        s = str(s).upper().strip()
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        return re.sub(r'\s+', ' ', s)

    plazas = pd.read_csv(plazas_file)
    print(f"\nCruzando con Plazas EDF ({len(plazas)} registros)...")

    plazas['_n'] = plazas['ESTABLECIMIENTO'].apply(norm_match)
    plazas['_c'] = plazas['COMUNA'].apply(norm_match)

    # Build lookup: (norm_name, norm_comuna) -> servicio de salud
    plazas_lookup = {}
    for _, row in plazas.iterrows():
        plazas_lookup[(row['_n'], row['_c'])] = row['SERVICIO DE SALUD']

    # Manual mappings for names that differ between datasets
    manual_mappings = {
        (norm_match('CESFAM la Reina de Colina'), norm_match('Colina')):
            (norm_match('CENTRO DE SALUD FAMILIAR LA REINA'), norm_match('Colina')),
        (norm_match('Centro de Salud Familiar Alberto Bachelet Martínez'), norm_match('Conchalí')):
            (norm_match('CENTRO DE SALUD FAMILIAR ALBERTO BACHELET'), norm_match('Conchalí')),
        (norm_match('Centro de Salud Familiar Juan Pablo II de Lampa'), norm_match('Lampa')):
            (norm_match('CENTRO DE SALUD FAMILIAR JUAN PABLO SEGUNDO'), norm_match('Lampa')),
        (norm_match('Centro de Salud Familiar Irene Frei de Cid'), norm_match('Quilicura')):
            (norm_match('CENTRO DE SALUD FAMILIAR IRENE FREI'), norm_match('Quilicura')),
        (norm_match('Centro de Salud Familiar Juan Pablo II ( Padre Hurtado)'), norm_match('Padre Hurtado')):
            (norm_match('CENTRO DE SALUD FAMILIAR JUAN PABLO II'), norm_match('Padre Hurtado')),
    }
    for estab_key, plaza_key in manual_mappings.items():
        if plaza_key in plazas_lookup:
            plazas_lookup[estab_key] = plazas_lookup[plaza_key]

    df['_n'] = df['EstablecimientoGlosa'].apply(norm_match)
    df['_c'] = df['ComunaGlosa'].apply(norm_match)

    def get_servicio(row):
        key = (row['_n'], row['_c'])
        return plazas_lookup.get(key, '')

    df['PlazaEDF'] = df.apply(lambda r: (r['_n'], r['_c']) in plazas_lookup, axis=1)
    df['ServicioSaludEDF'] = df.apply(get_servicio, axis=1)
    df = df.drop(columns=['_n', '_c'])

    matched = df['PlazaEDF'].sum()
    print(f"Plazas EDF cruzadas: {matched}/{len(plazas)}")
    return df


def main():
    input_file = 'data/establecimientos_20260310.csv'
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

        # Standardize TieneServicioUrgencia values
        if 'TieneServicioUrgencia' in df.columns:
            urgencia_map = {'SI': 'SI', 'Si': 'SI', 'si': 'SI', 'NO': 'NO', 'No': 'NO', 'no': 'NO'}
            df['TieneServicioUrgencia'] = df['TieneServicioUrgencia'].map(urgencia_map).fillna(df['TieneServicioUrgencia'])
            print(f"\nTieneServicioUrgencia estandarizado: {df['TieneServicioUrgencia'].value_counts().to_dict()}")

        print("\nAplicando normalización a los datos...")
        df = normalize_columns(df)

        if 'RegionGlosa' in df.columns:
            print("\nEjemplos de regiones DESPUÉS de normalización:")
            print(df['RegionGlosa'].drop_duplicates().head(10).tolist())

        df = add_plaza_edf(df)

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