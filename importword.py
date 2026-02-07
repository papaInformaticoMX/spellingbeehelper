import sqlite3
import csv
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
DB_NAME = "vocabulario.db"
CSV_FILE = "words.csv"

def importar_palabras():
    print("--- INICIANDO IMPORTACIÓN CON AUDITORÍA ---")

    # 1. Conectar/Crear base de datos
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print(f"✅ Base de datos '{DB_NAME}' conectada.")
    except Exception as e:
        print(f"❌ Error al conectar base de datos: {e}")
        return

    # 2. Crear la tabla 'words' con los campos de auditoría
    # created: Se llena solo con la fecha actual al insertar.
    # modificated: Lo actualizaremos manualmente desde el script.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT,
            usage_example TEXT,
            status INTEGER DEFAULT 0,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modificated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("✅ Tabla 'words' verificada (con created/modificated).")

    # 3. Leer CSV e insertar/actualizar
    if not os.path.exists(CSV_FILE):
        print(f"❌ ERROR: No encuentro el archivo '{CSV_FILE}'.")
    else:
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                count_insert = 0
                count_update = 0
                
                print("📂 Procesando CSV...")
                for row in reader:
                    if len(row) >= 4:
                        w_id = row[0]
                        word = row[1]
                        defi = row[2]
                        examp = row[3]
                        
                        # Fecha actual para 'modificated'
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # ESTRATEGIA INTELIGENTE (UPSERT):
                        # Intentamos insertar. Si el ID choca (ya existe), hacemos UPDATE.
                        # Esto protege tu campo 'created' y 'status' original.
                        cursor.execute("""
                            INSERT INTO words (id, word, definition, usage_example, status, modificated)
                            VALUES (?, ?, ?, ?, 0, ?)
                            ON CONFLICT(id) DO UPDATE SET
                                word = excluded.word,
                                definition = excluded.definition,
                                usage_example = excluded.usage_example,
                                modificated = excluded.modificated
                        """, (w_id, word, defi, examp, now))
                        
                        # (Nota: SQLite no dice fácil si fue insert o update, así que contamos procesados)
                        count_insert += 1
                
                conn.commit()
                print(f"✅ PROCESO COMPLETADO.")
                print(f"   Filas procesadas: {count_insert}")
                print("   (Las palabras nuevas se crearon, las existentes se actualizaron sin perder su estatus).")

        except Exception as e:
            print(f"❌ Error leyendo el CSV: {e}")

    conn.close()
    input("\nPresiona ENTER para salir...")

if __name__ == "__main__":
    importar_palabras()