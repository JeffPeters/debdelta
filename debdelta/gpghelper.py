#!/usr/bin/python3

# https://docs.red-dove.com/python-gnupg/index.html

import os, sys, datetime, time, logging

__doc__ = """Usage %s [GNUPGHOME] [COMMAND] [YEAR]

 COMMAND may be `test` or `create`
 
 test : tests some routines
 
 list: list public keys
 
 list-sec: list secret keys
 
 create : create a key for current year, or given year
""" % sys.argv[0]


logger = logging.getLogger(__name__)

#gpg.encoding = 'utf-8'

try:
    import gnupg
except ImportError:
    logger.error('Please install "python3-gnupg"')
    gnupg = None
    if __name__ == '__main__':
        sys.exit(1)

def key_can_sign(S, now):
    if 's' in S['cap']:
        e = S['expires']
        if e:
            e = float(e)
            return e > now
        else:
            return True
    else:
        return False


def select_secret_key_by_date(gnupghome ,now):
    " select the oldest secret key that can sign and that has not expired as of `now` "
    gpg = gnupg.GPG(gnupghome=gnupghome)
    private_keys = gpg.list_keys(secret = True)
    usable_keys = []
    for P in private_keys:
        d = float(P['date'])
        if key_can_sign(P, now):
            usable_keys.append(  (d,P) )
    usable_keys.sort()
    if usable_keys:
        return usable_keys[0][1]['keyid']
    else: return None

def convert_time(j, v, now=None):
    if now is None:
        now = time.time()
    if j in ('expires','date'):
        if not v:
            v = 'NO DATE'
        elif 'T' not in v:
            f = float(v)
            v = time.ctime(f)
            if f < now and j == 'expires':
                v += '  ** EXPIRED **'
        else:
            logger.error('date format %r = %r unsupported',j,v)
    return v

def list_keys(gnupghome, secret=False):
    now = time.time()
    gpg = gnupg.GPG(gnupghome=gnupghome)
    private_keys = gpg.list_keys(secret = secret)
    for P in private_keys:
        print()
        print('KEY %r CAN_SIGN %r' % (P['keyid'] , key_can_sign(P, now) ) )
        for k in P:
            if k not in ('subkeys','subkey_info'):
                v = convert_time(k, P[k])
                print(' %r = %r'% (k, v))
        SI = P.get('subkey_info',{})
        for k in SI:
            S = SI[k]
            print(' SUBKEY %r CAN_SIGN %r' % (S['keyid'] , key_can_sign(S, now) ) )
            for j in S:
                v = convert_time(j, S[j])
                print('    %r = %r'% (j,v))

def find_secret_key_by_year(gnupghome , year):
    " select the oldest secret key that can sign and that has not expired as of `now` "
    gpg = gnupg.GPG(gnupghome=gnupghome)
    private_keys = gpg.list_keys(secret = True)
    name =  'Debian deltas automatic signing key (%s)' % year
    for P in private_keys:
        if any( [ u.startswith(name) for u in P['uids'] ]  ):
            return P['keyid']



def create_key(gnupghome, year = None):
    # all good and nice, but it pretends user interaction to enter the password
    # even though docs say that this may disable the need for user interaction
    f = os.path.join(gnupghome,'gpg-agent.conf')
    if not os.path.isfile(f) or 'allow-loopback-pinentry' not in open(f).read():
        logger.warning('Appending allow-loopback-pinentry to gpg-agent.conf')
        open(f,'a').write('allow-loopback-pinentry\n')

    if year is None:
        year = datetime.datetime.now().year
    
    key = find_secret_key_by_year(gnupghome , year)
    if key is not None:
        #print('already exists')
        return key
    #
    expire_date = str(year + 5) + '-12-31'
    #expiration = int(time.mktime(  datetime.date(year + 5,12,31).timetuple() ))
    #
    gpg = gnupg.GPG(gnupghome=gnupghome)
    input_data = gpg.gen_key_input(key_type="RSA", key_length=4096,
                                   name_real =  'Debian deltas automatic signing key (%s)' % year,
                                   name_email = 'debdelta_%s@debdelta.debian.net' % year,
                                   name_comment = '',
                                   expire_date = expire_date,
                                   passphrase = '',
                                   )
    #
    #print(input_data)
    #
    key = gpg.gen_key(input_data)
    if  key.fingerprint is None:
        logger.error('failed : %r', key.stderr)
        return None
    #
    return key.fingerprint
    
    #ascii_armored_public_keys = gpg.export_keys([key.fingerprint])
    #print(ascii_armored_public_keys)




#gnupghome='/home/debdev/debdelta/debdelta-suite/gpg_tmp'
#gnupghome='/home/debdev/debdelta/gnupg~~'

if __name__ == '__main__':
    argv = sys.argv[1:]
    if len(argv) < 1:
        print(__doc__)
        sys.exit(0)
    
    gnupghome = argv[0]
    if not os.path.isdir(gnupghome):
        logger.error('Directory  does not exist : %r', gnupghome)
        sys.exit(1)
    
    argv = argv[1:]
    
    year = datetime.datetime.now().year
    
    if argv and argv[0] == 'test':
        print('Key created in 2017')
        print( find_secret_key_by_year(gnupghome , 2017))
        print('Usable key')
        print( select_secret_key_by_date(gnupghome , time.time() + (60 * 24 * 3600) ) )
    
    if argv and argv[0] == 'list':
        list_keys(gnupghome)
    
    if argv and argv[0] == 'list-sec':
        list_keys(gnupghome, secret=True)
        
    if argv and argv[0] == 'create':
        if len(argv)>1:
            year = int(argv[1])
        print("Key for this year is %r" % create_key(gnupghome, year))
