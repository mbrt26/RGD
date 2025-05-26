def update_crm_views():
    # Ruta al archivo views.py del módulo CRM
    views_path = "/Users/miguelrodriguez/GitHub/RGD AIRE/crm/views.py"
    
    # Leer el contenido actual del archivo
    with open(views_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Reemplazar las rutas de las plantillas de representantes
    updated_content = content.replace(
        "template_name = 'crm/representante_form.html'",
        "template_name = 'crm/representante/form.html'"
    )
    
    # Escribir el contenido actualizado de vuelta al archivo
    with open(views_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("Rutas de plantillas de representantes actualizadas correctamente.")

if __name__ == "__main__":
    update_crm_views()
