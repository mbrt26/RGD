import re

# Leer el archivo original
with open('/Users/miguelrodriguez/GitHub/RGD AIRE/proyectos/views/actividad/views.py', 'r') as file:
    content = file.read()

# Definir el nuevo contenido de los campos
new_fields = """    fields = [
        'proyecto', 'actividad', 'inicio', 'fin',
        'duracion', 'estado', 'avance', 'predecesoras',
        'observaciones', 'adjuntos'
    ]"""

# Reemplazar en ActividadCreateView
content = re.sub(
    r"fields = \[\s*'proyecto', 'actividad', 'descripcion', 'inicio', 'fin',\s*'duracion', 'estado', 'avance', 'responsable', 'predecesoras',\s*'observaciones', 'adjuntos'\s*\]",
    new_fields,
    content
)

# Reemplazar en ActividadUpdateView
content = re.sub(
    r"fields = \[\s*'proyecto', 'actividad', 'descripcion', 'inicio', 'fin',\s*'duracion', 'estado', 'avance', 'responsable', 'predecesoras',\s*'observaciones', 'adjuntos'\s*\]",
    new_fields,
    content
)

# Escribir el archivo actualizado
with open('/Users/miguelrodriguez/GitHub/RGD AIRE/proyectos/views/actividad/views.py', 'w') as file:
    file.write(content)

print("Archivo actualizado exitosamente.")
