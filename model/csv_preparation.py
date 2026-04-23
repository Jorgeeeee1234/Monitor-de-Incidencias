import pandas as pd
import os

# --- CONFIGURACIÓN ---
# Rutas a los archivos CSV
benign_files = {
    "benign_samples_1.csv": "benign_samples_1",
    "benign_samples_2.csv": "benign_samples_2"
}

prompt_injection_file = "prompt_injection_dataset.csv"
harmful_file = "harmful_content.csv"

# --- FUNCIÓN PARA CARGAR Y REPARAR MALFORMADOS ---
def load_malformed_csv(filepath):
    """
    Carga CSVs malformados donde text y label están envueltos en comillas.
    Intenta primero utf-8, luego latin-1 si falla.
    """
    data = []
    for encoding in ['utf-8', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                for i, line in enumerate(f):
                    if i == 0:
                        continue
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('"') and line.endswith('"'):
                        line = line[1:-1]
                    if ',""' in line:
                        text_part, label_part = line.rsplit(',""', 1)
                        label_str = label_part.rstrip('"')
                        try:
                            label_value = int(label_str)
                            data.append({"text": text_part, "label": label_value})
                        except ValueError:
                            continue
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error al cargar {filepath} con encoding {encoding}: {e}")
    return pd.DataFrame()


# --- FUNCIÓN PARA NORMALIZAR COLUMNAS ---
def normalize_df(df, default_label_name=None, default_source=None):
    """
    Normaliza los dataframes a un formato consistente con 4 columnas:
    text, label, label_name, source
    """
    if "text" not in df.columns:
        raise ValueError(f"Falta columna 'text'. Columnas encontradas: {list(df.columns)}")
    
    if "label" not in df.columns:
        raise ValueError(f"Falta columna 'label'. Columnas encontradas: {list(df.columns)}")
    
    if "label_name" not in df.columns:
        df["label_name"] = default_label_name
    
    if "source" not in df.columns:
        df["source"] = default_source
    
    df = df[["text", "label", "label_name", "source"]].copy()
    df["text"] = df["text"].astype(str).str.strip()
    
    return df


# --- CARGAR BENIGN ---
print("Cargando archivos benign...")
benign_dfs = []
for file, source_name in benign_files.items():
    if not os.path.exists(file):
        print(f"  ⚠️  Archivo no encontrado: {file}")
        continue
    
    print(f"  Cargando {file}...")
    df = pd.read_csv(file)
    df = normalize_df(df, default_label_name="benign", default_source=source_name)
    benign_dfs.append(df)
    print(f"    ✓ {len(df)} muestras")

benign_df = pd.concat(benign_dfs, ignore_index=True) if benign_dfs else pd.DataFrame()
print(f"Total benign: {len(benign_df)}\n")


# --- CARGAR PROMPT INJECTION ---
print("Cargando prompt injection...")
if os.path.exists(prompt_injection_file):
    prompt_df = load_malformed_csv(prompt_injection_file)
    if len(prompt_df) > 0:
        prompt_df = normalize_df(prompt_df, default_label_name="prompt_injection", 
                                default_source="prompt_injection_dataset")
        print(f"  ✓ {len(prompt_df)} muestras\n")
    else:
        print(f"  ⚠️  No se pudieron cargar filas. Intentando con pandas.read_csv()...")
        prompt_df = pd.read_csv(prompt_injection_file)
        prompt_df = normalize_df(prompt_df, default_label_name="prompt_injection", 
                                default_source="prompt_injection_dataset")
        print(f"  ✓ {len(prompt_df)} muestras\n")
else:
    print(f"  ⚠️  Archivo no encontrado: {prompt_injection_file}\n")
    prompt_df = pd.DataFrame()


# --- CARGAR HARMFUL CONTENT ---
print("Cargando harmful content...")
if os.path.exists(harmful_file):
    harmful_df = load_malformed_csv(harmful_file)
    if len(harmful_df) > 0:
        harmful_df = normalize_df(harmful_df, default_label_name="harmful_content", 
                                 default_source="harmful_content")
        print(f"  ✓ {len(harmful_df)} muestras\n")
    else:
        print(f"  ⚠️  No se pudieron cargar filas. Intentando con pandas.read_csv()...")
        try:
            harmful_df = pd.read_csv(harmful_file, encoding='utf-8')
        except UnicodeDecodeError:
            harmful_df = pd.read_csv(harmful_file, encoding='latin-1')
        harmful_df = normalize_df(harmful_df, default_label_name="harmful_content", 
                                 default_source="harmful_content")
        print(f"  ✓ {len(harmful_df)} muestras\n")
else:
    print(f"  ⚠️  Archivo no encontrado: {harmful_file}\n")
    harmful_df = pd.DataFrame()


# --- UNIFICAR TODO ---
print("Unificando datasets...")
dfs_to_concat = [df for df in [benign_df, prompt_df, harmful_df] if len(df) > 0]
if dfs_to_concat:
    final_df = pd.concat(dfs_to_concat, ignore_index=True)
    print(f"  ✓ {len(final_df)} muestras totales")
    
    print("\nEstadísticas por categoría:")
    for category in final_df["label_name"].unique():
        count = len(final_df[final_df["label_name"] == category])
        print(f"  {category}: {count} muestras")
    
    print("\nMezclando dataset...")
    final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    output_file = "dataset_unificado.csv"
    final_df.to_csv(output_file, index=False)
    print(f"✓ Dataset final guardado en: {output_file}")
    print(f"✓ Total de muestras: {len(final_df)}")
else:
    print("❌ No se pudieron cargar ninguno de los datasets")
