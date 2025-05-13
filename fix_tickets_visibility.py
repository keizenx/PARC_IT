# Script pour corriger la visibilité des tickets dans le portail
# Exécuter avec: odoo shell -c odoo.conf < custom_addons/it__park/fix_tickets_visibility.py

# 1. Vérifier que le template de vue du portail est actif
portal_template = env['ir.ui.view'].search([('name', '=', 'portal_my_tickets')])
if portal_template and not portal_template.active:
    portal_template.active = True
    print(f"Template 'portal_my_tickets' activé.")

# 2. Vérifier les règles d'accès aux tickets pour les utilisateurs du portail
portal_group = env.ref('base.group_portal')
ticket_model = env['ir.model'].search([('model', '=', 'it.ticket')], limit=1)

# Chercher la règle d'accès existante
access_rule = env['ir.model.access'].search([
    ('model_id', '=', ticket_model.id),
    ('group_id', '=', portal_group.id)
])

# Si la règle n'existe pas, la créer avec les droits appropriés
if not access_rule:
    env['ir.model.access'].create({
        'name': 'it.ticket portal access',
        'model_id': ticket_model.id,
        'group_id': portal_group.id,
        'perm_read': True,
        'perm_write': False,
        'perm_create': True,
        'perm_unlink': False
    })
    print("Règle d'accès créée pour les tickets dans le portail.")
else:
    # S'assurer que les droits de lecture sont activés
    if not access_rule.perm_read:
        access_rule.perm_read = True
        print("Droit de lecture activé pour les tickets dans le portail.")
    if not access_rule.perm_create:
        access_rule.perm_create = True
        print("Droit de création activé pour les tickets dans le portail.")

# 3. Vérifier les règles d'enregistrement pour les tickets
ticket_rule = env['ir.rule'].search([
    ('model_id', '=', ticket_model.id),
    ('groups', 'in', [portal_group.id]),
    ('name', 'ilike', '%portal%')
])

# Si aucune règle n'est trouvée, en créer une
if not ticket_rule:
    env['ir.rule'].create({
        'name': 'it.ticket: portal users see their own and commercial partner tickets',
        'model_id': ticket_model.id,
        'domain_force': "['|', ('client_id.commercial_partner_id', '=', user.partner_id.commercial_partner_id.id), ('partner_id.commercial_partner_id', '=', user.partner_id.commercial_partner_id.id)]",
        'groups': [(4, portal_group.id)],
        'perm_read': True,
        'perm_write': False,
        'perm_create': True,
        'perm_unlink': False
    })
    print("Règle d'enregistrement créée pour les tickets dans le portail.")

# 4. Mettre à jour le compteur de tickets dans le menu
try:
    ticket_menu = env.ref('it__park.menu_portal_tickets')
    if ticket_menu:
        ticket_menu.sequence = 10  # Remonter dans la liste des menus
        print("Menu des tickets mis à jour.")
except Exception as e:
    print(f"Erreur lors de la mise à jour du menu: {str(e)}")

# 5. Rafraîchir le cache et vider les caches de vue
env['ir.ui.view'].clear_caches()
print("Cache de vues vidé.")

print("Corrections terminées. Redémarrez le serveur Odoo pour appliquer toutes les modifications.") 