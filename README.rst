This application make more simple to input the data in forms that use dependent fields
and works with linear dependence and when one field depends on several fields.

Developed in association with `WinePad GmbH <https://www.winepad.at/>`_.

How to use on frontend
----------------------
Add "dfapp" to your INSTALLED_APPS setting like this:
::

    INSTALLED_APPS = [
        ...
        'dfapp',
    ]

Сreate your own form inherited from "DependentFieldsMixin":
::

    from dfapp.mixins import DependentFieldsMixin

    class UpdateFrontendForm(DependentFieldsMixin, forms.ModelForm):
        something here

You need to point a minimum one linear dependence, otherwise you will not see the changes.

For example, I have models "Country", "Region"** and "District". These models connected each other through foreign key. Manager models should be "MixinManager":
::

    from dfapp.mixins import MixinManager

    class Country(models.Model):
        ...
        objects = MixinManager()

    class Region(models.Model):
        country = models.ForeignKey(Country ...)
        ...
        objects = MixinManager()

    class District(models.Model):
        region = models.ForeignKey(Region ...)
        objects = MixinManager()

And I want to accelerate the adding model "Wine".
::

    class Wine(models.Model):
        country = models.ForeignKey(Country ...)
        region = models.ForeignKey(Region ...)
        district = models.ForeignKey(District ...)
        title = models.CharField(...)
        objects = MixinManager()

So, I customize the form so to point linear dependence, url, class Meta and class Media. In class Meta you point widget's fields inheritated from "MixinSelectWidget()":
::

    from dfapp.mixins import MixinSelectWidget

    class UpdateFrontendForm(DependentFieldsMixin, forms.ModelForm):
        data_url = '/name_your_app/edit/frontend/form/'
        linear_dependencies = {
            'country': ['region', 'district'],
        }

        class Meta:
            model = Wine
            fields = ['country', 'region', 'district', 'title']
            widgets = {
                'country': MixinSelectWidget(),
                'region': MixinSelectWidget(),
                'district': MixinSelectWidget(),
            }

        class Media:
            js = ('dfapp/js/update_form.js',)

In "data_url" you point full path to your view with your app's label.
For example, main URLconf looks so:
::

    urlpatterns = [
        path('edit/frontend/form/<int:pk>/', Your_View.as_view(), name='Your_View_Name'),
        ...
    ]

In form's "data_url" you point "name_your_app/some_url_to_your_view/" without "<int:pk>/". You add it in URLconf.

You can point several linear dependencies, like so:
::

    class UpdateFrontendForm(DependentFieldsMixin, forms.ModelForm):
        data_url = '...'
        linear_dependencies = {
            'country': ['region', 'district'],
            'country2': ['region2', 'district2'],
        }

**Most importantly, that the model fields included these fields!**

Create views. You need to create two views. First view will initialize the form. Second will create the form with updating data.
Basic configuration first view may looks so:
::

    class IndexPageView(CreateView):
        form_class = UpdateFrontendForm
        template_name = 'base.html'
        success_url = '/'

Basic configuration second view looks so:
::

    from dfapp.views import CheckCTView

    class FrontendFormView(CheckCTView):
        form_class = UpdateFrontendForm

Add need urls in URLconf:
::

    from yourapp.views import IndexPageView, FrontendFormView

    urlpatterns = [
        path('', IndexPageView.as_view()),
        path('edit/frontend/form/<int:pk>/', FrontendFormView.as_view()),
        ...
    ]

You can also point an independent dependency. If a country is selected, will be displayed "mark" that has only a country will be displayed. If a region is selected, will be displayed "marks" thet has "country" and "region". Id a district selected, will be displayed "marks" thet has "country" and "region" and "district". The key fields in independent_dependencies should be also inheritated MixinSelectWidget.

The configuration form may looks so:
::

    class UpdateFrontendForm(DependentFieldsMixin, forms.ModelForm):
        data_url = '...'
        linear_dependencies = {
            'country': ['region', 'district'],
        }
        independent_dependencies = {
            'mark': ['country', 'region', 'district'],
            'mark2': ['country', 'region'],
        }

        class Meta:
            ...
            widgets = {
                'country': MixinSelectWidget(),
                'region': MixinSelectWidget(),
                'district': MixinSelectWidget(),
                'mark': MixinSelectWidget(),
                'mark2': MixinSelectWidget(),
            }

That's all. The configuration of formset, inline formset is similar to the standard.

How to use on backend
---------------------
**Add url that will handle requests from backend only one time!**
::

    from dfapp.views import CheckCTView

    urlpatterns = [
        ...
        path('edit/admin/form/<int:pk>/', CheckCTView.as_view()),
        ...
    ]

Make the form for backend like for frontend.

Example:
::

    class UpdateAdminForm(DependentFieldsMixin, forms.ModelForm):
        data_url = '...'
        linear_dependencies = {
            'country': ['region', 'district'],
        }
        independent_dependencies = {
            'mark': ['country', 'region', 'district'],
        }

        class Meta:
            model = Wine
            fields = ['country', 'region', 'district', 'mark', 'title']

        class Media:
            js = ('dfapp/js/update_form.js',)

**Specify "data_url" without "<int:pk>"!**

Add created form in configuration your model in admin.py.
::

    @admin.register(Wine)
    class WineAdmin(admin.ModelAdmin):
        list_display = ['title', 'pk', 'country', 'region', 'district', 'mark', 'mark2']
        form = UpdateAdminForm

The configuration of formset, inline formset is similar to the standard.
::

    @admin.register(Recomendation_container)
    class Recomendation_containerAdmin(admin.ModelAdmin):
        list_display = ['recom_1', 'recom_2']
        form = RecomendationForm


    class RecomendationInline(admin.TabularInline):
        model = Recomendation_container
        extra = 0
        form = RecomendationForm

    @admin.register(Wine)
    class WineAdmin(admin.ModelAdmin):
        list_display = ['title', 'pk', 'country', 'region', 'district', 'mark', 'mark2']
        inlines = [RecomendationInline]
        form = UpdateAdminForm

How to use with proxy model
---------------------------
Create proxy model may be like this.
::

    class MetaGeography(models.Model):
        title = models.CharField(...)
        parent = models.ForeignKey('self'...)

        objects = MixinManager()


    class MetaCountry(MetaGeography):
        class Meta:
            proxy = True
            managed = False


    class MetaRegion(MetaGeography):
        class Meta:
            proxy = True
            managed = False


    class MetaDistrict(MetaGeography):
        class Meta:
            proxy = True
            managed = False

There is model container all these models.
::

    class MetaWine(models.Model):
    country = models.ForeignKey(MetaCountry, related_name='country' ...)
    region = models.ForeignKey(MetaRegion, related_name='region' ...)
    district = models.ForeignKey(MetaDistrict, related_name='district' ...)
    title = models.CharField(...)

    objects = MixinManager()

Create the form as shown earlier. And add your form on frontend or backend.

How to use with generic inline formset
--------------------------------------
You may be have models like this.
::

    from django.contrib.contenttypes.models import ContentType
    from django.contrib.contenttypes.fields import GenericForeignKey

    class GenericRecomendation_1(models.Model):
        title = models.CharField(...)

        objects = MixinManager()


    class GenericRecomendation_2(models.Model):
        title = models.CharField(...)
        recom_1 = models.ForeignKey(...)

        objects = MixinManager()

    class GenericRecomendation_container(models.Model):
        title = models.CharField(...)
        recom_1 = models.ForeignKey(GenericRecomendation_1 ...)
        recom_2 = models.ForeignKey(GenericRecomendation_2 ...)
        content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
        object_id = models.PositiveIntegerField()
        content_object = GenericForeignKey('content_type', 'object_id')

        objects = MixinManager()

Create form.
::

    class GenericRecomendationForm(DependentFieldsMixin, forms.ModelForm):
    data_url = '...'
    linear_dependencies = {
        'recom_1': ['recom_2'],
    }

    class Meta:
        model = GenericRecomendation_container
        fields = ['recom_1', 'recom_2']

    class Media:
        js = ('js/update_form.js',)

Register model in admin.py.
::

    @admin.register(GenericRecomendation_container)
    class GenericRecomendation_containerAdmin(admin.ModelAdmin):
        list_display = ['recom_1', 'recom_2']
        form = GenericRecomendationForm

Specify form as "GenericInlineFormset".
::

    from django.contrib.contenttypes.admin import GenericTabularInline

    class GenericRecomendationInline(GenericTabularInline):
        model = GenericRecomendation_container
        extra = 0
        form = GenericRecomendationForm

    @admin.register(Wine)
    class WineAdmin(admin.ModelAdmin):
        list_display = ['title', 'pk', 'country', 'region', 'district', 'mark', 'mark2']
        inlines = [GenericRecomendationInline]
        form = UpdateAdminForm

You can use InlineFormset together GenericInlineFormset that very convenient.
::

    @admin.register(Wine)
    class WineAdmin(admin.ModelAdmin):
        list_display = ['title', 'pk', 'country', 'region', 'district', 'mark', 'mark2']
        inlines = [RecomendationInline, GenericRecomendationInline]
        form = UpdateAdminForm