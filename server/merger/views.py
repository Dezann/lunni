import csv
from collections import Counter
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views import View
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from merger.models import TransactionLog, TransactionLogMerge, TransactionCategoryMatcher, TransactionCategory
from merger.parsers import parse_mbank_statement_file, Entry, parse_pko_statement_file, \
    parse_mbank_savings_statement_file
from merger.serializers import TransactionLogSerializer, TransactionLogMergeSerializer, TransactionCategorySerializer, \
    TransactionCategoryMatcherSerializer, TransactionLogExportSerializer


class UploadAPIView(CreateAPIView):
    function_map = {
        'mbank': parse_mbank_statement_file,
        'mbank-savings': parse_mbank_savings_statement_file,
        'pko': parse_pko_statement_file
    }

    def create(self, request, *args, **kwargs):
        variant: str = request.POST.get('variant')
        if variant not in self.function_map.keys():
            return HttpResponseBadRequest(
                f"Invalid parameter 'variant'. Allowed values are: {', '.join(self.function_map.keys())}.")

        in_memory_file: InMemoryUploadedFile = request.FILES.get('file')
        if in_memory_file is None:
            return HttpResponseBadRequest("Missing file 'file'.")

        bytes_io: BytesIO = in_memory_file.file
        extracted_entries: list[Entry] = self.function_map.get(variant)(bytes_io)

        transaction_logs_to_create = []

        for entry in extracted_entries:
            if not TransactionLog.objects.filter(
                Q(date=entry['date']) &
                Q(description=entry['description']) &
                Q(account=entry['account']) &
                Q(amount=entry['amount'])
            ).exists():
                transaction_logs_to_create.append(
                    TransactionLog(
                        date=entry['date'],
                        description=entry['description'],
                        account=entry['account'],
                        amount=entry['amount'],
                    )
                )

        TransactionLog.objects.bulk_create(transaction_logs_to_create)

        return JsonResponse(
            data={'new_entries': len(transaction_logs_to_create)},
            status=status.HTTP_201_CREATED,
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
def rematch_categories(request, *args, **kwargs):
    TransactionLog.objects.update(category=None)

    for matcher in TransactionCategoryMatcher.objects.all():
        queryset = TransactionLog.objects.annotate(
            search_field=Concat('date', Value(' '), 'description', output_field=CharField()))
        queryset.filter(search_field__iregex=matcher.regex_expression).update(category=matcher.category)

    return JsonResponse(
        data={},
        status=status.HTTP_200_OK,
    )


class TransactionCategoryStatsView(APIView):
    def get(self, request):
        qs = TransactionLog.objects.all()

        count_summary = [{'categoryName': count[0], 'totalCount': count[1]} for count in
                         Counter(list(qs.values_list('category__name', flat=True))).items()]

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
