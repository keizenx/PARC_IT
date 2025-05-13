#!/usr/bin/env python3
import os
import re
from lxml import etree

def fix_xml_template():
    """
    Corrige la structure du fichier mail_template_data.xml pour Odoo 18
    en ajoutant l'attribut noupdate à chaque record
    """
    file_path = 'data/mail_template_data.xml'
    
    # Lire le contenu du fichier
    print(f"Lecture du fichier {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Analyser le XML
    parser = etree.XMLParser(remove_blank_text=True)
    xml = etree.fromstring(content.encode('utf-8'), parser)
    
    # Vérifier si l'élément racine a l'attribut noupdate
    root = xml
    has_noupdate = root.get('noupdate', None)
    
    # Créer un nouvel élément racine sans attribut noupdate
    new_root = etree.Element('odoo')
    
    # Transférer tous les commentaires et éléments de l'ancien arbre
    for elem in root:
        if isinstance(elem, etree._Comment):
            new_root.append(elem)
        elif elem.tag == 'data':
            # Si nous avons un élément data, transférer ses enfants directement
            for child in elem:
                if child.tag == 'record' and has_noupdate:
                    child.set('noupdate', has_noupdate)
                new_root.append(child)
        elif elem.tag == 'record':
            # Si nous avons un record directement sous l'élément racine,
            # ajouter l'attribut noupdate s'il existe dans la racine
            if has_noupdate:
                elem.set('noupdate', has_noupdate)
            new_root.append(elem)
        else:
            new_root.append(elem)
    
    # Sauvegarder le nouveau XML
    fixed_file_path = file_path.replace('.xml', '_fixed.xml')
    print(f"Sauvegarde du fichier corrigé dans {fixed_file_path}...")
    with open(fixed_file_path, 'wb') as f:
        f.write(etree.tostring(new_root, pretty_print=True, encoding='UTF-8', xml_declaration=True))
    
    # Remplacer le fichier original
    import shutil
    print(f"Remplacement du fichier original...")
    shutil.move(fixed_file_path, file_path)
    
    print("Correction terminée!")

if __name__ == '__main__':
    fix_xml_template() 