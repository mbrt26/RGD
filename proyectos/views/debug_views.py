from django.http import HttpResponse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

def debug_template_loading(request):
    template_path = 'colaboradores/form.html'
    try:
        template = get_template(template_path)
        return HttpResponse(f"Template found at: {template.origin}")
    except TemplateDoesNotExist:
        return HttpResponse(f"Template not found: {template_path}", status=404)
