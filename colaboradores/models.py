from django.db import models

class Colaborador(models.Model):
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    email = models.EmailField('Correo electrónico', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.cargo}"
