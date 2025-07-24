#!/usr/bin/env python3
"""
Script para verificar el trato #6981 en producción
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_cloudrun')
django.setup()

from crm.models import Trato
from servicios.models import SolicitudServicio
from crm.signals import crear_solicitud_servicio_desde_trato

def main():
    print("=== VERIFICANDO TRATO #6981 EN PRODUCCIÓN ===")
    
    try:
        # Buscar por número de oferta
        trato = Trato.objects.get(numero_oferta='6981')
        print(f"✅ Trato encontrado:")
        print(f"  ID: {trato.id}")
        print(f"  Número oferta: {trato.numero_oferta}")
        print(f"  Cliente: {trato.cliente.nombre if trato.cliente else 'Sin cliente'}")
        print(f"  Estado: {trato.estado}")
        print(f"  Tipo negociación: {trato.tipo_negociacion}")
        print(f"  Centro costos: '{trato.centro_costos}'")
        print(f"  Responsable: {trato.responsable}")
        print(f"  Fecha creación: {trato.fecha_creacion}")
        
        # Verificar si tiene solicitudes de servicio
        print(f"\n=== SOLICITUDES DE SERVICIO ===")
        solicitudes_trato = SolicitudServicio.objects.filter(trato_origen=trato)
        solicitudes_orden = SolicitudServicio.objects.filter(numero_orden__icontains='6981')
        
        print(f"Solicitudes por trato_origen: {solicitudes_trato.count()}")
        for sol in solicitudes_trato:
            print(f"  - {sol.numero_orden} (Estado: {sol.estado}, Creado: {sol.fecha_programada})")
        
        print(f"Solicitudes por número orden: {solicitudes_orden.count()}")
        for sol in solicitudes_orden:
            print(f"  - {sol.numero_orden} (Estado: {sol.estado}, Creado: {sol.fecha_programada})")
            
        # Verificar si cumple condiciones para crear solicitud
        print(f"\n=== VALIDACIONES ===")
        
        puede_crear = True
        problemas = []
        
        if trato.estado != 'ganado':
            puede_crear = False
            problemas.append(f"Estado es '{trato.estado}' (debe ser 'ganado')")
        else:
            print("✅ Estado es 'ganado'")
            
        if trato.tipo_negociacion not in ['control', 'servicios']:
            puede_crear = False
            problemas.append(f"Tipo negociación '{trato.tipo_negociacion}' no genera servicios")
        else:
            print(f"✅ Tipo negociación '{trato.tipo_negociacion}' es válido")
            
        if not trato.centro_costos:
            puede_crear = False
            problemas.append("Sin centro de costos")
        else:
            print("✅ Tiene centro de costos")
            
        if not trato.cliente:
            puede_crear = False
            problemas.append("Sin cliente asignado")
        else:
            print("✅ Tiene cliente asignado")
        
        # Verificar si ya tiene solicitudes
        if solicitudes_trato.exists() or solicitudes_orden.exists():
            puede_crear = False
            problemas.append("Ya tiene solicitudes de servicio creadas")
        else:
            print("✅ No tiene solicitudes duplicadas")
        
        if problemas:
            print(f"\n❌ PROBLEMAS ENCONTRADOS:")
            for problema in problemas:
                print(f"  - {problema}")
        
        # Si puede crear la solicitud, hacerlo
        if puede_crear:
            print(f"\n=== CREANDO SOLICITUD DE SERVICIO ===")
            try:
                success, message, solicitud = crear_solicitud_servicio_desde_trato(trato)
                if success:
                    print("✅ SOLICITUD CREADA EXITOSAMENTE:")
                    print(message)
                else:
                    print("❌ ERROR AL CREAR SOLICITUD:")
                    print(message)
            except Exception as e:
                print(f"❌ EXCEPCIÓN AL CREAR SOLICITUD: {e}")
        else:
            print(f"\n⚠️ NO SE PUEDE CREAR SOLICITUD AUTOMÁTICAMENTE")
            
    except Trato.DoesNotExist:
        print("❌ Trato #6981 no encontrado")
        
        # Buscar tratos similares
        print("\nBuscando tratos con números similares...")
        tratos_similares = Trato.objects.filter(numero_oferta__icontains='6981')[:5]
        for trato in tratos_similares:
            print(f"  - {trato.numero_oferta} (ID: {trato.id}, Estado: {trato.estado})")
            
        # Mostrar algunos tratos recientes
        print("\nTratos más recientes:")
        tratos_recientes = Trato.objects.all().order_by('-id')[:5]
        for trato in tratos_recientes:
            print(f"  - #{trato.numero_oferta} (ID: {trato.id}, Estado: {trato.estado})")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()