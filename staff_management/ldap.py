from subprocess import PIPE
from subprocess import Popen
from sys import exit
from sys import stderr

class LDAP():
    '''Does what we need and no more. Not an LDAP API.
    '''
    def __init__(self, host, oc):
        self.oc = oc
        self.host = host

    def netid(self, employee_id):
        try:
            return self._query(employee_id, 'universityid')['uid']
        except TypeError as te:
            print(str(te), file=stderr)
            print("If you're off campus, are you connected to VPN?", file=stderr)
            exit(68)

    def _query(self, field, val):
        # Shell out to ldapsearch and get back a dict of values
        query = self._build_query(field, val)
        proc = Popen(query, stderr=PIPE, stdout=PIPE)
        stdout, stderr = proc.communicate()
        return LDAP._format_response(stdout)

    def _build_query(self, val, field='uid'):
        # fields: universityid, uid (net id), mail
        filter = f'{field}={val}'
        # if field == 'mail':
        #     filter = f'{filter}@princeton.edu'
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
        if 'uid' not in d: # shortcut; could lead to errors
            return None
        else:
            return d
