@echo off
echo ===== MISE A JOUR DU MODULE IT__PARK ET REDEMARRAGE D'ODOO =====
pushd %~dp0\..\..
python odoo-bin -c odoo.conf -d odoo18 --update it__park
echo ===== TERMINÉ =====
echo Appuyez sur une touche pour fermer cette fenêtre...
pause > nul
popd 