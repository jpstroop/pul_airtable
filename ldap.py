from subprocess import PIPE
from subprocess import Popen

class LDAP_API():
    '''Does what we need and no more. Not an LDAP API.
    '''
    def __init__(self, host, oc):
        self.oc = oc
        self.host = host

    def _build_query(self, field, id):
        filter = f'{field}={id}'
        if field == 'mail':
            filter = f'{filter}@princeton.edu'
        return ['ldapsearch', '-h', self.host, '-p', '389', '-x', '-b', self.oc, filter]

    @staticmethod
    def _format_response(resp):
        d = {}
        for line in resp.decode('utf-8', errors='ignore').strip().split("\n"):
            if ':' in line:
                tokens = line.split(':')
                k = tokens[0]
                if len(tokens) == 2:
                    d[k] = tokens[1].strip()
                else:
                    d[k] = ':'.join(tokens[1:]).strip()
        if 'uid' not in d:
            return None
        else:
            return d

    def query(self, field, id):
        # Shell out to ldapsearch and get back a dict of values
        query = self._build_query(field, id)
        proc = Popen(query, stderr=PIPE, stdout=PIPE)
        stdout, stderr = proc.communicate()
        return LDAP_API._format_response(stdout)
