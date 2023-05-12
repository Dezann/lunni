import datetime
from io import StringIO, BytesIO

from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.utils import json

from merger.factories import TransactionLogFactory, TransactionCategoryFactory, TransactionCategoryMatcherFactory


class MergerTestCase(APITestCase):
    def test_upload_mbank_file(self):
        url = reverse('merger-upload')

        operations_file = """mBank S.A. Bankowość Detaliczna;
Skrytka Pocztowa 2108;
90-959 Łódź 2;
www.mBank.pl;
mLinia: 801 300 800;
+48 (42) 6 300 800;


#Klient;
ŁUKASZ BLACHNICKI;

Lista operacji;

#Za okres:;
XXXXXXX;

#zgodnie z wybranymi filtrami wyszukiwania;
#dla rachunków:;
Prywatne - XXXX;

#Lista nie jest dokumentem w rozumieniu art. 7 Ustawy Prawo Bankowe (Dz. U. Nr 140 z 1997 roku, poz.939 z późniejszymi zmianami), ponieważ operacje można samodzielnie edytować.;

#Waluta;#Wpływy;#Wydatki;
PLN;XXXXXXXXXX

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;
2023-02-11;"Zwrot za Maka";"Prywatne";"Wpływy";15,80 PLN;;
2023-02-10;"Stacja Grawitacja Cz-wa  ZAKUP PRZY UŻYCIU KARTY W KRAJU                                                     transakcja nierozliczona";"Prywatne";"Jedzenie poza domem";-31,60 PLN;;
        """
        sio = StringIO(operations_file)
        bio = BytesIO(sio.read().encode('utf8'))

        response = self.client.post(
            path=url,
            data=encode_multipart(
                data=dict(file=bio, variant='mbank'),
                boundary=BOUNDARY,
            ),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_content = response.json()['new_entries']
        self.assertEqual(response_content, 2)

    def test_upload_mbank_savings_file(self):
        url = reverse('merger-upload')

        operations_file = """mBank S.A. Bankowość Detaliczna;
Skrytka Pocztowa 2108;
90-959 Łódź 2;
www.mBank.pl;
mLinia: 801 300 800;
+48 (42) 6 300 800;
    

#Klient;
ŁUKASZ BLACHNICKI;

Elektroniczne zestawienie operacji;

#Za okres:;
asdasd
#Rodzaj rachunku;
asdasd
#Waluta;
asdasd
#Numer rachunku;
asdasd
#Data następnej kapitalizacji;
asdasd
#Oprocentowanie rachunku;
asdasd
#Limit kredytu;
asdasd
#Oprocentowanie kredytu;
asdasd

#Podsumowanie obrotów na rachunku;#Liczba operacji;#Wartość operacji
asdasd
asdasd
asdasd

asdasd

#Data księgowania;#Data operacji;#Opis operacji;#Tytuł;#Nadawca/Odbiorca;#Numer konta;#Kwota;#Saldo po operacji;
2023-01-01;2023-01-01;PRZELEW NA TWOJE CELE;"";"CEL  ";'';0,01;0,01;
2023-02-11;2023-02-11;WPŁATA NA CEL;"CEL OPŁATY";"  ";'';12 345,00;12 345,67;
        """
        sio = StringIO(operations_file)
        bio = BytesIO(sio.read().encode('cp1250'))

        response = self.client.post(
            path=url,
            data=encode_multipart(
                data=dict(file=bio, variant='mbank-savings'),
                boundary=BOUNDARY,
            ),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_content = response.json()['new_entries']
        self.assertEqual(response_content, 2)

    def test_prevent_csv_duplicates(self):
        url = reverse('merger-upload')

        operations_file = """mBank S.A. Bankowość Detaliczna;
Skrytka Pocztowa 2108;
90-959 Łódź 2;
www.mBank.pl;
mLinia: 801 300 800;
+48 (42) 6 300 800;


#Klient;
ŁUKASZ BLACHNICKI;

Lista operacji;

#Za okres:;
XXXXXXX;

#zgodnie z wybranymi filtrami wyszukiwania;
#dla rachunków:;
Prywatne - XXXX;

#Lista nie jest dokumentem w rozumieniu art. 7 Ustawy Prawo Bankowe (Dz. U. Nr 140 z 1997 roku, poz.939 z późniejszymi zmianami), ponieważ operacje można samodzielnie edytować.;

#Waluta;#Wpływy;#Wydatki;
PLN;XXXXXXXXXX

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;
2023-02-11;"Zwrot za Maka";"Prywatne";"Wpływy";15,80 PLN;;
2023-02-10;"Stacja Grawitacja Cz-wa  ZAKUP PRZY UŻYCIU KARTY W KRAJU                                                     transakcja nierozliczona";"Prywatne";"Jedzenie poza domem";-31,60 PLN;;
2023-02-10;"Stacja Grawitacja Cz-wa  ZAKUP PRZY UŻYCIU KARTY W KRAJU                                                     transakcja nierozliczona";"Prywatne";"Jedzenie poza domem";-31,60 PLN;;
        """
        sio = StringIO(operations_file)
        bio = BytesIO(sio.read().encode('utf8'))

        response = self.client.post(
            path=url,
            data=encode_multipart(
                data=dict(file=bio, variant='mbank'),
                boundary=BOUNDARY,
            ),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_content = response.json()['new_entries']
        self.assertEqual(response_content, 2)

        sio = StringIO(operations_file)
        bio = BytesIO(sio.read().encode('utf8'))

        response = self.client.post(
            path=url,
            data=encode_multipart(
                data=dict(file=bio, variant='mbank'),
                boundary=BOUNDARY,
            ),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_content = response.json()['new_entries']
        self.assertEqual(response_content, 0)

    def test_prevent_database_duplicates(self):
        category = TransactionCategoryFactory.create()
        TransactionLogFactory(date='2023-01-05', description='desc', account='prywatnte', amount=1, category=category)

        url = reverse('merger-upload')

        operations_file = """mBank S.A. Bankowość Detaliczna;
Skrytka Pocztowa 2108;
90-959 Łódź 2;
www.mBank.pl;
mLinia: 801 300 800;
+48 (42) 6 300 800;


#Klient;
ŁUKASZ BLACHNICKI;

Lista operacji;

#Za okres:;
XXXXXXX;

#zgodnie z wybranymi filtrami wyszukiwania;
#dla rachunków:;
Prywatne - XXXX;

#Lista nie jest dokumentem w rozumieniu art. 7 Ustawy Prawo Bankowe (Dz. U. Nr 140 z 1997 roku, poz.939 z późniejszymi zmianami), ponieważ operacje można samodzielnie edytować.;

#Waluta;#Wpływy;#Wydatki;
PLN;XXXXXXXXXX

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;
2023-01-05;"desc";"prywatnte";"food";0,01 PLN;;
        """
        sio = StringIO(operations_file)
        bio = BytesIO(sio.read().encode('utf8'))

        response = self.client.post(
            path=url,
            data=encode_multipart(
                data=dict(file=bio, variant='mbank'),
                boundary=BOUNDARY,
            ),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_content = response.json()['new_entries']
        self.assertEqual(response_content, 0)


    def test_upload_pko_file(self):
        url = reverse('merger-upload')

        operations_file = """
"Data operacji","Data waluty","Typ transakcji","Kwota","Waluta","Saldo po transakcji","Opis transakcji","","","",""
"2023-05-08","2023-05-08","Przelew na rachunek","+20.70","PLN","+23.99","Costam","Nazwa nadawcy: BIURO","Adres nadawcyxxxx","",""
"2023-05-08","2023-05-08","Przelew na rachunek","+20.70","PLN","+23.99","Rachunek nadawcy: XXXX","Nazwa nadawcy: BIURO","Adres nadawcyxxxx","Tytul: sddsd",""
        """
        sio = StringIO(operations_file)
        bio = BytesIO(sio.read().encode('cp1250'))

        response = self.client.post(
            path=url,
            data=encode_multipart(
                data=dict(file=bio, variant='pko'),
                boundary=BOUNDARY,
            ),
            content_type=MULTIPART_CONTENT,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_content = response.json()['new_entries']
        self.assertEqual(response_content, 2)

    def test_get_transactions(self):
        category = TransactionCategoryFactory.create()
        TransactionLogFactory.create(id=1, amount=300, category=category)
        TransactionLogFactory.create(id=2, amount=-50, category=category)

        url = reverse('merger-transactions')

        response = self.client.get(path=url)

        response_json = response.json()

        self.assertEqual(response_json['count'], 2)
        self.assertEqual(response_json['total_pages'], 1)

        first_result = response_json['results'][0]
        self.assertEqual(first_result['id'], 2)
        self.assertEqual(first_result['amount'], -50)
        self.assertEqual(first_result['calculated_amount'], -50)
        self.assertEqual(first_result['date'], '2023-01-05')
        self.assertEqual(first_result['description'], 'desc')
        self.assertEqual(first_result['account'], 'prywatnte')
        self.assertEqual(first_result['category']['id'], 1)
        self.assertEqual(first_result['category']['name'], 'food')
        self.assertEqual(first_result['category']['variant'], 'NEG')

        second_result = response_json['results'][1]
        self.assertEqual(second_result['id'], 1)
        self.assertEqual(second_result['amount'], 300)
        self.assertEqual(second_result['calculated_amount'], 300)
        self.assertEqual(second_result['date'], '2023-01-05')
        self.assertEqual(second_result['description'], 'desc')
        self.assertEqual(second_result['account'], 'prywatnte')
        self.assertEqual(second_result['category']['id'], 1)
        self.assertEqual(second_result['category']['name'], 'food')
        self.assertEqual(second_result['category']['variant'], 'NEG')

    def test_merge_transactions(self):
        category = TransactionCategoryFactory.create()
        TransactionLogFactory(id=1, amount=300, category=category)
        TransactionLogFactory(id=2, amount=-50, category=category)
        TransactionLogFactory(id=3, amount=100, category=category)
        TransactionLogFactory(id=4, amount=-100, category=category)

        url = reverse('merger-merge')

        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    'from_transaction': 1,
                    'to_transaction': 2,
                    'amount': 49
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    'from_transaction': 3,
                    'to_transaction': 4,
                    'amount': 100
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('merger-transactions')

        response_json = self.client.get(path=url).json()

        self.assertEqual(response_json['count'], 2)
        self.assertEqual(response_json['total_pages'], 1)
        self.assertEqual(response_json['results'][0]['id'], 2)
        self.assertEqual(response_json['results'][0]['calculated_amount'], -1)
        self.assertEqual(response_json['results'][1]['id'], 1)
        self.assertEqual(response_json['results'][1]['calculated_amount'], 251)

    def test_merge_transactions_prevent_negative_amount(self):
        category = TransactionCategoryFactory.create()
        TransactionLogFactory(id=1, amount=300, category=category)
        TransactionLogFactory(id=2, amount=-50, category=category)

        url = reverse('merger-merge')

        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    'from_transaction': 1,
                    'to_transaction': 2,
                    'amount': -50
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merge_transactions_prevent_overdraw(self):
        category = TransactionCategoryFactory.create()
        TransactionLogFactory(id=1, amount=300, category=category)
        TransactionLogFactory(id=2, amount=-50, category=category)

        url = reverse('merger-merge')

        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    'from_transaction': 1,
                    'to_transaction': 2,
                    'amount': 350
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merge_transactions_prevent_negative_overdraw(self):
        category = TransactionCategoryFactory.create()
        TransactionLogFactory(id=1, amount=300, category=category)
        TransactionLogFactory(id=2, amount=-50, category=category)

        url = reverse('merger-merge')

        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    'from_transaction': 2,
                    'to_transaction': 1,
                    'amount': -30
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_merge_multiple_transactions(self):
        category = TransactionCategoryFactory.create()
        TransactionLogFactory(id=1, amount=-75, category=category)
        TransactionLogFactory(id=2, amount=50, category=category)
        TransactionLogFactory(id=3, amount=25, category=category)

        url = reverse('merger-merge')

        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    'from_transaction': 2,
                    'to_transaction': 1,
                    'amount': 25
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            path=url,
            data=json.dumps(
                {
                    'from_transaction': 3,
                    'to_transaction': 1,
                    'amount': 25
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('merger-transactions')

        response_json = self.client.get(path=url).json()

        self.assertEqual(response_json['count'], 2)
        self.assertEqual(response_json['total_pages'], 1)
        self.assertEqual(response_json['results'][0]['id'], 1)
        self.assertEqual(response_json['results'][0]['calculated_amount'], -25)
        self.assertEqual(response_json['results'][1]['id'], 2)
        self.assertEqual(response_json['results'][1]['calculated_amount'], 25)

    def test_rematch_categories(self):
        TransactionLogFactory(
            id=1,
            amount=300,
            description='gift',
            category=None
        )
        TransactionLogFactory(
            id=2,
            amount=-50,
            description='spotify payment',
            category=None
        )
        subscriptionsCategory = TransactionCategoryFactory(
            id=1,
            name='subscriptions',
            variant='NEG'
        )
        TransactionCategoryMatcherFactory(
            id=1,
            regex_expression='spotify',
            category=subscriptionsCategory
        )

        url = reverse('rematch-categories')

        response = self.client.post(
            path=url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('merger-transactions')

        response = self.client.get(
            path=url,
        )

        response_content = response.json()
        self.assertEqual(response_content['count'], 2)
        self.assertEqual(response_content['total_pages'], 1)

        results = response_content['results']
        self.assertEqual(len(results), 2)

        first_result = results[0]
        self.assertEqual(first_result['id'], 2)
        self.assertEqual(first_result['date'], '2023-01-05')
        self.assertEqual(first_result['description'], 'spotify payment')
        self.assertEqual(first_result['account'], 'prywatnte')
        self.assertEqual(first_result['category'], {'id': 1, 'name': 'subscriptions', 'variant': 'NEG'})
        self.assertEqual(first_result['amount'], -50)
        self.assertEqual(first_result['calculated_amount'], -50)

        second_result = results[1]
        self.assertEqual(second_result['id'], 1)
        self.assertEqual(second_result['date'], '2023-01-05')
        self.assertEqual(second_result['description'], 'gift')
        self.assertEqual(second_result['account'], 'prywatnte')
        self.assertIsNone(second_result['category'])
        self.assertEqual(second_result['amount'], 300)
        self.assertEqual(second_result['calculated_amount'], 300)

    def test_editing_single_transaction(self):
        TransactionLogFactory(id=1, amount=300)

        url = reverse('merger-transaction-details', kwargs={'pk': 1})

        response = self.client.get(
            path=url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()

        self.assertEqual(response_json['note'], '')

        response = self.client.patch(
            path=url,
            data=json.dumps(
                {
                    'note': 'my note',
                }
            ),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()

        self.assertEqual(response_json['note'], 'my note')

    def test_export_transactions(self):
        category = TransactionCategoryFactory(
            id=1,
            name='subscriptions',
            variant='NEG'
        )

        TransactionLogFactory(
            id=1,
            amount=300,
            description='gift',
            date=datetime.date(2018, 5, 1),
            category=category
        )
        TransactionLogFactory(
            id=2,
            amount=-50,
            description='spotify payment',
            date=datetime.date(2018, 5, 6),
            category=None
        )

        url = reverse('transactions-export')

        response = self.client.get(path=url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_content = response.content.decode('utf-8')
        csv_lines = [line for line in response_content.split('\r\n') if line != '']
        header = csv_lines.pop(0)

        self.assertEqual(header, 'id,date,description,note,account,category_name,amount,calculated_amount')
        self.assertEqual(len(csv_lines), 2)
        self.assertEqual(csv_lines[0], '2,2018-05-06,spotify payment,,prywatnte,,-50,-50')
        self.assertEqual(csv_lines[1], '1,2018-05-01,gift,,prywatnte,subscriptions,300,300')
