import sys
sys.setrecursionlimit(10000)

import time
from venture import shortcuts
ripl = shortcuts.make_church_prime_ripl()

from library import Library
lib = Library(ripl)

def log(N, base=2):
    exp = 0
    while N > 1:
        exp += 1
        N /= base
    return exp

# linear time
def test_predict(N):
    ripl.assume('coin', '(flip)')
    
    for i in range(N):
        ripl.predict('coin')

# O(N) time forwards
# O(log N) time to infer
def test_fold(N):
    lib.load('array')
    
    ripl.assume('N', N)
    ripl.assume('array',
        '(make_array 0 N\
            (mem (lambda (i)\
                (normal 0.0 1.0)\
            ))\
        )'
    )
    
    ripl.predict('(array_fold + array)')

# O(N) time forwards
# O(N) time to infer
def test_fold_size(N):
    ripl.assume('N', N)
    ripl.assume('arr', '(lambda (i) i)')
    
    ripl.predict('(fold + arr 1 (int_plus N (uniform_discrete 0 1)))')

# O(N) forwards
# O(N) to infer
def test_iterate(N):
    ripl.assume('N', N)
    ripl.assume('arr', '(mem (lambda (i) (normal 0.0 1.0)))')
    
    ripl.predict('(iterate + arr 1 N)')

# O(N) forwards
# O(1) to infer
def test_native_pair(N):
    ripl.assume('get', '(lambda (n lst) (if (int_eq n 0) (first lst) (get (int_minus n 1) (rest lst))))')
    
    ripl.assume('list0', '(pair (flip 0.5) 0)')
    
    for i in range(N):
        ripl.assume('list%d' % (i+1), '(pair (flip 0.5) list%d)' % i)
    
    ripl.predict('(get %d list%d)' % (0, N))

# O(N) forwards
# O(N) to infer
def test_lambda_cons(N):
    lib.make_struct("cons", "car", "cdr")
    
    ripl.assume('get', '(lambda (n lst) (if (int_eq n 0) (cons_get_car lst) (get (int_minus n 1) (cons_get_cdr lst))))')

    ripl.assume('list0', '(make_cons (flip 0.5) 0)')
    
    for i in range(N):
        ripl.assume('list%d' % (i+1), '(make_cons (flip) list%d)' % i)
    
    ripl.predict('(get %d list%d)' % (N, N))

# O(N^2/M) time forwards
# O(N/M) time to infer
def test_map_vals(N):
    ripl.assume('f', '(lambda (key) 0)')
    ripl.assume('map0', '(map_make f)')
    
    M = N
    
    for i in range(N/M):
        ripl.assume('map%d' % (i+1), '(map_set map%d %d (normal 1 1))' % (i, i*M))
    
    for i in range(N):
        ripl.predict('(map%d %d)' % (N/M, i))
    
    print ripl.sivm.core_sivm.engine.get_entropy_info()

# O(N^2/M) forwards
# should be O(N^2/M) per inference
def test_map_keys(N):
    ripl.assume('f', '(lambda (key) false)')
    ripl.assume('map0', '(map_make f)')
    
    M = N
    
    for i in range(N/M):
        ripl.assume('map%d' % (i+1), '(map_set map%d (uniform_discrete 0 %d) true)' % (i, N-1))
    
    for i in range(N):
        ripl.predict('(map%d %d)' % (N/M, i))

def test_array(N):
    ripl.assume('N', N)
    ripl.assume('f', '(lambda (i) 0)')
    
    ripl.assume('arr', '(arr_set f 0 N (uniform_discrete 0 (int_minus N 1) 1)')
    ripl.observe('(fold arr min max)')

# N needs to be a power of 2
# O(N log^2 N) forwards
# O(log^2 N) to infer
def test_sort(N):
    lib.load('sort')
    
    ripl.assume('arr', '(mem (lambda (i) (normal i 1)))')
    ripl.assume('sorted', '(sort arr 0 %d true)' % N)
    
    sorted = [ripl.predict('(sorted %d)' % i) for i in range(1)]
    #print(sorted)
    
    #for i in range(N-1):
    #    ripl.observe('(< (sorted %d) (sorted %d))' % (i, i+1), 'true')

# O(M log^2 N) forwards
# O(log^2 N) to infer
def test_randomized_sort(N):
    lib.load('sort')
    
    ripl.assume('N', N)
    ripl.assume('id', '(lambda (i) i)')
    ripl.assume('permutation', '((randomized_sort id 0 N))')
    #print([ripl.predict('(permutation %d)' % i) for i in range(N)])
    #ripl.observe('(fold int_plus permutation 0 N)', N*(N-1)/2)
    
    M = log(N)
    
    for i in range(M):
        ripl.predict('(permutation %d)' % i)
    
    #print(ripl.sivm.core_sivm.engine.get_entropy_info())

# O(N) forwards
# O(N) to infer
def test_choose(N):
    ripl.assume('bits',
        '(mem (lambda (i j)\
            (if (int_gt i 0)\
                (bits (int_minus i 1) (int_div j 2))\
                (int_mod j 2)\
            )\
        ))'
    )
    
    # lazy short-circuit evaluation
    ripl.assume('AND',
        '(lambda (f1 f2)\
            (if (f1) (f2) false)\
        )'
    )
    
    ripl.assume('make_choose',
        '(lambda (n)\
            (let ((rbits (mem (lambda (i) (flip)))))\
                (lambda (j)\
                    ((lazy_fold AND\
                        (lambda (i)\
                            (int_eq\
                                (rbits i)\
                                (bits i j)\
                            )\
                        )\
                        0 n\
                    ))\
                )\
            )\
        )'
    )
    
    ripl.assume('N', N)
    ripl.assume('n', log(N))
    ripl.assume('choose', '(make_choose n)')
    ripl.predict('(fold int_plus choose 0 N)')

def test_matrix_prod(N):
    lib.load('matrix')
    ripl.assume('N', N)
    
    ripl.assume('A', """
        (make_matrix N N
            (lambda (r c)
                (normal (- r c) 1)))
    """)
    
    ripl.assume('x', """
        (make_matrix N 1
            (lambda (r c) (normal 0 1)))
    """)
    
    ripl.assume('Ax', "(matrix_prod A x)")
    
    for i in range(N):
        ripl.observe("(normal (matrix_get_entry Ax %d 0) 1)" % i, 1)
    
# O(N) forwards
# O(log N) to infer
def test_tree_from_key(N):
    lib.load('tree')
    
    ripl.assume('N', N)
    
    ripl.assume('tree', '(tree_from_key 0 N (uniform_discrete 0 (int_minus N 1)) 1)')
    ripl.assume('array', '(tree_to_array tree)')
    ripl.predict('(array_fold int_plus array)')

def test_map_to_tree(N):
    lib.load('tree')
    
    ripl.assume('N', N)
    
    ripl.assume('tree', '(map_to_tree 0 N (lambda (i) i))')
    print(ripl.predict('(tree_count tree)'))

# O(N log^ N) forwards
# O(log^2 N) to infer
def test_tree_sort(N):
    lib.load('tree')
    lib.load('sort')
    
    ripl.assume('N', N)
    ripl.assume('id', '(lambda (i) i)')
    ripl.assume('permutation', '((randomized_sort id 0 N))')
    
    ripl.assume('trees',
        '(mem (lambda (i)\
            (tree_from_key 0 N (permutation i) 1)\
        ))'
    )
    
    ripl.assume('merged', '(fold tree_merge trees 0 N)')
    
    print(ripl.predict('(tree_nth merged (int_div N 2))'))

def test_tree_sample(N):
    lib.load('tree')
    
    ripl.assume('N', N)
    ripl.assume('map',
        '(mem (lambda (i)\
            (poisson i)\
        ))'
    )
    
    ripl.assume('tree', '(map_to_tree 0 N map)')
    ripl.predict('(tree_sample tree)')

def test_geometric(N):
    lib.load('array')
    
    ripl.assume('id', '(lambda (i) i)')
    
    ripl.assume('search',
        '(lambda (min max map)\
            (fold\
                (lambda (i1 i2)\
                    (if (map i1)\
                        i1\
                        i2\
                    )\
                )\
                id min max\
            )\
        )'
    )
    
    ripl.assume('double_search',
        '(lambda (map min)\
            (let\
                (\
                    (max (int_times min 2))\
                    (i (search min max map))\
                )\
                (if (map i)\
                    i\
                    (double_search map max)\
                )\
            )\
        )'
    )
    
    if True:
        ripl.assume('geometric',
            '(lambda (p)\
                (double_search\
                    (mem (lambda (i)\
                        (flip p)\
                    ))\
                    1\
                )\
            )'
        )
    else: # this causes seg faults for some reason...
        # perhaps the trace is too deep?
        ripl.assume('geometric',
            '(lambda (p)\
                (if (flip p)\
                    1\
                    (int_plus 1 (geometric p))\
                )\
            )'
        )

    
    print(ripl.predict('(geometric (/ 1.0 %d))' % N))

def test_blog(N):
    lib.load('blog')
    
    ripl.assume('N', N)
    
    ripl.assume('helicopter', 0)
    ripl.assume('airplane', 1)
    ripl.assume('noise', 2)
    
    ripl.assume('helicopter_set', '(set_from_id helicopter (poisson N))')
    ripl.assume('airplane_set', '(set_from_id airplane (poisson (* N 4)))')
    ripl.assume('aircraft_set', '(set_union helicopter_set airplane_set)')
    
    ripl.assume('noise_set', '(set_from_id noise (poisson (* N 2)))')
    
    ripl.assume('blip_set',
        '(set_union\
            (set_expand noise_set\
                (lambda (i) (poisson 2.0))\
            )\
            (set_expand aircraft_set\
                (lambda (i) (poisson 1.0))\
            )\
        )'
    )
    
    ripl.assume('blade_flash',
        '(lambda (blip)\
            (if (int_eq blip noise)\
                (bernoulli 0.01)\
                (if (int_eq blip helicopter)\
                    (bernoulli 0.9)\
                    (bernoulli 0.1)\
                )\
            )\
        )'
    )
    
    ripl.assume('get_blip',
        '(mem (lambda (i)\
            (set_sample blip_set)\
        ))'
    )
    
    for i in range(6):
        ripl.observe('(blade_flash (get_blip %d))' % i, i==0)
    
    for i in range(6):
        ripl.predict('(get_blip %d)' % i)

def test_scramble(N):
    ripl.assume('flips', "(mem (lambda (i n) (flip)))")
    
    if not lite:
        ripl.assume('pow2', """
            (mem (lambda (i)
                (if (int_eq i 0) 1
                    (int_times 2
                        (pow2 (int_minus i 1))))))
        """)
        
        ripl.assume('bit_set', """
            (lambda (i n)
                (int_eq 1
                    (int_mod
                        (int_div n (pow2 i))
                        2)))
        """)
        
        ripl.assume('clear_bit', """
            (lambda (i n)
                (if (bit_set i n)
                    (int_minus n (pow2 i))
                    n))
        """)
        
        ripl.assume('flip_bit', """
            (lambda (i n)
                (if (bit_set i n)
                    (int_minus n (pow2 i))
                    (int_plus n (pow2 i))))
        """)
    
    ripl.assume('scramble', """
        (lambda (map i)
            (mem (lambda (n)
                (if (flips i (clear_bit 0 n))
                    (map (flip_bit 0 n))
                    (map n)))))
    """)
    
    ripl.assume('map0', '(lambda (n) n)')
    
    k = log(N)
    for i in range(k):
        ripl.assume('map%d' % (i+1), "(scramble map%d %d)" % (i, i))
    
    for j in range(k, k+1):
        for n in range(N):
            ripl.predict('(map%d %d)' % (j, n))

def test_in_range(N):
    ripl.assume('element', '(uniform_discrete 0 %d)' % N)
    
    if not lite:
        ripl.assume('pow2', """
            (mem (lambda (i)
                (if (int_eq i 0) 1
                    (int_times 2
                        (pow2 (int_minus i 1))))))
        """)
        
        ripl.assume('bit_set', """
            (lambda (i n)
                (int_eq 1
                    (int_mod
                        (int_div n (pow2 i))
                        2)))
        """)
        
        ripl.assume('clear_bit', """
            (lambda (i n)
                (if (bit_set i n)
                    (int_minus n (pow2 i))
                    n))
        """)
    
    ripl.assume('n', log(N))
    
    ripl.assume('in_range', """
        (mem (lambda (i min)
            (if (and (int_lt i n)
                    (not (in_range (int_plus i 1) (clear_bit i min))))
                false
                (and (int_lte min element)
                    (int_lt element (int_plus min (pow2 i)))))))
    """)
    
    for k in range(N):
        ripl.predict('(in_range 0 %d)' % k)

def test_categorical(N):
    lib.load('categorical')
    lib.load('dirichlet')
    
    ripl.assume('N', N)
    
    ripl.assume('dir', '(symmetric_dirichlet 1.0)')
    ripl.assume('cat', '(build_categorical 0 N dir)')
    
    lib.observe_categorical('cat', 0)
    ripl.predict('(categorical_sample cat)')

def test_multinomial_array(N):
    lib.load('multinomial')
    
    ripl.assume('m', '(multinomial_array %d 0 %d (lambda (i) i))' % (N, N))

def test_multinomial_func(N):
    lib.load('multinomial')

    ripl.assume('f', '(multinomial_func %d 0 %d (lambda (i) i))' % (N, N))
    [ripl.predict('(f %d)' % i) for i in range(N)]

def cprofile(test_fun, N, I=100):
    cProfile.runctx("test_fun(N)", None, locals())
    if I > 0:
        with open("temp", "w") as temp:
            cProfile.runctx("ripl.infer(I)", globals(), locals())
    lib.clear()
    
def run_test(test_fun, N, I=100):
    start = time.time()
    test_fun(N)
    split = time.time()
    if I > 0:
        ripl.infer(I)
    end = time.time()
    
    lib.clear()
    
    return (split - start, end - split)

def test_asymptotics(test_fun, size=9, I=100):
    for n in range(1, size):
        print run_test(test_fun, 2**n, I)

