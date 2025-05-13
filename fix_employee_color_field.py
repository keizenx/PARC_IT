# -*- coding: utf-8 -*-

def fix_employee_color_field(env):
    """
    Script pour corriger le problème de champ 'color' dans le modèle it.employee
    À exécuter avec le shell Odoo:
    python odoo-bin shell -d Parc_IT_2 -c path/to/odoo.conf --no-http
    """
    print("=" * 80)
    print("DÉMARRAGE DU SCRIPT DE CORRECTION POUR LE CHAMP 'COLOR' DANS IT.EMPLOYEE")
    print("=" * 80)
    
    print("\n[DEBUG] Modèles disponibles: ", list(env.keys())[:10], "... (et plus)")
    
    # Vérifier si le modèle existe
    if 'it.employee' in env:
        print("\n[OK] Le modèle it.employee existe dans le registre.")
        
        # Obtenir des informations sur le modèle
        model_obj = env['it.employee']
        print(f"[DEBUG] Informations du modèle: {model_obj._name}, {model_obj._description}")
        print(f"[DEBUG] Champs disponibles: {list(model_obj._fields.keys())}")
        
        # Vérifier si le champ color est dans les champs
        has_color_field = 'color' in model_obj._fields
        print(f"[DEBUG] Le champ 'color' est présent dans les champs du modèle: {has_color_field}")
        
        # Vérifier si le modèle existe dans ir.model
        model = env['ir.model'].search([('model', '=', 'it.employee')])
        print(f"[DEBUG] Modèle trouvé dans ir.model: {model}, ID: {model.id if model else 'Non trouvé'}")
        
        if model:
            # Vérifier si le champ color existe dans ir.model.fields
            field = env['ir.model.fields'].search([
                ('model_id', '=', model.id),
                ('name', '=', 'color')
            ])
            print(f"[DEBUG] Champ 'color' trouvé dans ir.model.fields: {field}, ID: {field.id if field else 'Non trouvé'}")
            
            if field:
                print("\n[INFO] Le champ 'color' existe déjà dans la définition du modèle.")
                
                # Vérifier l'état du champ
                print(f"[DEBUG] État du champ 'color': {field.state}")
                print(f"[DEBUG] Type du champ 'color': {field.ttype}")
                print(f"[DEBUG] Description du champ 'color': {field.field_description}")
            else:
                print("\n[ACTION] Le champ 'color' n'existe pas dans ir.model.fields. Création...")
                try:
                    new_field = env['ir.model.fields'].create({
                        'name': 'color',
                        'field_description': 'Color Index',
                        'model_id': model.id,
                        'ttype': 'integer',
                        'state': 'manual',
                    })
                    print(f"[OK] Champ 'color' créé avec succès. ID: {new_field.id}")
                except Exception as e:
                    print(f"[ERREUR] Échec de la création du champ: {e}")
                
            # Vérifier la structure de la table dans la base de données
            print("\n[DEBUG] Vérification de la structure de la table it_employee...")
            env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='it_employee'")
            columns = env.cr.fetchall()
            print(f"[DEBUG] Colonnes existantes dans la table it_employee: {[col[0] for col in columns]}")
            
            env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='it_employee' AND column_name='color'")
            color_column = env.cr.fetchone()
            
            if not color_column:
                print("\n[ACTION] La colonne 'color' n'existe pas dans la table. Ajout...")
                try:
                    env.cr.execute("ALTER TABLE it_employee ADD COLUMN color INTEGER DEFAULT 0")
                    print("[OK] Colonne 'color' ajoutée avec succès à la table.")
                    
                    # Vérifier que la colonne a bien été créée
                    env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='it_employee' AND column_name='color'")
                    if env.cr.fetchone():
                        print("[DEBUG] Vérification après ajout: La colonne 'color' existe bien maintenant.")
                    else:
                        print("[ERREUR] La colonne 'color' n'a pas été créée malgré la commande réussie.")
                except Exception as e:
                    print(f"[ERREUR] Échec de l'ajout de la colonne: {e}")
            else:
                print("\n[INFO] La colonne 'color' existe déjà dans la table.")
                
            # Vérifier si des enregistrements existent
            employee_count = env['it.employee'].search_count([])
            print(f"\n[DEBUG] Nombre d'enregistrements dans it.employee: {employee_count}")
            
            if employee_count > 0:
                # Vérifier une valeur exemple
                sample = env['it.employee'].search([], limit=1)
                print(f"[DEBUG] Exemple d'enregistrement: ID={sample.id}, Nom={sample.name}")
                try:
                    color_val = sample.color
                    print(f"[DEBUG] Valeur du champ color pour cet enregistrement: {color_val}")
                except Exception as e:
                    print(f"[ERREUR] Impossible d'accéder au champ color: {e}")
                
                # Tester une mise à jour
                try:
                    print("\n[ACTION] Test de mise à jour de la valeur color...")
                    sample.write({'color': 1})
                    print(f"[DEBUG] Nouvelle valeur après mise à jour: {sample.color}")
                except Exception as e:
                    print(f"[ERREUR] Échec de la mise à jour de la valeur: {e}")
            
            # Créer une méthode virtuelle pour gérer le champ color
            print("\n[DEBUG] Tentative de mise à jour des paramètres du modèle...")
            try:
                env.cr.execute("UPDATE ir_model_data SET noupdate=false WHERE model='ir.model' AND res_id=%s", (model.id,))
                print("[OK] Configuration mise à jour pour permettre la modification du modèle.")
            except Exception as e:
                print(f"[ERREUR] Échec de la mise à jour de la configuration: {e}")
                
            # Commit des changements
            env.cr.commit()
            print("\n[OK] Changements enregistrés dans la base de données.")
            
            # Un test final pour garantir que tout fonctionne
            print("\n[DEBUG] Test final de la fonctionnalité...")
            try:
                test_read = env['it.employee'].search_read([], ['name', 'color'], limit=1)
                print(f"[DEBUG] Résultat de search_read avec color: {test_read}")
                print("[OK] Le champ color est bien accessible via l'API.")
            except Exception as e:
                print(f"[ERREUR] Le champ color n'est pas accessible via l'API: {e}")
                
    else:
        print("\n[ERREUR CRITIQUE] Le modèle it.employee n'existe pas dans le registre!")
        available_models = [m for m in list(env.keys()) if 'employee' in m or 'it.' in m]
        print(f"[DEBUG] Modèles similaires disponibles: {available_models}")
        
    print("\n" + "=" * 80)
    print("FIN DU SCRIPT DE CORRECTION")
    print("=" * 80)
    
    return True

# Pour exécuter dans le shell Odoo:
# fix_employee_color_field(env)