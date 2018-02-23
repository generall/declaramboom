import Levenshtein
import pandas as pd


class FlatPricing:
    def __init__(self):
        # http://www.gks.ru/dbscripts/cbsd/dbinet.cgi?pl=1905001
        self.filled_table_int = pd.read_csv("data/flat_price.csv")
        self.region_mapping = {}

        # https://rosrealt.ru/cena
        # type: (coefficient, depend_on_square)
        self.price_coef = {
            'Квартира': (1.9, True),
            'Земельный участок': (218040 / 62044 / 100, True),
            'Жилой дом': (7813770 / 62044, False),
            'Дача': (7813770 / 62044, False),
            'Гараж': (395807 / 62044, False),
            'Иное': (0, False)
        }

        self.median_sqrs = {
            'Гараж': 21.2,
            'Дача': 73.2,
            'Жилой дом': 136.9,
            'Земельный участок': 1100.0,
            'Иное': 63.1,
            'Квартира': 63.0
        }

    def get_price(self, region, year):
        year = str(year)
        if region:
            target_region = self.region_mapping.get(region)
        else:
            target_region = 'Российская Федерация'
        if not target_region:
            target_region = sorted(self.filled_table_int.region, key=lambda x: Levenshtein.distance(region, x))[0]
            self.region_mapping[region] = target_region

        return self.filled_table_int[self.filled_table_int.region == target_region][year].mean()
