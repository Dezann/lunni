from io import BytesIO
from typing import TypedDict, List

import pandas as pd


class Entry(TypedDict):
    date: str
    description: str
    account: str
    amount: int


def file_to_entries(file: BytesIO) -> List[Entry]:
    df = pd.read_csv(file, skiprows=25, sep=';', index_col=False, encoding='utf8')

    # take only necessary rows
    df = df.iloc[:, :5]

    # rename headers
    df = df.rename(
        columns={
            '#Data operacji': 'Date',
            '#Opis operacji': 'Description',
            '#Rachunek': 'Account',
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

    df['Description'] = df['Description'].apply(
        lambda description:
        " ".join(description.split())
    ).astype(str)

    df = df.drop_duplicates()

    renamed_entries = df.rename(
        columns={
            'Date': 'date',
            'Description': 'description',
            'Account': 'account',
            'Amount': 'amount',
        }
    ).to_dict('records')

    return renamed_entries


def pko_file_to_entries(file: BytesIO) -> List[Entry]:
    df = pd.read_csv(file, sep=',', index_col=False, encoding='cp852')

    # rename headers
    df = df.rename(
        columns={
            'Data operacji': 'Date',
            'Kwota': 'Amount',
        }
    )

    # next-to-last column contains real transfer title, but sometimes it's missing
    # falls back to 'Opis transakcji', which typically stores sender's account number but it's better than nothing
    col = df.columns[-2]
    df['Description'] = df[col].fillna(df['Opis transakcji'])

    # add header for compatibility with Entry type
    df["Account"] = "PKO"

    # e.g. +20.10 -> 20.10, -10.00 -> -10
    # todo improve performance
    df['Amount'] = df['Amount'].apply(
        lambda amount:
        amount * 100
    ).astype(int)

    df['Description'] = df['Description'].apply(
        lambda description:
        " ".join(description.split())
    ).astype(str)

    df = df.drop_duplicates()

    renamed_entries = df.rename(
        columns={
            'Date': 'date',
            'Description': 'description',
            'Account': 'account',
            'Amount': 'amount',
        }
    ).to_dict('records')

    return renamed_entries
