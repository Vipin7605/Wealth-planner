import pytest
from backend.expenses import categorize,parse_expenses
def test_category_suggestions_are_reviewable():
    assert categorize('Broadband recharge')['category']=='Utilities'
    assert categorize('unknown payment')['needs_review']
    assert categorize('rent and groceries')['category']=='Other'
def test_csv_parses_quoted_names_and_preserves_zero():
    records=parse_expenses('name,amount,category,essential\n"Rent, maintenance",0,Housing,true\nCinema,100,,false')
    assert records[0]['amount']==0
    assert records[1]['category']=='Entertainment'
    assert records[1]['essential'] is False
@pytest.mark.parametrize('text',['name,amount\nBad,-1','name,amount\nBad,nan','foo,bar\n1,2','name,amount,essential\nBad,1,maybe'])
def test_invalid_csv_rejected(text):
    with pytest.raises(ValueError):parse_expenses(text)


@pytest.mark.parametrize('text,expected', [
    ('Parents support', 'Other'),        # "rent" inside "parents"
    ('Current account fee', 'Other'),    # "rent" inside "current"
    ('Business lunch', 'Other'),         # "bus" inside "business"
    ('Facebook ads', 'Other'),           # "book" is not a keyword, "books" must not match "facebook"
    ('Monthly rent', 'Housing'),
    ('House rents', 'Housing'),          # plural still matches
    ('Metro bus pass', 'Travel'),
    ('Online course fee', 'Education'),
    ('Training program', 'Other'),       # "train" inside "training"
    ('Train ticket', 'Travel'),
])
def test_categorizer_matches_whole_words_only(text, expected):
    assert categorize(text)['category'] == expected


def test_csv_accepts_real_world_exports():
    text = 'Description;Amount (INR)\nRent;"₹ 18,000"\nGroceries;Rs. 9,000.50\n'
    items = parse_expenses(text)
    assert [(i['name'], i['amount'], i['category']) for i in items] == [('Rent', 18000, 'Housing'), ('Groceries', 9000.5, 'Food')]
    assert parse_expenses('NAME,Amount\nRent,1,20,000\n'.replace('1,20,000', '"1,20,000"'))[0]['amount'] == 120000
    assert len(parse_expenses('name,amount\nA,1\n\n,,\nB,2\n')) == 2   # blank lines ignored


@pytest.mark.parametrize('text', ['name,amount\nA,', 'name,amount\nA,abc', 'name,amount\nA,1e999', 'name\nA'])
def test_more_invalid_csvs_rejected(text):
    with pytest.raises(ValueError):
        parse_expenses(text)
