from flat_price import FlatPricing
from collections import abc
import numpy as np
import pandas as pd


def nested_dict_iter(nested, path):
    for key, value in nested.items():
        if isinstance(value, abc.Mapping):
            yield key, value, path
            yield from nested_dict_iter(value, path + [key])
        else:
            yield key, value, path


class PersonToFeatures:
    def __init__(self):
        self.flat_pricing = FlatPricing()

        self.skip_own_types = {
            'Безвозмездное пользование',
            'Служебное жилье',
            'Наём (аренда)',
            'Фактическое предоставление',
            'В пользовании'
        }

    @classmethod
    def get_possible_regions(cls, person):
        for main in person:
            for key, val, path in nested_dict_iter(main, []):
                if key == 'region':
                    if val:
                        yield val, path

    def estimate_item(self, item, year, possible_regions):

        item_region = item.get('region')
        if not item_region:
            item_region = possible_regions
        else:
            item_region = [item_region['name']]

        item_type = item['type']['name']
        coef, depend_on_square = self.flat_pricing.price_coef[item_type]

        mean_square = self.flat_pricing.median_sqrs.get(item_type, 1)

        if depend_on_square:
            square = item.get('square') or mean_square
        else:
            square = 1

        share = item.get('share') or 1.0

        prices = []
        for region in item_region:
            estimated_price = int(self.flat_pricing.get_price(region, year) * square * coef * share)
            prices.append(estimated_price)
        mean_price = np.mean(prices)

        return mean_price

    def estimate_all_real_estates(self, person, possible_regions):
        year = person['main']['year']

        if not possible_regions:
            possible_regions = [None]

        prop = 'real_estates'
        real_estates = person.get(prop) or []

        res = {
            prop + '_self_price': 0,
            prop + '_rel_price': 0
        }

        for item in real_estates:

            if item.get('own_type', {}).get('name') in self.skip_own_types:
                continue

            price = self.estimate_item(item, year, possible_regions)
            if not item.get('relative'):
                res[prop + '_self_price'] += price
            else:
                res[prop + '_rel_price'] += price

        return res

    def count_things(self, person, prop='real_estates'):
        res = {
            prop + '_self_count': 0,
            prop + '_rel_count': 0
        }
        items = person.get(prop) or []
        for item in items:
            if item.get('own_type', {}).get('name') in self.skip_own_types:
                continue

            if not item.get('relative'):
                res[prop + '_self_count'] += 1
            else:
                res[prop + '_rel_count'] += 1
        return res

    def count_field(self, person, prop='incomes', field='size'):
        res = {
            prop + '_self_' + field: 0,
            prop + '_rel_' + field: 0
        }
        items = person.get(prop) or []
        for item in items:
            if item.get('own_type', {}).get('name') in self.skip_own_types:
                continue

            if not item.get('relative'):
                res[prop + '_self_' + field] += item.get(field, 0) or 0
            else:
                res[prop + '_rel_' + field] += item.get(field, 0) or 0

        return res

    def get_timeline(self, person):
        possible_regions = set(map(lambda x: x[0]['name'], self.get_possible_regions(person)))
        declarations_by_year = sorted(person, key=lambda x: x['main']['year'])

        trends = []
        for declaration in declarations_by_year:
            year = declaration['main']['year']
            price = self.estimate_all_real_estates(declaration, possible_regions)
            counts_estates = self.count_things(declaration, 'real_estates')
            counts_vehicles = self.count_things(declaration, 'vehicles')
            incomes = self.count_field(declaration)

            sqrs = self.count_field(declaration, 'real_estates', 'square')

            features = {**price, **counts_estates, **counts_vehicles, **incomes, **sqrs, "year": year}

            trends.append(features)

        return trends

    def generate_timeline_features(self, person):
        timeline = self.get_timeline(person)

        timeline_features = pd.DataFrame(timeline).drop(['year'], axis=1).describe().loc[['min', 'max', 'mean', 'std']].to_dict()

        timeline_features_flatten = {}
        for key, value, path in nested_dict_iter(timeline_features, []):
            if isinstance(value, dict):
                continue
            flatten_key = "_".join(path) + "_" + key
            timeline_features_flatten[flatten_key] = value

        diffs = []
        for prev, follow in zip(timeline[:-1], timeline[1:]):
            all_keys = set(list(prev.keys()) + list(follow.keys()))
            diff = {}
            for key in all_keys:
                diff[key] = follow.get(key, 0) - prev.get(key, 0)
            diffs.append(diff)

        df_diffs = pd.DataFrame(diffs)
        timeline_diff_features = df_diffs.describe().loc[['min', 'max']].to_dict()

        timeline_diff_features_flatten = {}
        for key, value, path in nested_dict_iter(timeline_diff_features, ['diff']):
            if isinstance(value, dict):
                continue
            flatten_key = "_".join(path) + "_" + key
            timeline_diff_features_flatten[flatten_key] = value

        return {
            **timeline_features_flatten,
            **timeline_diff_features_flatten
        }
