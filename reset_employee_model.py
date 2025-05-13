#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
import os

# Configuration de la connexion
DB_NAME = "Parc_IT_2"
DB_USER = "odoo2"      # À modifier selon votre configuration
DB_PASSWORD = "franckX"  # À modifier selon votre configuration
DB_HOST = "localhost"
DB_PORT = "5432"

print("=" * 80)
print(f"RÉINITIALISATION DU MODÈLE IT.EMPLOYEE")
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
    
    # 1. Forcer la mise à jour du module it__park
    print("[ACTION] Marquage du module it__park pour mise à jour...")
    cursor.execute("UPDATE ir_module_module SET state='to upgrade' WHERE name='it__park'")
    print("[OK] Module marqué pour mise à jour")
    
    # 2. Nettoyer les références au modèle it.employee dans ir_model_data
    print("[ACTION] Nettoyage des références au modèle it.employee...")
    cursor.execute("""
        DELETE FROM ir_model_data 
        WHERE model='ir.model.fields' 
        AND res_id IN (SELECT id FROM ir_model_fields WHERE model='it.employee' AND name='color')
    """)
    print("[OK] Références nettoyées")
    
    # 3. Vérifier si le champ color existe dans la table it_employee
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='it_employee' AND column_name='color'")
    if not cursor.fetchone():
        print("[ACTION] Le champ 'color' n'existe pas dans la table. Ajout...")
        cursor.execute("ALTER TABLE it_employee ADD COLUMN color INTEGER DEFAULT 0")
        print("[OK] Colonne 'color' ajoutée à la table")
    else:
        print("[INFO] La colonne 'color' existe déjà dans la table")
    
    # 4. Vérifier et créer l'entrée dans ir_model_fields
    cursor.execute("""
        SELECT id FROM ir_model_fields 
        WHERE model='it.employee' AND name='color'
    """)
    if not cursor.fetchone():
        print("[ACTION] Le champ 'color' n'est pas enregistré dans ir_model_fields. Ajout...")
        cursor.execute("""
            INSERT INTO ir_model_fields (name, field_description, model_id, ttype, state)
            SELECT 'color', 'Color Index', id, 'integer', 'base'
            FROM ir_model WHERE model='it.employee'
        """)
        print("[OK] Champ 'color' enregistré dans ir_model_fields")
    else:
        print("[INFO] Le champ 'color' est déjà enregistré dans ir_model_fields")
    
    # 5. Vider le cache Odoo
    print("[ACTION] Nettoyage des caches...")
    tables_to_clear = [
        'ir_attachment',
        'ir_ui_view_custom',
        'ir_translation',
        'ir_config_parameter'
    ]
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE create_date < NOW() - INTERVAL '1 hour' AND name LIKE '%cache%'")
        except:
            pass
    print("[OK] Cache nettoyé")
    
    print("\n[SUCCESS] Opérations de réinitialisation terminées avec succès!")
    print("[INFO] Redémarrez complètement le serveur Odoo pour appliquer les changements.")
    
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
print("FIN DU SCRIPT DE RÉINITIALISATION")
print("=" * 80) 