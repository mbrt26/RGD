from django.contrib import admin
from colaboradores.models import Colaborador

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cargo', 'email', 'telefono')
    list_filter = ('cargo',)
    search_fields = ('nombre', 'cargo', 'email', 'telefono')
    ordering = ('nombre',)
