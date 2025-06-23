from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from .models import SolicitudMejora, ComentarioSolicitud, AdjuntoSolicitud
from .forms import (
    SolicitudMejoraForm, SolicitudMejoraUpdateForm, ComentarioSolicitudForm,
    AdjuntoSolicitudForm, FiltroSolicitudesForm, SolicitudMejoraConAdjuntosForm
)

User = get_user_model()

class MejoraContinuaDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal del módulo de mejora continua."""
    template_name = 'mejora_continua/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todas las solicitudes del usuario o todas si es staff
        if self.request.user.is_staff:
            solicitudes = SolicitudMejora.objects.all()
        else:
            solicitudes = SolicitudMejora.objects.filter(solicitante=self.request.user)
        
        # Estadísticas generales
        context['total_solicitudes'] = solicitudes.count()
        context['solicitudes_pendientes'] = solicitudes.filter(estado='pendiente').count()
        context['solicitudes_en_desarrollo'] = solicitudes.filter(estado='en_desarrollo').count()
        context['solicitudes_completadas'] = solicitudes.filter(estado='completada').count()
        
        # Mis solicitudes recientes
        context['mis_solicitudes'] = SolicitudMejora.objects.filter(
            solicitante=self.request.user
        ).order_by('-fecha_solicitud')[:5]
        
        # Si es staff, mostrar solicitudes asignadas
        if self.request.user.is_staff:
            context['solicitudes_asignadas'] = SolicitudMejora.objects.filter(
                asignado_a=self.request.user
            ).exclude(estado__in=['completada', 'cancelada', 'rechazada']).order_by('-fecha_solicitud')[:5]
            
            # Estadísticas por estado
            context['stats_por_estado'] = solicitudes.values('estado').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Estadísticas por tipo
            context['stats_por_tipo'] = solicitudes.values('tipo_solicitud').annotate(
                count=Count('id')
            ).order_by('-count')
        
        return context

class SolicitudMejoraListView(LoginRequiredMixin, ListView):
    """Lista de solicitudes de mejora."""
    model = SolicitudMejora
    template_name = 'mejora_continua/solicitud_list.html'
    context_object_name = 'solicitudes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SolicitudMejora.objects.all()
        
        # Los usuarios normales solo ven sus propias solicitudes
        if not self.request.user.is_staff:
            queryset = queryset.filter(solicitante=self.request.user)
        
        # Aplicar filtros
        form = FiltroSolicitudesForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data['estado']:
                queryset = queryset.filter(estado=form.cleaned_data['estado'])
            if form.cleaned_data['tipo_solicitud']:
                queryset = queryset.filter(tipo_solicitud=form.cleaned_data['tipo_solicitud'])
            if form.cleaned_data['modulo_afectado']:
                queryset = queryset.filter(modulo_afectado=form.cleaned_data['modulo_afectado'])
            if form.cleaned_data['prioridad']:
                queryset = queryset.filter(prioridad=form.cleaned_data['prioridad'])
            if form.cleaned_data['asignado_a']:
                queryset = queryset.filter(asignado_a=form.cleaned_data['asignado_a'])
        
        # Búsqueda por texto
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(titulo__icontains=search_query) |
                Q(descripcion__icontains=search_query) |
                Q(numero_solicitud__icontains=search_query)
            )
        
        return queryset.order_by('-fecha_solicitud')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = FiltroSolicitudesForm(self.request.GET)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class SolicitudMejoraDetailView(LoginRequiredMixin, DetailView):
    """Detalle de una solicitud de mejora."""
    model = SolicitudMejora
    template_name = 'mejora_continua/solicitud_detail.html'
    context_object_name = 'solicitud'
    
    def dispatch(self, request, *args, **kwargs):
        solicitud = self.get_object()
        # Los usuarios normales solo pueden ver sus propias solicitudes
        if not request.user.is_staff and solicitud.solicitante != request.user:
            messages.error(request, 'No tienes permisos para ver esta solicitud.')
            return redirect('mejora_continua:solicitud_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comentario_form'] = ComentarioSolicitudForm(user=self.request.user)
        context['adjunto_form'] = AdjuntoSolicitudForm()
        # context['multiple_upload_form'] = MultipleFileUploadForm()  # Temporarily disabled
        context['update_form'] = SolicitudMejoraUpdateForm(instance=self.object) if self.request.user.is_staff else None
        
        # Organizar adjuntos por tipo
        adjuntos = self.object.adjuntos.all()
        context['adjuntos_imagenes'] = adjuntos.filter(tipo_archivo='imagen')
        context['adjuntos_documentos'] = adjuntos.exclude(tipo_archivo='imagen')
        
        return context

class SolicitudMejoraCreateView(LoginRequiredMixin, CreateView):
    """Crear nueva solicitud de mejora con archivos adjuntos."""
    model = SolicitudMejora
    form_class = SolicitudMejoraConAdjuntosForm
    template_name = 'mejora_continua/solicitud_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Guardar la solicitud primero
        form.instance.solicitante = self.request.user
        solicitud = form.save()
        
        # Procesar archivos adjuntos si los hay
        archivos = self.request.FILES.getlist('archivos')
        archivos_guardados = 0
        
        for archivo in archivos:
            adjunto = AdjuntoSolicitud(
                solicitud=solicitud,
                archivo=archivo,
                descripcion=f'Archivo adjunto durante la creación de la solicitud',
                subido_por=self.request.user
            )
            adjunto.save()
            archivos_guardados += 1
        
        # Mensaje de éxito
        if archivos_guardados > 0:
            messages.success(
                self.request, 
                f'Solicitud de mejora creada exitosamente con {archivos_guardados} archivo(s) adjunto(s).'
            )
        else:
            messages.success(self.request, 'Solicitud de mejora creada exitosamente.')
        
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse('mejora_continua:solicitud_detail', kwargs={'pk': self.object.pk})

class SolicitudMejoraUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Actualizar estado y asignación de solicitud (solo staff)."""
    model = SolicitudMejora
    form_class = SolicitudMejoraUpdateForm
    template_name = 'mejora_continua/solicitud_update.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        # Si se está asignando por primera vez, guardar fecha de asignación
        if form.instance.asignado_a and not form.instance.fecha_asignacion:
            form.instance.fecha_asignacion = timezone.now()
        
        # Si se marca como completada, guardar fecha de completado
        if form.instance.estado == 'completada' and not form.instance.fecha_completado:
            form.instance.fecha_completado = timezone.now()
        
        messages.success(self.request, 'Solicitud actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('mejora_continua:solicitud_detail', kwargs={'pk': self.object.pk})

class ComentarioCreateView(LoginRequiredMixin, CreateView):
    """Agregar comentario a una solicitud."""
    model = ComentarioSolicitud
    form_class = ComentarioSolicitudForm
    
    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(SolicitudMejora, pk=kwargs['solicitud_pk'])
        # Verificar permisos
        if not request.user.is_staff and self.solicitud.solicitante != request.user:
            messages.error(request, 'No tienes permisos para comentar en esta solicitud.')
            return redirect('mejora_continua:solicitud_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.solicitud = self.solicitud
        form.instance.autor = self.request.user
        messages.success(self.request, 'Comentario agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('mejora_continua:solicitud_detail', kwargs={'pk': self.solicitud.pk})

class AdjuntoCreateView(LoginRequiredMixin, CreateView):
    """Subir archivo adjunto a una solicitud."""
    model = AdjuntoSolicitud
    form_class = AdjuntoSolicitudForm
    
    def dispatch(self, request, *args, **kwargs):
        self.solicitud = get_object_or_404(SolicitudMejora, pk=kwargs['solicitud_pk'])
        # Verificar permisos
        if not request.user.is_staff and self.solicitud.solicitante != request.user:
            messages.error(request, 'No tienes permisos para subir archivos a esta solicitud.')
            return redirect('mejora_continua:solicitud_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.solicitud = self.solicitud
        form.instance.subido_por = self.request.user
        messages.success(self.request, 'Archivo subido exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('mejora_continua:solicitud_detail', kwargs={'pk': self.solicitud.pk})

class MisSolicitudesView(LoginRequiredMixin, ListView):
    """Lista de mis solicitudes."""
    model = SolicitudMejora
    template_name = 'mejora_continua/mis_solicitudes.html'
    context_object_name = 'solicitudes'
    paginate_by = 15
    
    def get_queryset(self):
        return SolicitudMejora.objects.filter(
            solicitante=self.request.user
        ).order_by('-fecha_solicitud')

class SolicitudesAsignadasView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de solicitudes asignadas a mí (solo staff)."""
    model = SolicitudMejora
    template_name = 'mejora_continua/solicitudes_asignadas.html'
    context_object_name = 'solicitudes'
    paginate_by = 15
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return SolicitudMejora.objects.filter(
            asignado_a=self.request.user
        ).order_by('-fecha_solicitud')

# class MultipleFileUploadView(LoginRequiredMixin, CreateView):
#     """Vista para subir múltiples archivos a una solicitud - Temporalmente deshabilitada."""
#     pass

class EliminarAdjuntoView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un archivo adjunto."""
    model = AdjuntoSolicitud
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Verificar permisos
        if not request.user.is_staff and self.object.subido_por != request.user:
            messages.error(request, 'No tienes permisos para eliminar este archivo.')
            return redirect('mejora_continua:solicitud_detail', pk=self.object.solicitud.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre_archivo = self.object.nombre_original or self.object.archivo.name
        solicitud_pk = self.object.solicitud.pk
        
        # Eliminar archivo físico
        if self.object.archivo:
            try:
                self.object.archivo.delete()
            except:
                pass  # Si no se puede eliminar el archivo físico, continúa
        
        # Eliminar registro de la base de datos
        self.object.delete()
        
        messages.success(request, f'Archivo "{nombre_archivo}" eliminado exitosamente.')
        return redirect('mejora_continua:solicitud_detail', pk=solicitud_pk)
