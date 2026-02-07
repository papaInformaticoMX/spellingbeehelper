import sqlite3
import csv
import os

# Nombres de archivos
DB_NAME = "vocabulario.db"
CSV_FILE = "words.csv"

def importar_palabras():
    print("--- INICIANDO IMPORTACIÓN ---")

    # 1. Conectar a la base de datos (se crea sola si no existe)
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print(f"✅ Base de datos '{DB_NAME}' conectada.")
    except Exception as e:
        print(f"❌ Error al conectar base de datos: {e}")
        return

    # 2. Crear la tabla 'words' (SOLO columnas básicas)
    # Si la tabla ya existe, no hace nada.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT,
            usage_example TEXT
        )
    """)
    conn.commit()
    print("✅ Tabla 'words' verificada.")

    # 3. Leer el archivo CSV e insertar datos
    if not os.path.exists(CSV_FILE):
        print(f"❌ ERROR: No encuentro el archivo '{CSV_FILE}' en esta carpeta.")
        print("   Asegúrate de crearlo antes de ejecutar este script.")
    else:
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                count = 0
                
                print("📂 Leyendo CSV...")
                for row in reader:
                    # Verificamos que la fila tenga al menos 4 columnas para evitar errores
                    if len(row) >= 4:
                        w_id = row[0]
                        word = row[1]
                        defi = row[2]
                        examp = row[3]

                        # INSERT OR REPLACE: Si el ID ya existe, actualiza los datos.
                        cursor.execute("""
                            INSERT OR REPLACE INTO words (id, word, definition, usage_example)
                            VALUES (?, ?, ?, ?)
                        """, (w_id, word, defi, examp))
                        count += 1
                
                conn.commit()
                print(f"✅ ÉXITO: Se importaron/actualizaron {count} palabras.")

        except Exception as e:
            print(f"❌ Ocurrió un error leyendo el CSV: {e}")

    # 4. Cerrar conexión
    conn.close()
    input("\nPresiona ENTER para salir...")

if __name__ == "__main__":
    importar_palabras()