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
print(f"DÉMARRAGE DU SCRIPT DE CORRECTION D'ALIAS POUR LE CHAMP COLOR")
print(f"Base de données: {DATABASE}")
print(f"Chemin Odoo: {odoo_path}")
print("=" * 80)

# Initialiser Odoo avec la configuration
odoo.tools.config.parse_config(['--config', ODOO_CONFIG])
odoo.tools.config['database'] = DATABASE

def fix_employee_field_alias(env):
    """Script pour corriger le problème de champ color dans it.employee en ajoutant un alias"""
    print("\n[DEBUG] Vérification du modèle it.employee...")
    
    # Vérifier si le modèle existe
    if 'it.employee' in env:
        print("[OK] Le modèle it.employee existe dans le registre.")
        
        # Obtenir des informations sur le modèle
        model_obj = env['it.employee']
        print(f"[DEBUG] Champs disponibles: {list(model_obj._fields.keys())}")
        
        # Vérifier si le champ color est maintenant disponible
        has_color = 'color' in model_obj._fields
        print(f"[DEBUG] Le champ 'color' est présent: {has_color}")
        
        # Définir le modèle comme à jour si nécessaire
        model = env['ir.model'].search([('model', '=', 'it.employee')])
        if model:
            print("\n[DEBUG] Mise à jour du registre pour le modèle...")
            env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model='ir.model' AND res_id=%s", (model.id,))
            print("[OK] Configuration mise à jour pour permettre la modification du modèle.")
        
        # Si le champ n'existe pas encore, on doit vider le cache du registre
        if not has_color:
            print("\n[ACTION] Nettoyage du cache du registre...")
            try:
                # Invalider le cache du modèle
                env.registry.clear_caches()
                # Recharger le modèle
                env.registry._init_modules = set(env.registry._init_modules)
                env.registry._init_modules.add('it__park')
                env.registry._init = True
                print("[OK] Cache du registre nettoyé.")
            except Exception as e:
                print(f"[ERREUR] Échec du nettoyage du cache: {e}")
        
        # Vérifier les vues utilisant ce modèle
        views = env['ir.ui.view'].search([('model', '=', 'it.employee')])
        print(f"\n[DEBUG] Nombre de vues utilisant le modèle: {len(views)}")
        
        # Valider les vues
        for view in views:
            try:
                view._check_xml()
                print(f"[OK] Vue {view.name} validée")
            except Exception as e:
                print(f"[ERREUR] Vue {view.name} invalide: {e}")
        
        # Activer les champs manuels dans les vues
        print("\n[ACTION] Activation des champs manuels dans les vues...")
        try:
            env.cr.execute("""
                UPDATE ir_ui_view SET mode='primary' 
                WHERE model = 'it.employee' AND type='form'
            """)
            print("[OK] Vues mises à jour.")
        except Exception as e:
            print(f"[ERREUR] Échec de la mise à jour des vues: {e}")
        
        # Commit des changements
        env.cr.commit()
        print("\n[OK] Changements enregistrés dans la base de données.")
    else:
        print("\n[ERREUR] Le modèle it.employee n'existe pas dans le registre!")
        
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
            result = fix_employee_field_alias(env)
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

# Exécution du script si lancé directement
if __name__ == '__main__':
    # Ce script est prévu pour être exécuté directement via:
    # python fix_employee_field_alias.py
    pass 