from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Case, When, IntegerField, F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.forms import DateInput
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import pandas as pd
import io
import json

from proyectos.models import Actividad, Proyecto, Bitacora, Colaborador
from proyectos.forms.actividad_forms import ActividadForm
from proyectos.forms.import_forms import ActividadImportForm


class ActividadListView(LoginRequiredMixin, ListView):
    model = Actividad
    template_name = 'proyectos/actividad/list.html'
    context_object_name = 'actividades'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('proyecto')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(actividad__icontains=search) |
                Q(proyecto__nombre_proyecto__icontains=search) |
                Q(proyecto__cliente__icontains=search)
            )
        
        # Filtro por proyecto
        proyecto_id = self.request.GET.get('proyecto_id')
        if proyecto_id:
            queryset = queryset.filter(proyecto_id=proyecto_id)
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        # Filtro por centro de costos
        centro_costo = self.request.GET.get('centro_costo')
        if centro_costo:
            queryset = queryset.filter(proyecto__centro_costos=centro_costo)
        
        # Anotar con información adicional
        return queryset.annotate(
            dias_restantes=Case(
                When(fin__lt=timezone.now().date(), then=Value(0)),
                default=F('fin') - timezone.now().date(),
                output_field=IntegerField()
            ),
            total_horas=Coalesce(Count('bitacoras'), 0)
        ).order_by('inicio', 'fin')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = dict(Actividad.ESTADOS_CHOICES)
        
        # Si se está filtrando por proyecto, agregar el proyecto al contexto
        proyecto_id = self.request.GET.get('proyecto_id')
        if proyecto_id:
            context['proyecto'] = get_object_or_404(Proyecto, pk=proyecto_id)
        
        # Obtener los centros de costos disponibles para el filtro
        centros_costos = Proyecto.objects.values_list('centro_costos', flat=True).distinct().order_by('centro_costos')
        context['centros_costos'] = centros_costos
        
        # Añadir filtros actuales al contexto
        context['filtros'] = {
            'centro_costo': self.request.GET.get('centro_costo', ''),
            'estado': self.request.GET.get('estado', '')
        }
        
        return context


class ActividadCreateView(LoginRequiredMixin, CreateView):
    model = Actividad
    template_name = 'proyectos/actividad/form.html'
    form_class = ActividadForm
    
    def get_success_url(self):
        return reverse('proyectos:actividad_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Remove the creado_por assignment since Actividad model doesn't have this field
        messages.success(self.request, 'Actividad creada exitosamente.')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filtrar proyectos activos en el formulario
        form.fields['proyecto'].queryset = Proyecto.objects.filter(estado__in=['pendiente', 'en_progreso'])
        
        # Establecer la fecha mínima para los selectores de fecha
        today = timezone.now().strftime('%Y-%m-%d')
        form.fields['inicio'].widget.attrs['min'] = today
        form.fields['fin'].widget.attrs['min'] = today
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nueva Actividad'
        
        # Añadir todos los proyectos con sus centros de costos al contexto
        proyectos = Proyecto.objects.filter(estado__in=['pendiente', 'en_progreso'])
        context['proyectos_con_centro_costos'] = [
            {'id': p.id, 'nombre': p.nombre_proyecto, 'centro_costos': p.centro_costos}
            for p in proyectos
        ]
        
        return context


class ActividadDetailView(LoginRequiredMixin, DetailView):
    model = Actividad
    template_name = 'proyectos/actividad/detail.html'
    context_object_name = 'actividad'
    
    def get_queryset(self):
        return super().get_queryset().select_related('proyecto')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad = self.get_object()
        
        # Obtener bitácoras relacionadas
        context['bitacoras'] = actividad.bitacoras.select_related(
            'responsable'
        ).order_by('-fecha_registro')
        
        # Agregar colaboradores para el modal de crear bitácora
        context['colaboradores'] = Colaborador.objects.all().order_by('nombre')
        
        return context


class ActividadUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Actividad
    template_name = 'proyectos/actividad/form.html'
    form_class = ActividadForm
    
    def test_func(self):
        actividad = self.get_object()
        return self.request.user.has_perm('proyectos.change_actividad') or \
               self.request.user == actividad.proyecto.lider
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permiso para editar esta actividad.')
        return redirect('proyectos:actividad_list')
    
    def get_success_url(self):
        return reverse('proyectos:actividad_detail', kwargs={'pk': self.object.pk})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Establecer la fecha mínima para los selectores de fecha
        today = timezone.now().strftime('%Y-%m-%d')
        form.fields['inicio'].widget.attrs['min'] = today
        form.fields['fin'].widget.attrs['min'] = today
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Actividad'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Actividad actualizada exitosamente.')
        return super().form_valid(form)


class ActividadImportView(LoginRequiredMixin, FormView):
    template_name = 'proyectos/actividad/import.html'
    form_class = ActividadImportForm
    success_url = reverse_lazy('proyectos:actividad_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proyecto_queryset'] = Proyecto.objects.filter(estado__in=['pendiente', 'en_progreso'])
        return kwargs
    
    def dispatch(self, request, *args, **kwargs):
        # Protección adicional contra doble envío
        if request.method == 'POST':
            # Verificar si hay un token de procesamiento activo en la sesión
            import_token = request.session.get('import_token')
            current_token = request.POST.get('import_token')
            
            if import_token and current_token and import_token == current_token:
                messages.warning(request, 'Ya hay una importación en progreso. Por favor espere.')
                return redirect('proyectos:actividad_import')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Generar token único para esta importación
        import uuid
        import_token = str(uuid.uuid4())
        self.request.session['import_token'] = import_token
        
        try:
            archivo_excel = form.cleaned_data['archivo_excel']
            proyecto = form.cleaned_data['proyecto']
            
            # Leer el archivo Excel
            df = pd.read_excel(archivo_excel)
            
            # Validar las columnas requeridas
            required_columns = ['actividad', 'inicio', 'fin', 'estado']
            if not all(col in df.columns for col in required_columns):
                messages.error(self.request, 'El archivo Excel debe contener las columnas: ' + ', '.join(required_columns))
                return self.form_invalid(form)
            
            # Validar que no haya filas vacías en campos obligatorios
            empty_rows = df[df[required_columns].isnull().any(axis=1)]
            if not empty_rows.empty:
                messages.error(self.request, f'Se encontraron {len(empty_rows)} filas con campos obligatorios vacíos. Por favor revise el archivo.')
                return self.form_invalid(form)
            
            # Procesar cada fila
            actividades_creadas = 0
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Validar que no exista una actividad duplicada en el mismo proyecto
                    if Actividad.objects.filter(
                        proyecto=proyecto, 
                        actividad=row['actividad']
                    ).exists():
                        errores.append(f'Fila {index + 2}: La actividad "{row["actividad"]}" ya existe en este proyecto.')
                        continue
                    
                    # Calculate duration if not provided
                    duracion = row.get('duracion', 1)
                    if pd.isna(duracion) or duracion == '':
                        # Calculate duration from dates if not provided
                        fecha_inicio = pd.to_datetime(row['inicio'])
                        fecha_fin = pd.to_datetime(row['fin'])
                        duracion = (fecha_fin - fecha_inicio).days + 1
                    
                    # Set default values for optional fields
                    avance = row.get('avance', 0)
                    if pd.isna(avance) or avance == '':
                        avance = 0
                    
                    predecesoras = row.get('predecesoras', '')
                    if pd.isna(predecesoras):
                        predecesoras = ''
                        
                    observaciones = row.get('observaciones', '')
                    if pd.isna(observaciones):
                        observaciones = ''
                    
                    Actividad.objects.create(
                        proyecto=proyecto,
                        actividad=row['actividad'],
                        inicio=row['inicio'],
                        fin=row['fin'],
                        duracion=duracion,
                        avance=avance,
                        estado=row['estado'],
                        predecesoras=predecesoras,
                        observaciones=observaciones
                    )
                    actividades_creadas += 1
                except Exception as e:
                    errores.append(f'Fila {index + 2}: Error al importar actividad "{row.get("actividad", "desconocida")}": {str(e)}')
            
            # Mostrar resultados
            if actividades_creadas > 0:
                messages.success(self.request, f'Se importaron {actividades_creadas} actividades exitosamente.')
            
            if errores:
                for error in errores[:5]:  # Mostrar solo los primeros 5 errores
                    messages.warning(self.request, error)
                if len(errores) > 5:
                    messages.warning(self.request, f'... y {len(errores) - 5} errores adicionales.')
            
            # Limpiar token de la sesión
            if 'import_token' in self.request.session:
                del self.request.session['import_token']
            
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo Excel: {str(e)}')
            # Limpiar token de la sesión en caso de error
            if 'import_token' in self.request.session:
                del self.request.session['import_token']
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar token único al contexto para el formulario
        import uuid
        context['form_token'] = str(uuid.uuid4())
        return context


class ActividadPlantillaExcelView(LoginRequiredMixin, TemplateView):
    """Vista para generar y descargar plantilla de Excel para actividades"""
    
    def get(self, request, *args, **kwargs):
        # Crear un DataFrame con las columnas y datos de ejemplo
        datos_ejemplo = {
            'actividad': ['Análisis de Requerimientos', 'Diseño del Sistema', 'Desarrollo Backend', 'Pruebas Unitarias'],
            'inicio': ['2025-06-01', '2025-06-15', '2025-07-01', '2025-08-01'],
            'fin': ['2025-06-14', '2025-06-30', '2025-07-31', '2025-08-15'],
            'duracion': [10, 12, 22, 10],
            'avance': [100, 75, 25, 0],
            'estado': ['finalizado', 'en_proceso', 'en_proceso', 'no_iniciado'],
            'predecesoras': ['', '1', '2', '3'],
            'observaciones': [
                'Análisis completo de todos los requerimientos funcionales',
                'Diseño de arquitectura y base de datos en progreso',
                'Desarrollo de APIs y lógica de negocio',
                'Pruebas pendientes de inicio'
            ]
        }
        
        df = pd.DataFrame(datos_ejemplo)
        
        # Crear archivo Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Actividades')
            
            # Obtener la hoja de trabajo para formatear
            worksheet = writer.sheets['Actividades']
            
            # Ajustar el ancho de las columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
            # Agregar una segunda hoja con información sobre los valores válidos
            info_data = {
                'Campo': ['estado', 'formato_fechas', 'duracion', 'avance'],
                'Valores_Válidos': [
                    'no_iniciado, en_proceso, finalizado',
                    'YYYY-MM-DD (ejemplo: 2025-06-01)',
                    'Número entero de días',
                    'Porcentaje entre 0 y 100'
                ],
                'Descripción': [
                    'Estado actual de la actividad',
                    'Formato obligatorio para fechas de inicio y fin',
                    'Duración estimada en días',
                    'Porcentaje de avance completado'
                ]
            }
            df_info = pd.DataFrame(info_data)
            df_info.to_excel(writer, index=False, sheet_name='Información')
        
        buffer.seek(0)
        
        # Crear respuesta HTTP con el archivo
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_actividades.xlsx"'
        
        return response

@require_http_methods(["POST"])
def actividad_bulk_delete(request):
    """Vista para eliminar múltiples actividades de forma masiva."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=401)
    
    try:
        # Obtener IDs de actividades a eliminar
        activity_ids = request.POST.getlist('activity_ids')
        
        if not activity_ids:
            return JsonResponse({'success': False, 'error': 'No se proporcionaron actividades para eliminar'})
        
        # Validar que el usuario tenga permisos para eliminar actividades
        # (puedes agregar lógica adicional de permisos aquí si es necesario)
        
        # Obtener las actividades que existen
        actividades = Actividad.objects.filter(id__in=activity_ids)
        
        if not actividades.exists():
            return JsonResponse({'success': False, 'error': 'No se encontraron actividades válidas para eliminar'})
        
        # Contar actividades antes de eliminar
        deleted_count = actividades.count()
        
        # Eliminar actividades (esto también eliminará las bitácoras y recursos relacionados por CASCADE)
        actividades.delete()
        
        return JsonResponse({
            'success': True, 
            'deleted_count': deleted_count,
            'message': f'Se eliminaron {deleted_count} actividades exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error al eliminar actividades: {str(e)}'
        }, status=500)

# Vista para API que devuelve actividades de un proyecto (usada en formularios AJAX)
@require_http_methods(["GET"])
def actividades_por_proyecto(request, proyecto_id):
    """Devuelve las actividades de un proyecto en formato JSON para su uso en AJAX."""
    actividades = Actividad.objects.filter(
        proyecto_id=proyecto_id
    ).values('id', 'actividad')
    return JsonResponse(list(actividades), safe=False)
