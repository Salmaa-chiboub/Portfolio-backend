import django_filters
from .models import Project
from skills.models import SkillReference


class ProjectFilter(django_filters.FilterSet):
    skill = django_filters.CharFilter(
        field_name='skills__name',
        lookup_expr='iexact',
        label='Filter by skill name (case-insensitive)'
    )
    
    skills = django_filters.ModelMultipleChoiceFilter(
        field_name='skills',
        queryset=SkillReference.objects.all(),
        label='Filter by multiple skills'
    )
    
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created after this date (YYYY-MM-DD)'
    )
    
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created before this date (YYYY-MM-DD)'
    )

    class Meta:
        model = Project
        fields = {
            'title': ['icontains', 'iexact'],
            'description': ['icontains'],
            'created_at': ['year', 'month', 'day'],
        }
