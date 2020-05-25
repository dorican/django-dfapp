from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.models import apply_limit_choices_to_to_formfield
from django.forms.widgets import Select
from django.contrib.admin.options import get_content_type_for_model


class MixinSelectWidget(Select):
    template_name = 'dfapp/widgets/front_select.html'


class MixinQuerySet(models.QuerySet):
    def queryset_filter(self, **kwargs):
        return self.filter(**kwargs)


class MixinManager(models.Manager):
    _queryset_class = MixinQuerySet


class DependentFieldsMixin():
    """
    In this mixin is main logic this django application
    """
    data_url = None
    remote_parent_field = None
    linear_dependencies = None
    independent_dependencies = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dependencies = self.get_dependencies()
        if dependencies:
            count_checker, counter = len(self.linear_dependencies), 0
        keys = []
        attrs_dict = {'onchange': 'update_form(this)', 'data-url': f'{self.data_url}{get_content_type_for_model(self._meta.model).pk}/'}
        if self.field_checker(dependencies):
            for parent_name, childs in dependencies.items():
                keys.append(parent_name)
                if counter < count_checker:
                    attrs_dict['data-name'] = parent_name
                    for item in self._meta.model._meta.get_field(parent_name).target_field.model._meta.fields:
                        if item.is_relation:
                            self.remote_parent_field = item.name
                            self.fields[parent_name].limit_choices_to = {f'{self.remote_parent_field}__isnull': True}
                            apply_limit_choices_to_to_formfield(self.fields[parent_name])
                else:
                    attrs_dict = {'style': 'visibility: hidden'}
                self.update_field_widget(parent_name, attrs_dict)
                attrs_dict['style'] = 'visibility: hidden'
                for child in childs:
                    if child not in keys:
                        self.update_field_widget(child, attrs_dict)
                counter += 1

    def get_dependencies(self):
        dependencies = self.linear_dependencies.copy() if self.linear_dependencies else None
        if self.independent_dependencies:
            dependencies.update(self.independent_dependencies)
        return dependencies

    def field_checker(self, dependencies):
        """
        Checking the form fields. If there is no field, then return False
        """
        form_fields = self._meta.fields
        if dependencies:
            for key, f_list in dependencies.items():
                if key not in form_fields:
                    return False
                for f in f_list:
                    if f not in form_fields:
                        return False
            return True

    def update_field_widget(self, field_name, style):
        """
        Update widget form's field
        """
        widget = getattr(self.fields[field_name].widget, 'widget', self.fields[field_name].widget)
        widget.attrs.update(style)

    def get_changed_fields(self):
        """
        Get fields to need to update
        """
        data = self.data
        control_field = self.data.get('active_field')
        linear_dependencies, independent_dependencies = self.linear_dependencies, self.independent_dependencies
        list_fields_to_change = []
        for parent_name, childs in linear_dependencies.items():
            if control_field == parent_name:
                list_fields_to_change.append(childs[0])
            elif control_field == childs[len(childs) - 1]:
                break
            elif control_field in childs:
                list_fields_to_change.append(childs[childs.index(control_field) + 1])
            for child in childs:
                if data.get(self.add_prefix(child)) and child not in list_fields_to_change and child != control_field:
                    list_fields_to_change.append(child)
        if independent_dependencies:
            list_fields_to_change += independent_dependencies.keys()
        return list_fields_to_change

    def form_to_dict(self):
        """
        Create dict. Key is form's field name with id, value is rendered form's field
        """
        template = 'id_{prefix}-{{}}'.format(**vars(self)).format if self.prefix else 'id_{}'.format
        return {template(item): f'{self[item]}' for item in self.get_changed_fields()}

    def built_dependencies_form(self):
        """
        Build dependencies before rendering form
        """
        data = self.data
        dependencies = self.get_dependencies()
        if dependencies:
            count_checker, counter = len(self.linear_dependencies), 0
        for parent_name, childs in dependencies.items():
            if counter < count_checker:
                checker = True
                for child in childs:
                    attrs_dict = {'onchange': 'update_form(this)', 'data-url': f'{self.data_url}{get_content_type_for_model(self._meta.model).pk}/', 'data-name': f'{child}'}
                    child_field = self.fields[child]
                    id_parent = data.get(self.add_prefix(parent_name)) if data.get(self.add_prefix(parent_name)) and checker else None
                    if self.remote_parent_field:
                        query = {self.remote_parent_field: id_parent}
                        child_field.limit_choices_to = {self.remote_parent_field: id_parent, f'{self.remote_parent_field}__isnull': False}
                    else:
                        query = {parent_name: id_parent}
                        child_field.limit_choices_to = {parent_name: id_parent}
                    apply_limit_choices_to_to_formfield(child_field)
                    attrs_dict['style'] = 'visibility: visible'
                    if len(child_field.choices) > 1 and checker:
                        self.update_field_widget(child, attrs_dict)
                    checker = self.fields[child].queryset.queryset_filter(pk=data.get(self.add_prefix(child)) or 0, **query).exists()
                    parent_name = child
            else:
                attrs_dict = {'style': 'visibility: visible'}
                parent_field = self.fields[parent_name]
                parent_field.choices = self.get_independent_choices(parent_name, childs)
                if len(parent_field.choices) > 1:
                    self.update_field_widget(parent_name, attrs_dict)
            counter += 1

    def get_independent_choices(self, parent_name, childs):
        """
        Get independent choices for parent field
        """
        field_choices = []
        for index, child in enumerate(childs):
            id_child_field = self.data.get(self.add_prefix(child))
            if id_child_field in [str(item.pk) for item in self.fields[child].queryset]:
                queryset_query = {child: id_child_field}
                queryset_query.update({f'{item}__isnull': True for item in childs[index + 1:]})
                item_choices = tuple(self.fields[parent_name].queryset.queryset_filter(**queryset_query).values_list('id', 'title'))
                field_choices = field_choices + [(f'{self.fields[child].queryset.queryset_filter(id=id_child_field).first()} ({len(item_choices)})', (item_choices))]
        return BLANK_CHOICE_DASH + field_choices
