from venture import shortcuts
ripl = shortcuts.make_church_prime_ripl()

from library import Library
lib = Library(ripl)

text = """Pseudo random number generators take a random seed and generate a longer sequenc
e of seemingly random bits. Randomness plays a crucial role in cryptography, as 
it is used to generate the secret keys for cryptographic algorithms. For example
, one time pads are random sequences of bits and trapdoor functions are chosen a
t random.  Due to the role of randomness in cryptography, the generation of pseu
do-random numbers is an important subject."""

#text = "a b a b"

text = text.replace('\n', '')
text = text.replace('.', ' . ')
text = text.split()

#text = text[:40]

def encode(tokens):
    count = [0]
    token2count = {}
    count2token = {}
    
    def get_count(token):
        if token not in token2count:
            token2count[token] = count[0]
            count2token[count[0]] = token
            count[0] += 1
        return token2count[token]
    
    sequence = map(get_count, tokens)
    
    return sequence, token2count, count2token

sequence, token2count, count2token = encode(text)

lib.load('sm')
ripl.assume('uniform', "(lambda (i) 1)")
ripl.assume('sm', '(make_sm uniform %d)' % len(token2count))
ripl.assume('prefix0', "(list)")

for i, s in enumerate(sequence):
    lib.observe_sm('sm', 'prefix%d' % i, s)
    ripl.assume('prefix%d' % (i+1), "(pair %d prefix%d)" % (s, i))

def parse_seq(seq):
    return [count2token[int(v['value'])] for v in seq]

def gen_seq(n):
    return parse_seq(ripl.predict('(sm_gen_seq sm prefix0 %d)' % n))

def context2list(context):
    return "(list " + ' '.join([str(token2count[t]) for t in reversed(context)]) + ")"

def get_distribution(context):
    l = context2list(context)
    weights = [(t, ripl.predict('(categorical_get_weight (sm_get_sampler sm %s) %d)' % (l, c))) for (t, c) in token2count.items()]
    return sorted(weights, key=lambda x: x[1])

