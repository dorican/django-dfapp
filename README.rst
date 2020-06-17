This application make more simple to input the data in forms that use dependent fields
and works with linear dependence and when one field depends on several fields.

Developed in association with `WinePad GmbH <https://www.winepad.at/>`_. Developer `Vasily Romanov <https://github.com/dorican>`_

How to use on frontend
----------------------
Add "dfapp" to your INSTALLED_APPS setting like this:
::

    INSTALLED_APPS = [
        ...
        'dfapp',
    ]

Create your own form inherited from "DependentFieldsMixin":
::

    from dfapp.mixins import DependentFieldsMixin

    class UpdateFrontendForm(DependentFieldsMixin, forms.ModelForm):
        something here

For example, I have models "Country", "Region"** and "District". These models connected each other through foreign key:
::

    from dfapp.mixins import MixinManager

    class Country(models.Model):
        ...

    class Region(models.Model):
        country = models.ForeignKey(Country ...)
        ...

    class District(models.Model):
        region = models.ForeignKey(Region ...)
        ...

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
        dependencies = {
            'country': {'key_parent': '', 'parent': [], 'all_parents': [], 'childs': ['region', 'district']},
            'region': {'key_parent': 'country', 'parent': ['country'], 'all_parents': ['country'], 'childs': ['district']},
            'district': {'key_parent': 'country', 'parent': ['region'], 'all_parents': ['country', 'region'], 'childs': [],
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

In "key_parent" you specify the first field in a linear dependency. In  "parent" specify field from which field is inherited. For a "region" it will be a "country", for a "district" - a "region". In 'all_parents' - all parent fields in this dependency begin with the specified field.

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
        dependencies = {
        'country': {'key_parent': '', 'parent': [], 'all_parents': [], 'childs': ['region2']},
        'region2': {'key_parent': 'country', 'parent': ['country'], 'all_parents': ['country'], 'childs': []},
        'region': {'key_parent': '', 'parent': [], 'all_parents': [], 'childs': ['district', 'subdistrict']},
        'district': {'key_parent': 'region', 'parent': ['region'], 'all_parents': ['region'], 'childs': ['subdistrict']},
        'subdistrict': {'key_parent': 'region', 'parent': ['district'], 'all_parents': ['region', 'district'], 'childs': []},
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

You can also point an independent dependency. If a country is selected, will be displayed "mark" that has only a country will be displayed. If a region is selected, will be displayed "marks" thet has "country" and "region". Id a district selected, will be displayed "marks" thet has "country" and "region" and "district". The key fields in independent dependency should be also inheritated MixinSelectWidget.

The configuration form may looks so:
::

    class UpdateFrontendForm(DependentFieldsMixin, forms.ModelForm):
        data_url = '...'
        dependencies = {
            'country': {'key_parent': '', 'parent': [], 'all_parents': [], 'childs': ['region', 'district']},
            'region': {'key_parent': 'country', 'parent': ['country'], 'all_parents': ['country'], 'childs': ['district']},
            'district': {'key_parent': 'country', 'parent': ['region'], 'all_parents': ['country', 'region'], 'childs': [],
            'mark': {'key_parent': '', 'parent': ['country', 'region', 'district'], 'all_parents': [], 'childs': []},
            'mark2': {'key_parent': '', 'parent': ['country', 'region'], 'all_parents': [], 'childs': []},
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