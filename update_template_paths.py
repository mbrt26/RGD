import os
import re

def update_template_paths():
    # Ruta al archivo views.py del módulo de proyectos
    views_path = "/Users/miguelrodriguez/GitHub/RGD AIRE/proyectos/views.py"
    
    # Diccionario con los patrones de búsqueda y reemplazo
    replacements = {
        r"template_name = 'proyectos/colaborador_form.html'": "template_name = 'proyectos/colaborador/form.html'",
        r"template_name = 'proyectos/proyecto_form.html'": "template_name = 'proyectos/proyecto/form.html'",
        r"template_name = 'proyectos/actividad_form.html'": "template_name = 'proyectos/actividad/form.html'",
        r"template_name = 'proyectos/recurso_form.html'": "template_name = 'proyectos/recurso/form.html'",
        r"template_name = 'proyectos/bitacora_form.html'": "template_name = 'proyectos/bitacora/form.html'",
        r"template_name = 'proyectos/entregable_form.html'": "template_name = 'proyectos/entregable/form.html'"
    }
    
    # Leer el contenido actual del archivo
    with open(views_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Realizar los reemplazos
    updated_content = content
    for old, new in replacements.items():
        updated_content = re.sub(old, new, updated_content)
    
    # Escribir el contenido actualizado de vuelta al archivo
    with open(views_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("Rutas de plantillas actualizadas correctamente.")

if __name__ == "__main__":
    update_template_paths()
