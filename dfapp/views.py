from django.views.generic.edit import FormView
from django.views.generic import DetailView
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.contrib.admin.sites import site
from django.contrib import admin


class CheckCTView(DetailView):
    """
    The view that gets the ContentType model and passes the getted model to the next view
    """
    model = ContentType
    form_class = None

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            super().get(request, *args, **kwargs)
            return RenderFormView(request=request, args=args, kwargs=kwargs, model=self.object.model_class(), form_class=self.form_class).post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class RenderFormView(FormView):
    """
    The view that creates frontend form or backend form for getted model. This view is used for ajax form update.
    """
    template_name = ''
    response_class = JsonResponse
    success_url = '/'

    def get_form_class(self):
        # breakpoint()
        if 'admin' in self.request.META.get('HTTP_REFERER'):
            self.form_class = (site._registry.get(self.model) or admin.ModelAdmin(self.model, site)).get_form(self.request)
        return super().get_form_class()

    def form_valid(self, form):
        return self.form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        form = context['form']
        return self.response_class(form.return_changed())

    def get_prefix(self):
        # breakpoint()
        self.prefix = self.request.POST.get('prefix')
        return super().get_prefix()
