# -*- coding: utf-8 -*-

def post_init_hook(cr, registry):
    """
    Hook qui s'exécute après l'installation/mise à jour du module
    pour corriger les menus dupliqués
    """
    # Script SQL pour désactiver les menus dupliqués
    sql = """
    -- Désactiver les menus problématiques connus par leur ID
    UPDATE ir_ui_menu SET active = FALSE WHERE id IN (482, 483, 484, 487, 488);
    
    -- Supprimer également les relations groupe-menu
    DELETE FROM ir_ui_menu_group_rel WHERE menu_id IN (482, 483, 484, 487, 488);
    
    -- Vider les caches (important)
    DELETE FROM ir_ui_menu WHERE id NOT IN (SELECT id FROM ir_ui_menu);
    """
    
    # Exécuter le script SQL
    cr.execute(sql)
    
    # Log pour confirmer l'exécution
    print("\n==== CORRECTION DES MENUS DUPLIQUÉS EFFECTUÉE AVEC SUCCÈS ====\n") 