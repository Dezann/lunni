import csv
from collections import Counter
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import IntegrityError
from django.db.models import F, Q, Value, CharField, Sum, OuterRef, Subquery
from django.db.models.functions import Concat, Coalesce
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status, serializers
from rest_framework.generics import ListAPIView, CreateAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from merger.helpers import file_to_entries, Entry, pko_file_to_entries, mbank_savings_file_to_entries
from merger.models import TransactionLog, TransactionLogMerge, TransactionCategoryMatcher, TransactionCategory
from merger.serializers import TransactionLogSerializer, TransactionLogMergeSerializer, CreateTransactionLogSerializer, \
    TransactionCategorySerializer, TransactionCategoryMatcherSerializer, TransactionLogExportSerializer


# todo find better location for this
def is_unique(entry: Entry):
    return not TransactionLog.objects.filter(
        Q(date=entry['date']) &
        Q(description=entry['description']) &
        Q(account=entry['account']) &
        Q(amount=entry['amount'])
    ).exists()


@require_POST
@csrf_exempt
def upload(request, *args, **kwargs):
    in_memory_file: InMemoryUploadedFile = request.FILES.get('file')
    variant: str = request.POST.get('variant')
    bytes_io: BytesIO = in_memory_file.file

    if variant == 'mbank':
        converted_entries = file_to_entries(bytes_io)
    elif variant == 'mbank-savings':
        converted_entries = mbank_savings_file_to_entries(bytes_io)
    elif variant == 'pko':
        converted_entries = pko_file_to_entries(bytes_io)
    else:
        raise serializers.ValidationError('Unknown variant')

    # todo improve performance for large datasets
    # todo progress bar
    converted_entries = list(filter(is_unique, converted_entries))

    serializer = CreateTransactionLogSerializer(data=converted_entries, many=True)
    if serializer.is_valid():
        serializer.save()

        return JsonResponse(
            data={'new_entries': serializer.data},
            status=status.HTTP_201_CREATED,
        )

    return JsonResponse(
        data={},
        status=status.HTTP_400_BAD_REQUEST,
    )


class TransactionsListView(ListAPIView):
    queryset = TransactionLog.objects.all()
    serializer_class = TransactionLogSerializer


class TransactionDetailView(RetrieveUpdateAPIView):
    queryset = TransactionLog.objects.all()
    serializer_class = TransactionLogSerializer


class TransactionCategoryListCreateView(ListCreateAPIView):
    queryset = TransactionCategory.objects.all().order_by('-created')
    serializer_class = TransactionCategorySerializer
    page_size = 1000


class TransactionCategoryMatcherListCreateView(ListCreateAPIView):
    queryset = TransactionCategoryMatcher.objects.all().order_by('-created')
    serializer_class = TransactionCategoryMatcherSerializer
    page_size = 1000


class TransactionsMergeCreateView(CreateAPIView):
    queryset = TransactionLogMerge.objects.all()
    serializer_class = TransactionLogMergeSerializer


@require_POST
@csrf_exempt
def rematch_categories(request, *args, **kwargs):
    TransactionLog.objects.update(category=None)


    for matcher in TransactionCategoryMatcher.objects.all():
        queryset = TransactionLog.objects.annotate(search_field=Concat('date', Value(' '), 'description', output_field=CharField()))
        queryset.filter(search_field__iregex=matcher.regex_expression).update(category=matcher.category)

    return JsonResponse(
        data={},
        status=status.HTTP_200_OK,
    )


class TransactionCategoryStatsView(APIView):
    def get(self, request):
        qs = TransactionLog.objects.all()

        count_summary = [{'categoryName': count[0], 'totalCount': count[1]} for count in Counter(list(qs.values_list('category__name', flat=True))).items()]

        return Response(count_summary)


class TransactionLogRegexMatchListView(ListAPIView):
    serializer_class = TransactionLogSerializer
    # todo add limited serializer for better performance

    def get_queryset(self):
        regex_expression = self.request.query_params.get('regex_expression')

        qs = TransactionLog.objects.all().annotate(
            search_field=Concat('date', Value(' '), 'description', output_field=CharField())
        )
        return qs.filter(search_field__iregex=regex_expression)


class TransactionsCSVExportView(View):
    serializer_class = TransactionLogExportSerializer

    def get_serializer(self, queryset, many=True):
        return self.serializer_class(
            queryset,
            many=many,
        )

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'

        serializer = self.get_serializer(
            TransactionLog.objects.all(),
            many=True
        )
        header = TransactionLogExportSerializer.Meta.fields

        writer = csv.DictWriter(response, fieldnames=header)
        writer.writeheader()
        for row in serializer.data:
            writer.writerow(row)

        return response

# def transactions_export(request):
#     # Create the HttpResponse object with the appropriate CSV header.
#     response = HttpResponse(
#         content_type="text/csv",
#         headers={"Content-Disposition": 'attachment; filename="somefilename.csv"'},
#     )
#
#     writer = csv.writer(response)
#     writer.writerow(["First row", "Foo", "Bar", "Baz"])
#     writer.writerow(["Second row", "A", "B", "C", '"Testing"', "Here's a quote"])
#
#     return response
