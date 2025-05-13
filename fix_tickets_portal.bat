@echo off
echo Execution du script de correction des tickets dans le portail...
cd C:\Users\franc\Desktop\odoo-18.0(community)
python odoo-bin -c odoo.conf -d Parc_IT_2 -u it__park --no-http --stop-after-init
echo Script termine. Veuillez redemarrer le serveur Odoo.
pause 