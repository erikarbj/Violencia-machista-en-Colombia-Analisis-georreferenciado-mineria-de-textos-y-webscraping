import os
import shutil
import hashlib
from collections import defaultdict

def compute_file_hash(filepath):
    """Calcula un hash del contenido del archivo (binario) para comparar igualdad."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"❌ Error leyendo {filepath}: {e}")
        return None

def remove_duplicate_files_by_content(directory):
    # Ruta de la carpeta de duplicados
    duplicates_folder = os.path.join(directory, "duplicados")
    os.makedirs(duplicates_folder, exist_ok=True)

    # Obtener todos los archivos CSV del directorio
    csv_files = [
        f for f in os.listdir(directory)
        if f.endswith('.csv') and os.path.isfile(os.path.join(directory, f))
    ]

    if not csv_files:
        print("⚠️ No se encontraron archivos CSV en el directorio.")
        return

    print(f"🔍 Se encontraron {len(csv_files)} archivos CSV.")

    # Diccionario: hash → lista de archivos con ese contenido
    content_groups = defaultdict(list)

    # Calcular hash de cada archivo
    for filename in csv_files:
        filepath = os.path.join(directory, filename)
        file_hash = compute_file_hash(filepath)
        if file_hash:
            content_groups[file_hash].append(filename)

    # Contador de archivos movidos
    moved_files = []

    print(f"\n📦 Grupos de contenido idéntico encontrados: {len(content_groups)}")
    for file_hash, group in content_groups.items():
        if len(group) > 1:
            # Dejar el primero, mover los demás
            keep = group[0]
            duplicates = group[1:]
            print(f"\n📝 Contenido: {file_hash[:10]}...")
            print(f"   ✅ Conservado: {keep}")
            for dup in duplicates:
                src = os.path.join(directory, dup)
                dst = os.path.join(duplicates_folder, dup)
                try:
                    shutil.move(src, dst)
                    moved_files.append(dup)
                    print(f"   🚚 Movido: {dup}")
                except Exception as e:
                    print(f"   ❌ Error moviendo {dup}: {e}")
        else:
            print(f"\n📝 Contenido único: {file_hash[:10]}... → {group[0]} (sin duplicados)")

    # Resumen final
    print("\n" + "="*60)
    print("✅ RESUMEN")
    print("="*60)
    if moved_files:
        print(f"Se movieron {len(moved_files)} archivos duplicados a 'duplicados/':")
        for f in moved_files:
            print(f"  ➤ {f}")
    else:
        print("No se encontraron archivos con contenido duplicado.")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    # ⚠️ Cambia esta ruta a la carpeta donde están tus archivos CSV
    directory = "articulos_x_procesar_ElUniversal_Duplicados"  # ← AJUSTA ESTA RUTA
    remove_duplicate_files_by_content(directory)