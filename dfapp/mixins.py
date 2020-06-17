from django.db.models import Q
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.models import apply_limit_choices_to_to_formfield
from django.forms.widgets import Select
from django.contrib.admin.options import get_content_type_for_model


class MixinSelectWidget(Select):
    template_name = 'dfapp/widgets/front_select.html'


class DependentFieldsMixin():
    """
    In this mixin is main logic this django application
    """
    data_url = None
    dependencies = None
    attrs_dict = {'onchange': 'update_form(this)', 'style': 'visibility: visible'}

    def _html_output(self, *args, **kwargs):
        """
        Hide fields and update field choices
        """
        dependencies = self.dependencies
        self.attrs_dict['data-url'] = f'{self.data_url}{get_content_type_for_model(self._meta.model).pk}/'
        dependencies_parent_pipe = (name for name, val in dependencies.items() if len(dependencies[name].get('parent')) == 0)
        for name in dependencies_parent_pipe:
            self.attrs_dict['data-name'] = name
            self.update_field_widget(name, self.attrs_dict)
        dependencies_childs_pipe = ((name, val.get('parent')[0]) for name, val in self.dependencies.items() if len(val.get('parent')) > 0)
        for name, parent in dependencies_childs_pipe:
            self.update_field_widget(name, {'style': 'visibility: hidden'})
            formfield = self.fields[name]
            formfield.limit_choices_to = {parent: self[parent].value() or 0}
            apply_limit_choices_to_to_formfield(formfield)
        return super()._html_output(*args, **kwargs)

    def update_field_widget(self, name, attrs_dict):
        """
        Update field's widget with passed dict
        """
        widget = getattr(self.fields[name].widget, 'widget', self.fields[name].widget)
        widget.attrs.update(attrs_dict)

    def return_changed(self):
        """
        Return to frontend only changed fields
        """
        def get_changed_fields(obj):
            dependencies = obj.dependencies
            ind_list = [field for field in dependencies if dependencies[field].get('parent') and not dependencies[field].get('key_parent')]
            sequence = dependencies[obj.data.get('active_field')].get('childs') if type(obj.data.get('active_field')) == str else None
            lin_list = []
            if sequence:
                lin_list.append(sequence[0])
                idx = 1
                while len(sequence) > idx and obj[lin_list[-1]].value():
                    lin_list.append(sequence[idx])
                    idx += 1
            _list = ind_list + lin_list
            self.built_choices(dependencies, ind_list, lin_list)
            self.update_widget_changed_fields(_list)
            return _list
        return {self[item].auto_id: f'{self[item]}' for item in get_changed_fields(self)}

    def built_choices(self, dependencies, ind_list, lin_list):
        """
        Update field choices with passed data
        """
        path_to_key_parent, key_parent = self.data.get('active_field'), self.data.get('active_field')
        if lin_list:
            for name in lin_list:
                parent = dependencies[name].get('parent')[0]
                formfield = self.fields[name]
                self.fields[name].limit_choices_to = {parent: self[parent].value() or 0, path_to_key_parent: self[key_parent].value() or 0}
                apply_limit_choices_to_to_formfield(formfield)
                path_to_key_parent = name + '__' + path_to_key_parent
        if ind_list:
            for name in ind_list:
                formfield = self.fields[name]
                formfield.choices = self.get_field_choices(formfield, dependencies[name].get('parent'))

    def get_field_choices(self, formfield, childs):
        """
        Get choices for received formfield
        """
        formfield_queryset = formfield.queryset
        field_choices = BLANK_CHOICE_DASH
        for index, child in enumerate(childs):
            if self.fields[child].queryset.filter(id=self[child].value() or 0).exists():
                query = dict(list({child: self[child].value()}.items()) + list({f'{item}__isnull': True for item in childs[index + 1:]}.items()))
                item_choices = tuple(formfield_queryset.filter(Q(**query)).values_list('id', 'title'))
                field_choices = field_choices + [(f'{self.fields[child].queryset.filter(id=self[child].value()).first()} ({len(item_choices)})', (item_choices))]
        return field_choices

    def update_widget_changed_fields(self, seq):
        """
        If field choices more than one than field is displayed
        """
        seq_choices_pipe = (name for name in seq if len(self.fields[name].choices) > 1)
        for name in seq_choices_pipe:
            self.attrs_dict["data-name"] = name
            self.update_field_widget(name, self.attrs_dict)
        list(self.update_field_widget(name, {'style': 'visibility: hidden'}) for name in seq if len(self.fields[name].choices) == 1)
