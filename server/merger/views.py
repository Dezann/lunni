import json

import pandas as pd
from django.core.exceptions import BadRequest
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import ListView
from rest_framework import status
from rest_framework.generics import ListAPIView

from merger.models import TransactionLog
from merger.serializers import TransactionLogSerializer, TransactionLogMergeSerializer, CreateTransactionLogSerializer


@require_POST
@csrf_exempt
def upload(request, *args, **kwargs):
    in_memory_file = request.FILES.get('file')
    bytes_io = in_memory_file.file
    df = pd.read_csv(bytes_io, skiprows=25, sep=';', index_col=False,)

    # take only necessary rows
    df = df.iloc[:, :5]

    # rename headers
    df = df.rename(
        columns={
            '#Data operacji': 'Date',
            '#Opis operacji': 'Description',
            '#Rachunek': 'Account',
            '#Kategoria': 'Category',
            '#Kwota': 'Amount',
        }
    )

    # parse 'Amount' column
    # e.g. 7 921,39 PLN -> 7921.39
    # todo improve performance
    df['Amount'] = df['Amount'].apply(
        lambda amount:
        amount.replace("PLN", "")
        .replace(",", "")
        .replace(" ", "")
    ).astype(int)

    converted_entries = df.rename(
        columns={
            'Date': 'date',
            'Description': 'description',
            'Account': 'account',
            'Category': 'category',
            'Amount': 'amount',
        }
    ).to_dict('records')

    serializer = CreateTransactionLogSerializer(data=converted_entries, many=True)
    serializer.is_valid()
    serializer.save() # fails...

    response_data = {
        'loaded_rows': serializer.data
    }

    return JsonResponse(
        response_data,
        status=status.HTTP_201_CREATED,
    )


class TransactionsListView(ListAPIView):
    queryset = TransactionLog.objects.all()
    serializer_class = TransactionLogSerializer


@require_POST
@csrf_exempt
def merge(request, *args, **kwargs):
    body = json.loads(request.body.decode('utf-8'))

    serializer = TransactionLogMergeSerializer(data=body)
    serializer.is_valid()

    from_transaction_serialized = TransactionLogSerializer(
        serializer.validated_data.get('from_transaction')
    )

    attempted_amount_transfer = serializer.validated_data.get('amount')
    available_amount = from_transaction_serialized.data.get('amount')

    if attempted_amount_transfer > available_amount:
        raise BadRequest('Cannot transfer from transaction more than the available transaction value')

    serializer.save()

    response_data = {
        'transaction_merge': serializer.data
    }

    return JsonResponse(
        response_data,
        status=status.HTTP_201_CREATED,
    )
