# Script amélioré à copier-coller directement dans le shell Odoo
# Ce script peut être exécuté tel quel, sans importation

def fix_duplicate_menus_radical():
    """
    Script radical pour corriger les menus dupliqués avec commit explicite.
    """
    print("====== DÉBUT DE LA CORRECTION RADICALE DES MENUS DUPLIQUÉS ======")
    
    # Liste des noms de menus problématiques
    menu_names = ['Logiciels', 'Licences', 'Contrats', 'Incidents', 'Interventions', 'Tickets IT', 'Tickets Helpdesk']
    
    # On récupère d'abord tous les menus actifs pour analyse
    all_active_menus = env['ir.ui.menu'].search([('active', '=', True)])
    print(f"Nombre total de menus actifs: {len(all_active_menus)}")
    
    # ID des modules concernés pour la recherche
    module_names = ['it__park']
    module_ids = env['ir.module.module'].search([('name', 'in', module_names)]).ids
    
    # 1. Identifier TOUS les menus dupliqués explicitement 
    env.cr.execute("""
        SELECT name, COUNT(*) as count, array_agg(id) as ids
        FROM ir_ui_menu
        WHERE active = TRUE
        GROUP BY name
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)
    all_duplicates = env.cr.dictfetchall()
    
    print(f"\nNombre total de menus dupliqués: {len(all_duplicates)}")
    for dup in all_duplicates:
        print(f"- '{dup['name']}': {dup['count']} occurrences, IDs: {dup['ids']}")
    
    # 2. Pour chaque menu dupliqué, obtenir les détails complets et décider lequel garder
    for menu_name in menu_names:
        print(f"\n### Traitement du menu '{menu_name}' ###")
        
        # Trouver tous les menus avec ce nom, actifs et inactifs
        all_menus = env['ir.ui.menu'].search([('name', '=', menu_name)])
        active_menus = all_menus.filtered(lambda m: m.active)
        
        if len(active_menus) <= 1:
            print(f"  Aucune duplication active pour '{menu_name}'")
            continue
            
        print(f"  {len(active_menus)} menus actifs trouvés:")
        
        # Afficher tous les détails pour analyse manuelle
        for i, menu in enumerate(active_menus):
            print(f"  {i+1}. ID={menu.id}, XML_ID={get_xml_id(menu)}, Parent={menu.parent_id.name}, Module={get_module(menu)}")
        
        # Désactiver tous les menus sauf celui du module it__park
        # (ou le premier si plusieurs du même module)
        keep_menu = None
        for menu in active_menus:
            xml_id = get_xml_id(menu)
            if xml_id and 'it__park' in xml_id:
                keep_menu = menu
                break
        
        # Si aucun menu it__park trouvé, garder le premier
        if not keep_menu and active_menus:
            keep_menu = active_menus[0]
            
        if keep_menu:
            print(f"\n  ✓ Menu conservé: ID={keep_menu.id}, XML_ID={get_xml_id(keep_menu)}")
            
            # Désactiver tous les autres menus
            for menu in active_menus:
                if menu.id != keep_menu.id:
                    print(f"  ✓ Menu désactivé: ID={menu.id}, XML_ID={get_xml_id(menu)}")
                    
                    # Désactiver directement avec SQL
                    env.cr.execute(f"UPDATE ir_ui_menu SET active = FALSE WHERE id = {menu.id}")
                    env.cr.execute(f"DELETE FROM ir_ui_menu_group_rel WHERE menu_id = {menu.id}")
    
    # 3. COMMIT explicite pour s'assurer que les changements sont enregistrés
    env.cr.commit()
    
    # 4. Vider le cache des menus APRÈS le commit
    env['ir.ui.menu'].clear_caches()
    
    print("\n====== FIN DE LA CORRECTION RADICALE DES MENUS DUPLIQUÉS ======")
    print("\nRedémarrez votre serveur Odoo pour que les changements prennent effet.")
    
    return True

def get_xml_id(record):
    """Récupère l'XML ID d'un enregistrement"""
    if not record:
        return None
    xml_id = record.get_external_id().get(record.id)
    return xml_id or 'Pas d\'XML ID'

def get_module(record):
    """Tente de déterminer le module d'origine d'un enregistrement"""
    xml_id = get_xml_id(record)
    if xml_id and '.' in xml_id:
        return xml_id.split('.')[0]
    return 'Inconnu'

# Exécuter la fonction
fix_duplicate_menus_radical() 