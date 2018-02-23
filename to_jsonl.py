import json
import ijson
from ijson import common
import decimal
from ijson.backends import yajl2

def floaten(event):
    if event[1] == 'number':
        return (event[0], event[1], float(event[2]))
    else:
        return event

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

with open('data/declarations.jsonl', 'w') as out:
    with open('data/declarations.json') as fd:
        for item in ijson.items(file=fd, prefix='item'):
            text = json.dumps(item, ensure_ascii=False, cls=DecimalEncoder)
            out.write(text)
            out.write('\n')
