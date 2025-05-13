#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys

# Configuration de la connexion
DB_NAME = "Parc_IT_2"
DB_USER = "odoo2"      # À modifier selon votre configuration
DB_PASSWORD = "franckX"  # À modifier selon votre configuration
DB_HOST = "localhost"
DB_PORT = "5432"

print("=" * 80)
print(f"CORRECTION SQL DIRECTE - CHAMP COLOR MANQUANT")
print(f"Base de données: {DB_NAME}")
print("=" * 80)

try:
    # Connexion à PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("[INFO] Connexion à PostgreSQL établie")
    
    # 1. Vérifier si la colonne existe déjà
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='it_employee' AND column_name='color'")
    if cursor.fetchone():
        print("[INFO] La colonne 'color' existe déjà dans la table it_employee")
    else:
        print("[ACTION] Ajout de la colonne 'color' à la table it_employee...")
        cursor.execute("ALTER TABLE it_employee ADD COLUMN color INTEGER DEFAULT 0")
        print("[OK] Colonne 'color' ajoutée avec succès")
    
    # 2. Vérifier si le champ existe dans ir_model_fields
    cursor.execute("""
        SELECT id FROM ir_model_fields 
        WHERE name = 'color' 
        AND model IN (SELECT model FROM ir_model WHERE model = 'it.employee')
    """)
    if cursor.fetchone():
        print("[INFO] Le champ 'color' existe déjà dans ir_model_fields")
    else:
        print("[ACTION] Ajout du champ 'color' dans ir_model_fields...")
        cursor.execute("""
            INSERT INTO ir_model_fields (name, field_description, model_id, ttype, state)
            SELECT 'color', 'Color Index', id, 'integer', 'manual'
            FROM ir_model WHERE model = 'it.employee'
        """)
        print("[OK] Champ 'color' ajouté à ir_model_fields avec succès")
    
    # 3. Actualiser les vues qui utilisent ce modèle
    print("[ACTION] Actualisation des vues utilisant le modèle it.employee...")
    cursor.execute("""
        UPDATE ir_ui_view SET arch_db = arch_db 
        WHERE model = 'it.employee'
    """)
    print("[OK] Vues actualisées avec succès")
    
    print("\n[SUCCESS] Opérations SQL terminées avec succès!")
    
except Exception as e:
    print(f"\n[ERREUR] Une erreur s'est produite: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
        print("[INFO] Connexion à la base de données fermée")

print("\n" + "=" * 80)
print("FIN DU SCRIPT")
print("=" * 80) 