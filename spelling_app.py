import sqlite3
import csv
import time
import os
import sys
from datetime import datetime, timedelta
from gtts import gTTS
import pygame  # Usamos pygame para reproducir audio sin depender del SO

# --- CONFIGURACIÓN ---
DB_NAME = "spelling_bee.db"
CSV_FILE = "words.csv"

# Inicializar mixer de audio
pygame.mixer.init()

class SpellingApp:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        """Crea las tablas si no existen."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                word TEXT NOT NULL,
                definition TEXT,
                usage_example TEXT,
                next_review DATETIME,
                review_interval INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS repasos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER,
                review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                spelled_correctly INTEGER,
                knew_definition INTEGER,
                knew_example INTEGER,
                time_taken_seconds REAL,
                FOREIGN KEY(word_id) REFERENCES words(id)
            );
        """)
        self.conn.commit()

    def import_csv(self):
        """Importa palabras desde el CSV si la tabla está vacía o para actualizar."""
        if not os.path.exists(CSV_FILE):
            print(f"❌ No se encontró {CSV_FILE}. Crea el archivo primero.")
            return

        print("📂 Importando palabras desde CSV...")
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if len(row) < 4: continue
                    w_id, word, defi, examp = row[0], row[1], row[2], row[3]
                    
                    # Insertar o Ignorar si ya existe (para no duplicar)
                    # Si es nueva, next_review es HOY
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO words (id, word, definition, usage_example, next_review)
                        VALUES (?, ?, ?, ?, COALESCE((SELECT next_review FROM words WHERE id=?), ?))
                    """, (w_id, word, defi, examp, w_id, now))
                    count += 1
                self.conn.commit()
                print(f"✅ Se procesaron {count} palabras.")
        except Exception as e:
            print(f"⚠️ Error importando CSV: {e}")

    def speak(self, text):
        """Genera y reproduce audio usando gTTS."""
        try:
            tts = gTTS(text=text, lang='en')
            filename = "temp_audio.mp3"
            tts.save(filename)
            
            # Reproducir
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Limpieza (pygame mantiene el archivo ocupado un momento, por eso el try)
            pygame.mixer.music.unload()
            os.remove(filename)
        except Exception as e:
            print(f"Error de audio: {e}")

    def get_due_words(self):
        """Obtiene palabras cuya fecha de repaso es hoy o antes."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            SELECT id, word, definition, usage_example, review_interval 
            FROM words 
            WHERE next_review <= ? 
            ORDER BY next_review ASC
        """, (now,))
        return self.cursor.fetchall()

    def update_progress(self, word_id, current_interval, all_correct):
        """Algoritmo de Repetición Espaciada simple (tipo Leitner/SuperMemo)."""
        if all_correct:
            # Si acertó todo: Aumentar intervalo (1 -> 2 -> 4 -> 8 días...)
            new_interval = 1 if current_interval == 0 else current_interval * 2
            streak_change = 1
        else:
            # Si falló algo: Reiniciar intervalo a 0 (repasar mañana/hoy)
            new_interval = 0
            streak_change = -1 # O reiniciar a 0 si prefieres ser estricto

        # Calcular nueva fecha
        next_date = datetime.now() + timedelta(days=new_interval)
        if new_interval == 0: 
            # Si falló, aseguramos que salga en la próxima sesión (mínimo 10 min después o mañana)
             next_date = datetime.now() + timedelta(minutes=10)

        self.cursor.execute("""
            UPDATE words 
            SET review_interval = ?, next_review = ?, streak = streak + ?
            WHERE id = ?
        """, (new_interval, next_date.strftime("%Y-%m-%d %H:%M:%S"), streak_change, word_id))
        self.conn.commit()

    def log_review(self, w_id, spelled_ok, def_ok, ex_ok, time_taken):
        """Guarda el intento en la tabla histórica."""
        self.cursor.execute("""
            INSERT INTO repasos (word_id, spelled_correctly, knew_definition, knew_example, time_taken_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (w_id, 1 if spelled_ok else 0, 1 if def_ok else 0, 1 if ex_ok else 0, time_taken))
        self.conn.commit()

    def start_session(self):
        due_words = self.get_due_words()
        if not due_words:
            print("\n🎉 ¡Felicidades! No tienes palabras pendientes por hoy.")
            return

        print(f"\n📚 Tienes {len(due_words)} palabras para repasar hoy.")
        input("Presiona ENTER para comenzar...")

        for word_data in due_words:
            w_id, word, definition, example, interval = word_data
            
            print("\n" + "="*40)
            print(f"👂 Escucha la palabra...")
            self.speak(word)
            
            # --- FASE 1: DELETREO ---
            start_time = time.time()
            user_spelling = input("⌨️  Escribe la palabra que escuchaste: ").strip()
            end_time = time.time()
            
            time_taken = round(end_time - start_time, 2)
            spelled_correctly = (user_spelling.lower() == word.lower())

            if spelled_correctly:
                print(f"✅ ¡Correcto! ({time_taken} seg)")
            else:
                print(f"❌ Incorrecto. Era: {word}")
                self.speak(f"The word is {word}") # Refuerzo auditivo

            # --- FASE 2: DEFINICIÓN Y EJEMPLO (Autoevaluación) ---
            print("-" * 20)
            print(f"Palabra: {word}")
            input("🤔 Piensa en la DEFINICIÓN. Presiona Enter para verla...")
            print(f"📖 Definición: {definition}")
            knew_def = input("¿La sabías? (s/n): ").lower() == 's'

            input("\n🤔 Piensa en un EJEMPLO. Presiona Enter para ver uno...")
            print(f"🗣️ Ejemplo: {example}")
            knew_ex = input("¿Lo sabías? (s/n): ").lower() == 's'

            # --- GUARDAR PROGRESO ---
            # Consideramos "acierto total" si deletreó bien Y sabía la definición
            all_correct = spelled_correctly and knew_def
            
            self.update_progress(w_id, interval, all_correct)
            self.log_review(w_id, spelled_correctly, knew_def, knew_ex, time_taken)

        print("\n🏁 Sesión terminada.")

if __name__ == "__main__":
    app = SpellingApp()
    
    # Menú simple
    while True:
        print("\n--- MENU ---")
        print("1. Cargar/Actualizar palabras desde CSV")
        print("2. Empezar a estudiar")
        print("3. Salir")
        op = input("Elige: ")
        
        if op == '1':
            app.import_csv()
        elif op == '2':
            app.start_session()
        elif op == '3':
            break