#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback

# Ajouter le chemin du répertoire odoo au PYTHONPATH
odoo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(odoo_path)

# Importer les modules Odoo nécessaires
import odoo
from odoo.api import Environment

# Base de données à utiliser
DATABASE = 'Parc_IT_2'
ODOO_CONFIG = os.path.join(odoo_path, 'odoo.conf')

print("=" * 80)
print(f"DÉMARRAGE DU SCRIPT DE CORRECTION DU CHAMP COLOR DANS IT.EMPLOYEE")
print(f"Base de données: {DATABASE}")
print(f"Chemin Odoo: {odoo_path}")
print("=" * 80)

# Initialiser Odoo avec la configuration
odoo.tools.config.parse_config(['--config', ODOO_CONFIG])
odoo.tools.config['database'] = DATABASE

def fix_employee_color_field(env):
    """Script pour corriger le problème de champ color dans it.employee"""
    print("\n[DEBUG] Vérification du modèle it.employee...")
    
    # Vérifier si le modèle existe
    if 'it.employee' in env:
        print("[OK] Le modèle it.employee existe dans le registre.")
        
        # Obtenir des informations sur le modèle
        model_obj = env['it.employee']
        print(f"[DEBUG] Champs disponibles: {list(model_obj._fields.keys())}")
        
        # Vérifier si le modèle existe dans ir.model
        model = env['ir.model'].search([('model', '=', 'it.employee')])
        print(f"[DEBUG] Modèle trouvé dans ir.model: {model}, ID: {model.id if model else 'Non trouvé'}")
        
        if model:
            # Vérifier la structure de la table dans la base de données
            print("\n[DEBUG] Vérification de la structure de la table it_employee...")
            env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='it_employee'")
            columns = env.cr.fetchall()
            print(f"[DEBUG] Colonnes existantes: {[col[0] for col in columns]}")
            
            # Vérifier si le champ 'color' existe déjà dans la table
            env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='it_employee' AND column_name='color'")
            color_column = env.cr.fetchone()
            
            if not color_column:
                print("\n[ACTION] La colonne 'color' n'existe pas. Ajout...")
                try:
                    env.cr.execute("ALTER TABLE it_employee ADD COLUMN color INTEGER DEFAULT 0")
                    print("[OK] Colonne 'color' ajoutée avec succès.")
                except Exception as e:
                    print(f"[ERREUR] Échec de l'ajout de la colonne: {e}")
            else:
                print("\n[INFO] La colonne 'color' existe déjà.")
                
            # Vérifier si le champ existe dans ir.model.fields
            field = env['ir.model.fields'].search([
                ('model_id', '=', model.id),
                ('name', '=', 'color')
            ])
            
            if not field:
                print("\n[ACTION] Le champ 'color' n'existe pas dans ir.model.fields. Création...")
                try:
                    field = env['ir.model.fields'].create({
                        'name': 'color',
                        'field_description': 'Color Index',
                        'model_id': model.id,
                        'ttype': 'integer',
                        'state': 'manual',
                    })
                    print("[OK] Champ 'color' créé avec succès.")
                except Exception as e:
                    print(f"[ERREUR] Échec de la création du champ: {e}")
            else:
                print("\n[INFO] Le champ 'color' existe déjà dans ir.model.fields.")
            
            # Test final pour vérifier l'accès au champ
            try:
                print("\n[DEBUG] Test final de la fonctionnalité...")
                test_read = env['it.employee'].search_read([], ['name', 'color'], limit=1)
                print(f"[DEBUG] Résultat de search_read avec color: {test_read}")
                print("[OK] Le champ color est accessible via l'API.")
            except Exception as e:
                print(f"[ERREUR] Le champ color n'est pas accessible: {e}")
                
            # Commit des changements
            env.cr.commit()
            print("\n[OK] Changements enregistrés dans la base de données.")
    else:
        print("\n[ERREUR] Le modèle it.employee n'existe pas dans le registre!")
        available_models = [m for m in list(env.keys()) if 'employee' in m or 'it.' in m]
        print(f"[DEBUG] Modèles similaires disponibles: {available_models}")
    
    return True

# Connexion à la base de données
try:
    registry = odoo.registry(DATABASE)
    
    with registry.cursor() as cr:
        env = Environment(cr, odoo.SUPERUSER_ID, {})
        print("\n[INFO] Connexion à la base de données établie avec succès")
        
        # Exécuter la fonction de correction
        try:
            print("\n[INFO] Lancement de la fonction de correction...")
            result = fix_employee_color_field(env)
            if result:
                print("\n[SUCCESS] Script exécuté avec succès!")
            else:
                print("\n[ERREUR] Le script a retourné une erreur.")
        except Exception as e:
            print(f"\n[ERREUR CRITIQUE] Erreur lors de l'exécution: {e}")
            traceback.print_exc()
            
except Exception as e:
    print(f"\n[ERREUR] Impossible de se connecter à la base de données: {e}")
    traceback.print_exc()
    
print("\n" + "=" * 80)
print("FIN DU SCRIPT")
print("=" * 80) 