import sqlite3
import csv
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
DB_NAME = "vocabulario.db"
CSV_FILE = "words.csv"

def importar_palabras():
    print("--- INICIANDO IMPORTACIÓN (Lógica Correcta) ---")

    # 1. Conectar
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print(f"✅ Base de datos '{DB_NAME}' conectada.")
    except Exception as e:
        print(f"❌ Error al conectar base de datos: {e}")
        return

    # 2. Crear tabla (Sin default en modificated)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT,
            usage_example TEXT,
            status INTEGER DEFAULT 0,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modificated DATETIME -- Será NULL por defecto
        )
    """)
    conn.commit()
    print("✅ Tabla 'words' verificada.")

    # 3. Procesar CSV
    if not os.path.exists(CSV_FILE):
        print(f"❌ ERROR: Falta el archivo '{CSV_FILE}'.")
    else:
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                count = 0
                
                print("📂 Procesando filas...")
                for row in reader:
                    if len(row) >= 4:
                        w_id = row[0]
                        word = row[1]
                        defi = row[2]
                        examp = row[3]
                        
                        # Fecha actual solo para cuando sea UPDATE
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # LÓGICA DE UPSERT:
                        # VALUES (?, ?, ?, ?, 0, NULL): 
                        #    - Al crear, status es 0 y modificated es NULL (correcto).
                        # ON CONFLICT(id) DO UPDATE SET ... modificated = ?:
                        #    - Al actualizar, cambiamos el texto y ponemos fecha en modificated.
                        
                        cursor.execute("""
                            INSERT INTO words (id, word, definition, usage_example, status, modificated)
                            VALUES (?, ?, ?, ?, 0, NULL)
                            ON CONFLICT(id) DO UPDATE SET
                                word = excluded.word,
                                definition = excluded.definition,
                                usage_example = excluded.usage_example,
                                modificated = ?
                        """, (w_id, word, defi, examp, now))
                        
                        count += 1
                
                conn.commit()
                print(f"✅ ÉXITO: {count} registros procesados.")
                print("   (Nuevos tienen modificated=NULL. Existentes tienen fecha actual).")

        except Exception as e:
            print(f"❌ Error leyendo CSV: {e}")

    conn.close()
    input("\nPresiona ENTER para salir...")

if __name__ == "__main__":
    importar_palabras()