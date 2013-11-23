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

text = "a b a b"

text = text.replace('\n', '')
text = text.replace('.', ' . ')
text = text.split()

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
    for t in count2token:
        print(ripl.predict('(categorical_get_weight (sm_get_sampler sm prefix%d) %d)' % (i, t)))
    lib.observe_sm('sm', 'prefix%d' % i, s)
    ripl.assume('prefix%d' % (i+1), "(pair %d prefix%d)" % (s, i))

def gen_seq(n):
    return ripl.predict('(sm_gen_seq sm prefix0 %d)' % n)
