from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from proyectos.models import Bitacora, Proyecto, Actividad, Colaborador, BitacoraArchivo
from proyectos.forms.bitacora_forms import BitacoraForm, FiltroBitacorasForm

@require_http_methods(["GET"])
def get_actividades_por_proyecto(request, proyecto_id):
    """Vista AJAX que devuelve las actividades de un proyecto específico"""
    try:
        actividades = Actividad.objects.filter(
            proyecto_id=proyecto_id,
            estado__in=['no_iniciado', 'en_proceso']  # Solo actividades no finalizadas
        ).values('id', 'actividad').order_by('actividad')
        return JsonResponse(list(actividades), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

class BitacoraListView(LoginRequiredMixin, ListView):
    model = Bitacora
    template_name = 'proyectos/bitacora/list.html'
    context_object_name = 'bitacoras'
    ordering = ['-fecha_registro']
    title = 'Bitácora de Actividades'
    add_url = 'proyectos:bitacora_create'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Crear el formulario de filtros con los datos GET
        form = FiltroBitacorasForm(self.request.GET)
        
        if form.is_valid():
            # Filtro por proyecto
            if form.cleaned_data.get('proyecto'):
                queryset = queryset.filter(proyecto=form.cleaned_data['proyecto'])
            
            # Filtro por estado
            if form.cleaned_data.get('estado'):
                queryset = queryset.filter(estado=form.cleaned_data['estado'])
            
            # Filtro por estado de validación
            if form.cleaned_data.get('estado_validacion'):
                queryset = queryset.filter(estado_validacion=form.cleaned_data['estado_validacion'])
            
            # Filtro por responsable
            if form.cleaned_data.get('responsable'):
                queryset = queryset.filter(responsable=form.cleaned_data['responsable'])
            
            # Filtro por urgencia
            urgencia = form.cleaned_data.get('urgencia')
            if urgencia == 'urgente':
                queryset = queryset.filter(fecha_ejecucion_real__isnull=True, fecha_planificada__lt=timezone.now().date())
            elif urgencia == 'normal':
                queryset = queryset.filter(Q(fecha_ejecucion_real__isnull=False) | Q(fecha_planificada__gte=timezone.now().date()))
            
            # Filtro por rango de fechas
            if form.cleaned_data.get('fecha_desde'):
                queryset = queryset.filter(fecha_planificada__gte=form.cleaned_data['fecha_desde'])
            
            if form.cleaned_data.get('fecha_hasta'):
                queryset = queryset.filter(fecha_planificada__lte=form.cleaned_data['fecha_hasta'])
        
        # Filtro de búsqueda por texto
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(descripcion__icontains=search_query) |
                Q(subactividad__icontains=search_query) |
                Q(observaciones__icontains=search_query) |
                Q(proyecto__nombre_proyecto__icontains=search_query) |
                Q(actividad__actividad__icontains=search_query)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['view'] = {'add_url': self.add_url}
        
        # Agregar el formulario de filtros al contexto
        form = FiltroBitacorasForm(self.request.GET)
        context['filter_form'] = form
        context['search_query'] = self.request.GET.get('search', '')
        
        # Contador de resultados
        context['total_bitacoras'] = self.get_queryset().count()
        
        # Información del proyecto si se está filtrando
        proyecto_id = self.request.GET.get('proyecto')
        if proyecto_id:
            try:
                proyecto = Proyecto.objects.get(id=proyecto_id)
                context['proyecto_filtro'] = proyecto
                context['title'] = f'Bitácoras - {proyecto.nombre_proyecto}'
            except Proyecto.DoesNotExist:
                pass
                
        return context

class BitacoraCreateView(LoginRequiredMixin, CreateView):
    model = Bitacora
    template_name = 'proyectos/bitacora/form.html'
    form_class = BitacoraForm
    success_url = reverse_lazy('proyectos:bitacora_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nueva Entrada de Bitácora'
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Verificar si hay un proyecto_id en la URL
        proyecto_id = self.request.GET.get('proyecto_id')
        
        # Si hay un proyecto seleccionado, mostrar sus actividades
        if form.instance.proyecto_id:
            form.fields['actividad'].queryset = Actividad.objects.filter(
                proyecto_id=form.instance.proyecto_id,
                estado__in=['no_iniciado', 'en_proceso']
            )
        elif form.data.get('proyecto'):
            # Si el formulario fue enviado, mostrar las actividades del proyecto seleccionado
            form.fields['actividad'].queryset = Actividad.objects.filter(
                proyecto_id=form.data['proyecto'],
                estado__in=['no_iniciado', 'en_proceso']
            )
        elif proyecto_id:
            # Si viene proyecto_id en la URL, preseleccionar el proyecto y cargar actividades
            try:
                proyecto = Proyecto.objects.get(id=proyecto_id)
                form.fields['proyecto'].initial = proyecto
                form.fields['actividad'].queryset = Actividad.objects.filter(
                    proyecto_id=proyecto_id,
                    estado__in=['no_iniciado', 'en_proceso']
                )
            except Proyecto.DoesNotExist:
                form.fields['actividad'].queryset = Actividad.objects.none()
        else:
            # Si no hay proyecto seleccionado, mostrar queryset vacío
            form.fields['actividad'].queryset = Actividad.objects.none()
            
        return form

    def form_valid(self, form):
        user = self.request.user
        # Obtener o crear el Colaborador basado en el usuario actual
        colaborador, created = Colaborador.objects.get_or_create(
            email=user.email,
            defaults={
                'nombre': f"{user.first_name} {user.last_name}".strip() or user.username,
                'cargo': 'Usuario del Sistema',
                'telefono': ''
            }
        )
        
        form.instance.responsable = colaborador
        
        # Usar transacción para asegurar consistencia
        with transaction.atomic():
            # Guardar la bitácora primero
            response = super().form_valid(form)
            
            # Procesar imágenes múltiples
            imagenes_multiples = self.request.FILES.getlist('imagenes_multiples')
            imagenes_creadas = 0
            
            for imagen in imagenes_multiples:
                if imagen:
                    BitacoraArchivo.objects.create(
                        bitacora=self.object,
                        archivo=imagen,
                        nombre_original=imagen.name
                    )
                    imagenes_creadas += 1
            
            # Procesar archivos múltiples
            archivos_multiples = self.request.FILES.getlist('archivos_multiples')
            archivos_creados = 0
            
            for archivo in archivos_multiples:
                if archivo:
                    BitacoraArchivo.objects.create(
                        bitacora=self.object,
                        archivo=archivo,
                        nombre_original=archivo.name
                    )
                    archivos_creados += 1
            
            # Mensaje de éxito con información de archivos
            total_adjuntos = imagenes_creadas + archivos_creados
            if total_adjuntos > 0:
                mensaje_partes = []
                if imagenes_creadas > 0:
                    mensaje_partes.append(f'{imagenes_creadas} imagen(es)')
                if archivos_creados > 0:
                    mensaje_partes.append(f'{archivos_creados} archivo(s)')
                
                mensaje = f"Entrada de bitácora creada exitosamente con {' y '.join(mensaje_partes)} adjunto(s)."
                messages.success(self.request, mensaje)
            else:
                messages.success(self.request, 'Entrada de bitácora creada exitosamente.')
            
            return response

class BitacoraDetailView(LoginRequiredMixin, DetailView):
    model = Bitacora
    template_name = 'proyectos/bitacora/detail.html'
    context_object_name = 'bitacora'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recursos'] = self.object.recursos.all()
        context['archivos_adjuntos'] = self.object.archivos_adjuntos.all()
        return context

class BitacoraUpdateView(LoginRequiredMixin, UpdateView):
    model = Bitacora
    template_name = 'proyectos/bitacora/form.html'
    form_class = BitacoraForm
    success_url = reverse_lazy('proyectos:bitacora_list')
    
    def form_valid(self, form):
        # Usar transacción para asegurar consistencia
        with transaction.atomic():
            # Guardar la bitácora
            response = super().form_valid(form)
            
            # Procesar nuevas imágenes múltiples
            imagenes_multiples = self.request.FILES.getlist('imagenes_multiples')
            imagenes_creadas = 0
            
            for imagen in imagenes_multiples:
                if imagen:
                    BitacoraArchivo.objects.create(
                        bitacora=self.object,
                        archivo=imagen,
                        nombre_original=imagen.name
                    )
                    imagenes_creadas += 1
            
            # Procesar nuevos archivos múltiples
            archivos_multiples = self.request.FILES.getlist('archivos_multiples')
            archivos_creados = 0
            
            for archivo in archivos_multiples:
                if archivo:
                    BitacoraArchivo.objects.create(
                        bitacora=self.object,
                        archivo=archivo,
                        nombre_original=archivo.name
                    )
                    archivos_creados += 1
            
            # Mensaje de éxito con información de archivos
            total_adjuntos = imagenes_creadas + archivos_creados
            if total_adjuntos > 0:
                mensaje_partes = []
                if imagenes_creadas > 0:
                    mensaje_partes.append(f'{imagenes_creadas} nueva(s) imagen(es)')
                if archivos_creados > 0:
                    mensaje_partes.append(f'{archivos_creados} nuevo(s) archivo(s)')
                
                mensaje = f"Bitácora actualizada exitosamente con {' y '.join(mensaje_partes)} adjunto(s)."
                messages.success(self.request, mensaje)
            else:
                messages.success(self.request, 'Bitácora actualizada exitosamente.')
            
            return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Entrada de Bitácora'
        # Obtener archivos adjuntos existentes
        context['archivos_existentes'] = self.object.archivos_adjuntos.all()
        return context

@require_http_methods(["POST"])
def eliminar_archivo_bitacora(request, archivo_id):
    """Vista AJAX para eliminar archivos adjuntos de bitácora"""
    try:
        archivo = get_object_or_404(BitacoraArchivo, id=archivo_id)
        
        # Verificar que el usuario tenga permisos (opcional - personalizar según necesidades)
        # Por ahora, cualquier usuario autenticado puede eliminar
        
        # Eliminar el archivo físico del sistema
        if archivo.archivo:
            try:
                archivo.archivo.delete()
            except:
                pass  # Archivo ya no existe en el sistema de archivos
        
        # Eliminar el registro de la base de datos
        archivo.delete()
        
        return JsonResponse({'success': True, 'message': 'Archivo eliminado exitosamente'})
        
    except BitacoraArchivo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Archivo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)