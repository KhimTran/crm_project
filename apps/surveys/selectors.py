"""Read-only survey list filtering by scheduled activity, in local calendar days."""
from datetime import datetime, time

from django.db.models import Count
from django.utils import timezone

from .models import Survey


def survey_list_queryset(filters):
    query = Survey.objects.annotate(sent=Count('surveyrecipient', distinct=True))
    if filters.get('q'):
        query = query.filter(title__icontains=filters['q'])
    if filters.get('status'):
        query = query.filter(status=filters['status'])
    start, end = filters.get('date_from'), filters.get('date_to')
    if start or end:
        query = query.filter(start_at__isnull=False, end_at__isnull=False)
    if start:
        query = query.filter(end_at__gte=timezone.make_aware(datetime.combine(start, time.min)))
    if end:
        query = query.filter(start_at__lte=timezone.make_aware(datetime.combine(end, time.max)))
    return query.order_by('survey_id')
