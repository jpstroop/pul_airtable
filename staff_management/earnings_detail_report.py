from csv import DictReader

class EarningsDetailReport():
    def __init__(self, csv_pth):
        self._lookup = {}
        with open(csv_pth, 'r', encoding='utf-16') as f: # Note encoding
            self._src_data = list(DictReader(f, delimiter='\t'))
        self._populate_lookup()

    def __getitem__(self, empid):
        return self._lookup[emplid]

    def __iter__(self):
        for k in self._lookup:
            try:
                yield k
            except StopIteration:
                return

    def items(self):
        for item in self._lookup.items():
            try:
                yield item
            except StopIteration:
                return

    def _populate_lookup(self):
        for emplid in {row['Employee Id'] for row in self._src_data}: # set comprehension!
            self._lookup[emplid] = list(self._fund_codes_for_emplid(emplid))

    def _fund_codes_for_emplid(self, emplid):
        return {r['Fund Code'] for r in self._src_data if r['Employee Id'] == emplid}





















