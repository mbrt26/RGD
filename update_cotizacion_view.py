def update_cotizacion_view():
    # Ruta al archivo views.py del módulo CRM
    views_path = "/Users/miguelrodriguez/GitHub/RGD AIRE/crm/views.py"
    
    # Leer el contenido actual del archivo
    with open(views_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Reemplazar el método get_context_data en CotizacionListView
    new_context_method = """    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        # Asegurar que add_url esté disponible tanto directamente como dentro de view
        context['view'] = {'add_url': self.add_url}
        context['add_url'] = self.add_url
        return context"""
    
    # Usar una expresión regular para encontrar y reemplazar el método
    import re
    updated_content = re.sub(
        r'def get_context_data\(self, \*\*kwargs\):\s+context = super\(\)\.get_context_data\(\*\*kwargs\)\s+context\[\'title\'\] = self\.title\s+context\[\'add_url\'\] = self\.add_url\s+return context',
        new_context_method,
        content,
        flags=re.DOTALL
    )
    
    # Escribir el contenido actualizado de vuelta al archivo
    with open(views_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("Vista CotizacionListView actualizada correctamente.")

if __name__ == "__main__":
    update_cotizacion_view()
