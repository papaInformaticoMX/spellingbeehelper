import sqlite3
import csv
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
DB_NAME = "vocabulario.db"
CSV_FILE = "words.csv"

def importar_palabras():
    print("--- INICIANDO IMPORTACIÓN (Columna word_id) ---")

    # 1. Conectar/Crear base de datos
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print(f"✅ Base de datos '{DB_NAME}' conectada.")
    except Exception as e:
        print(f"❌ Error al conectar base de datos: {e}")
        return

    # 2. Crear tabla 'words' (Ahora con word_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word_id INTEGER PRIMARY KEY,  -- Nombre cambiado
            word TEXT NOT NULL,
            definition TEXT,
            usage_example TEXT,
            status INTEGER DEFAULT 0,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modificated DATETIME -- NULL por defecto
        )
    """)
    conn.commit()
    print("✅ Tabla 'words' verificada (con columna word_id).")

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
                    # Validar que la fila tenga datos suficientes
                    if len(row) >= 4:
                        w_id = row[0]
                        word = row[1]
                        defi = row[2]
                        examp = row[3]
                        
                        # Fecha actual solo para cuando sea UPDATE
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # LÓGICA DE UPSERT:
                        # Si es NUEVO: word_id=?, status=0, modificated=NULL
                        # Si EXISTE (conflicto en word_id): actualizamos texto y modificated=FECHA
                        cursor.execute("""
                            INSERT INTO words (word_id, word, definition, usage_example, status, modificated)
                            VALUES (?, ?, ?, ?, 0, NULL)
                            ON CONFLICT(word_id) DO UPDATE SET
                                word = excluded.word,
                                definition = excluded.definition,
                                usage_example = excluded.usage_example,
                                modificated = ?
                        """, (w_id, word, defi, examp, now))
                        
                        count += 1
                
                conn.commit()
                print(f"✅ ÉXITO: {count} registros procesados.")

        except Exception as e:
            print(f"❌ Error leyendo CSV: {e}")

    conn.close()

if __name__ == "__main__":
    importar_palabras()