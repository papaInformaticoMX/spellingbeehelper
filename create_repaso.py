import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
DB_NAME = "vocabulario.db"

def inicializar_y_crear_repaso():
    print("--- GESTOR DE REPASOS ---")

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        print(f"✅ Conectado a '{DB_NAME}'.")
    except Exception as e:
        print(f"❌ Error crítico de conexión: {e}")
        return

    # ---------------------------------------------------------
    # PASO 1: VERIFICAR Y CREAR TABLAS (SI NO EXISTEN)
    # ---------------------------------------------------------
    try:
        # Tabla Maestra: REPASOS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repasos (
                repaso_id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla Detalle: REPASO_WORDS (Con todos los campos solicitados)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repaso_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repaso_id INTEGER,
                word_id INTEGER,
                
                -- Snapshot de la palabra
                word TEXT,
                definition TEXT,
                usage_example TEXT,
                
                -- Estado y Métricas
                status INTEGER DEFAULT 0, -- 0: Pendiente, 1: Bien, 2: Mal
                
                -- Fechas
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- fechaCreacion
                updated_at DATETIME, -- fechaModificacion (NULL al inicio)
                shown_at DATETIME,   -- fechaMostrada (NULL hasta que aparezca)
                
                -- Métricas de rendimiento
                response_time REAL DEFAULT 0, -- tiempoContestada
                attempts INTEGER DEFAULT 0,   -- intentos
                
                -- Ayudas (Booleanos: 0=No, 1=Sí)
                used_definition INTEGER DEFAULT 0, 
                used_example INTEGER DEFAULT 0,
                
                FOREIGN KEY(repaso_id) REFERENCES repasos(repaso_id)
            )
        """)
        conn.commit()
        # print("✅ Estructura de tablas verificada.") 

    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        conn.close()
        return

    # ---------------------------------------------------------
    # PASO 2: LOGICA DE CREACIÓN DEL REPASO
    # ---------------------------------------------------------
    try:
        # A. Crear registro en 'repasos' para obtener ID
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO repasos (fecha) VALUES (?)", (fecha_hoy,))
        repaso_id = cursor.lastrowid
        
        # B. Actualizar nombre: "Repaso {ID}"
        nombre_repaso = f"Repaso {repaso_id}"
        cursor.execute("UPDATE repasos SET nombre = ? WHERE repaso_id = ?", (nombre_repaso, repaso_id))
        
        print(f"📝 Creando sesión: '{nombre_repaso}' (ID: {repaso_id})...")

        # C. Buscar palabras en 'words' con status = 0 (Pendientes)
        #    ORDER BY RANDOM() asegura que se inserten desordenadas
        cursor.execute("""
            SELECT word_id, word, definition, usage_example 
            FROM words 
            WHERE status = 0 
            ORDER BY RANDOM()
        """)
        palabras = cursor.fetchall()

        if not palabras:
            print("⚠️  AVISO: No hay palabras con 'status = 0' en la tabla 'words'.")
            print("   El repaso se creó pero está vacío.")
        else:
            print(f"   -> Encontradas {len(palabras)} palabras pendientes.")
            
            # D. Insertar en 'repaso_words'
            # Preparamos la query de inserción masiva
            query_insert = """
                INSERT INTO repaso_words (
                    repaso_id, word_id, word, definition, usage_example, 
                    created_at, status, attempts, used_definition, used_example, response_time
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0)
            """
            
            # Creamos una lista de tuplas para ejecutar many
            datos_para_insertar = []
            for p in palabras:
                # p[0]=id, p[1]=word, p[2]=def, p[3]=ex
                datos_para_insertar.append((
                    repaso_id, p[0], p[1], p[2], p[3], fecha_hoy
                ))

            cursor.executemany(query_insert, datos_para_insertar)
            conn.commit()
            print(f"✅ ¡ÉXITO! Se han cargado {len(palabras)} palabras en el '{nombre_repaso}'.")

    except Exception as e:
        print(f"❌ Error generando el repaso: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        input("\nPresiona ENTER para salir...")

if __name__ == "__main__":
    inicializar_y_crear_repaso()