import os
import shutil
import hashlib
from collections import defaultdict

def get_base_name(filename):
    """Extrae el nombre base antes del último guion bajo (antes del número final)."""
    name = os.path.splitext(filename)[0]  # Quita la extensión
    parts = name.rsplit('_', 1)  # Divide desde el último _
    return parts[0] if len(parts) == 2 else name

def compute_file_hash(filepath):
    """Calcula un hash del contenido del archivo para comparar si son iguales."""
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def move_duplicates_to_folder(directory):
    # Ruta de la carpeta de duplicados
    duplicates_folder = os.path.join(directory, "duplicados")
    os.makedirs(duplicates_folder, exist_ok=True)

    # Obtener todos los archivos CSV
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    
    if not csv_files:
        print("No se encontraron archivos CSV en el directorio.")
        return

    # Agrupar por nombre base
    grouped_files = defaultdict(list)
    for filename in csv_files:
        base_name = get_base_name(filename)
        grouped_files[base_name].append(filename)
    
    moved_files = []

    for base_name, file_list in grouped_files.items():
        if len(file_list) < 2:
            continue  # No hay duplicados potenciales

        # Calcular hash del contenido para cada archivo
        file_with_hash = []
        for filename in file_list:
            filepath = os.path.join(directory, filename)
            if os.path.exists(filepath):  # Verifica que exista
                file_hash = compute_file_hash(filepath)
                file_with_hash.append((filename, file_hash))

        # Agrupar por contenido (hash)
        content_groups = defaultdict(list)
        for filename, file_hash in file_with_hash:
            content_groups[file_hash].append(filename)

        # Procesar cada grupo de contenido idéntico
        for file_group in content_groups.values():
            if len(file_group) > 1:
                # Dejar el primero en la carpeta raíz, mover los demás
                keep = file_group[0]
                duplicates = file_group[1:]
                
                for duplicate in duplicates:
                    src = os.path.join(directory, duplicate)
                    dst = os.path.join(duplicates_folder, duplicate)
                    
                    try:
                        shutil.move(src, dst)
                        moved_files.append(duplicate)
                        print(f"Movido: {duplicate} → duplicados/")
                    except Exception as e:
                        print(f"Error moviendo {duplicate}: {e}")

    print("\nResumen:")
    print(f"Archivos movidos a 'duplicados/': {len(moved_files)}")
    if moved_files:
        for f in moved_files:
            print(f"  - {f}")
    else:
        print("No se encontraron duplicados para mover.")

# --- Ejecución ---
if __name__ == "__main__":
    directory = "articulos_x_procesar_ElHeraldo_Duplicados"  # ⚠️ Cambia esto por tu ruta real
    move_duplicates_to_folder(directory)