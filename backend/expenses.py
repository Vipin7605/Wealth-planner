"""Transparent category suggestions, with explicit user correction."""
import csv, io, re, uuid
from .schemas import Expense

KEYWORDS = {
    'Housing': ['rent', 'housing', 'maintenance', 'accommodation'],
    'Insurance': ['insurance', 'premium', 'term cover'],
    'Healthcare': ['hospital', 'clinic', 'medicine', 'pharmacy', 'doctor'],
    'Education': ['tuition', 'course', 'school', 'college', 'books', 'education'],
    'Utilities': ['electricity', 'broadband', 'internet', 'water bill', 'mobile bill', 'recharge'],
    'Travel': ['fuel', 'petrol', 'diesel', 'uber', 'bus', 'train', 'flight', 'commute', 'transport'],
    'Food': ['groceries', 'grocery', 'meals', 'restaurant', 'food', 'swiggy', 'zomato'],
    'Entertainment': ['cinema', 'netflix', 'streaming', 'movie', 'entertainment'],
    'Shopping': ['shopping', 'clothing', 'clothes', 'apparel', 'household purchases']}
# Whole-word matching (optional plural "s"): "rent" must not match "parents" or "current",
# and "bus" must not match "business".
PATTERNS = {category: re.compile(r'\b(?:' + '|'.join(re.escape(w) for w in words) + r')s?\b')
            for category, words in KEYWORDS.items()}
NAME_HEADERS = {'name', 'description', 'item', 'expense', 'narration', 'merchant'}
AMOUNT_HEADERS = {'amount', 'monthly amount', 'monthly_amount', 'amount_inr', 'amount (inr)', 'inr'}
CURRENCY_NOISE = re.compile(r'[₹,\s]|\brs\.?|\binr\b', re.IGNORECASE)


def categorize(text):
    lowered = text.lower()
    matches = [category for category, pattern in PATTERNS.items() if pattern.search(lowered)]
    return {'category': matches[0] if len(matches) == 1 else 'Other', 'method': 'keyword_rules',
            'needs_review': len(matches) != 1, 'note': 'Rule-based suggestion. Review before saving.'}


def parse_amount(raw):
    """Accept '1200', '1,20,000', '₹ 4,500.50' and 'Rs. 900'; reject anything else."""
    cleaned = CURRENCY_NOISE.sub('', raw or '')
    if not cleaned:
        raise ValueError('amount is empty')
    return float(cleaned)


def _sniff(text):
    try:
        return csv.Sniffer().sniff(text[:2000].split('\n', 1)[0], delimiters=',;\t').delimiter
    except csv.Error:
        return ','


def parse_expenses(text):
    text = text.lstrip('\ufeff')
    reader = csv.reader(io.StringIO(text), delimiter=_sniff(text))
    rows = list(reader)
    if not rows:
        raise ValueError('CSV contains no records')
    header = [h.strip().lower() for h in rows[0]]
    name_col = next((i for i, h in enumerate(header) if h in NAME_HEADERS), None)
    amount_col = next((i for i, h in enumerate(header) if h in AMOUNT_HEADERS), None)
    if name_col is None or amount_col is None:
        raise ValueError('CSV needs name and amount columns. Amount must be a monthly total.')
    column = {h: i for i, h in enumerate(header)}
    items = []
    for line, row in enumerate(rows[1:], 2):
        if not any(cell.strip() for cell in row):
            continue  # ignore blank lines
        if len(items) >= 200:
            raise ValueError('Maximum 200 expense rows per import')
        try:
            get = lambda key: row[column[key]].strip() if key in column and column[key] < len(row) else ''
            name = row[name_col].strip()
            amount = parse_amount(row[amount_col] if amount_col < len(row) else '')
            category = get('category') or categorize(name)['category']
            essential_text = get('essential').lower()
            if essential_text not in {'', 'true', 'false', '1', '0', 'yes', 'no'}:
                raise ValueError('essential must be true or false')
            essential = (essential_text in {'true', '1', 'yes'}) if essential_text else category not in {'Shopping', 'Entertainment', 'Other'}
            items.append(Expense(id=uuid.uuid4().hex, name=name, amount=amount, category=category, essential=essential).model_dump())
        except Exception as exc:
            raise ValueError(f'Invalid CSV row {line}: {exc}') from exc
    if not items:
        raise ValueError('CSV contains no records')
    return items
