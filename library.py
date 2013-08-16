class Library(object):
    def __init__(self, ripl):
        self.ripl = ripl
        self.clear()
    
    def clear(self):
        self.ripl.clear()
        self.loaded = set()
    
    def load(self, module):
        if module not in self.loaded:
            load_module = 'load_' + module
            if not hasattr(self, load_module):
                raise NameError('Module %s does not exist.' % module)
            self.loaded.add(module)
            getattr(self, load_module)()
    
    def make_struct(self, name, *fields):
        args = ' '.join(fields)
        
        maker = 'make_'+name
        
        self.ripl.assume(maker, '(lambda (%s) (lambda (f) (f %s)))' % (args, args))
        
        for (index, field) in enumerate(fields):
            self.ripl.assume(name + '_get_' + field,
                '(lambda (%s)\
                    (%s\
                        (lambda (%s)\
                            %s\
                        )\
                    )\
                )'
                % (name, name, args, field)
            )
            
            _field = '_'+field
            _fields = list(fields)
            _fields[index] = _field
            _args = ' '.join(_fields)
            
            self.ripl.assume(name + '_set_' + field,
                '(lambda (%s %s)\
                    (%s\
                        (lambda (%s)\
                            (%s %s)\
                        )\
                    )\
                )'
                % (name, _field, name, args, maker, _args)
            )
    
    def load_misc(self):
        self.ripl.assume('average',
            '(lambda (min max)\
                (int_div\
                    (int_plus min max)\
                    2\
                )\
            )'
        )
                
        self.ripl.assume('int_pow',
            '(mem (lambda (base exp)\
                (if (int_eq exp 0)\
                    1\
                    (int_times\
                        base\
                        (int_pow base (int_minus exp 1))\
                    )\
                )\
            ))'
        )
        
        self.ripl.assume('uniform',
            '(lambda (n)\
                (fold int_plus\
                    (lambda (i)\
                        (if (flip)\
                            (int_pow 2 i)\
                            0\
                        )\
                    )\
                    0 n\
                )\
            )'
        )
        
        self.ripl.assume('thunk',
            '(lambda (c)\
                (mem (lambda ()\
                    c\
                ))\
            )'
        )
        
                
        self.ripl.assume('lazy_int_plus',
            '(lambda (int1 int2)\
                (mem (lambda ()\
                    (int_plus (int1) (int2))\
                ))\
            )'
        )

    def load_blog(self):
        self.make_struct('set', 'count', 'sampler', 'expander')
        
        self.ripl.assume('set_sample',
            '(lambda (set)\
                ((set_get_sampler set))\
            )'
        )
        
        self.ripl.assume('set_expand',
            '(lambda (set f)\
                ((set_get_expander set) f)\
            )'
        )
        
        self.load('array')
        
        self.ripl.assume('set_from_id',
            '(lambda (id count)\
                (make_set count\
                    (lambda () id)\
                    (lambda (f)\
                        (set_from_id id\
                            (fold int_plus\
                                (mem (lambda (i)\
                                    (f i)\
                                ))\
                                0 count\
                            )\
                        )\
                    )\
                )\
            )'
        )
        
        self.ripl.assume('set_union',
            '(lambda (set1 set2)\
                (let\
                    (\
                        (count1 (set_get_count set1))\
                        (count\
                            (int_plus count1\
                                (set_get_count set2)\
                            )\
                        )\
                    )\
                    (make_set count\
                        (lambda ()\
                            (if (flip (/ count1 count))\
                                (set_sample set1)\
                                (set_sample set2)\
                            )\
                        )\
                        (lambda (f)\
                            (set_union\
                                (set_expand set1 f)\
                                (set_expand set2 f)\
                            )\
                        )\
                    )\
                )\
            )'
        )

    def load_map(self):
        self.ripl.assume('map_make', '(lambda (map) (mem map))')
        
        self.ripl.assume('map_set',
            '(lambda (map key val)\
                (mem (lambda (k)\
                    (if (eq k key)\
                        val\
                        (map k)\
                    )\
                ))\
            )'
        )

    def load_array(self):
        self.make_struct('array', 'min', 'max', 'map')

        self.ripl.assume('fold',
            '(lambda (op arr min max)\
                (let ((avg (int_div (int_plus min max) 2)))\
                    (if (int_eq min avg)\
                        (arr min)\
                        (op\
                            (fold op arr min avg)\
                            (fold op arr avg max)\
                        )\
                    )\
                )\
            )'
        )
        
        self.ripl.assume('array_fold',
            '(lambda (op arr)\
                (fold op\
                    (array_get_map arr)\
                    (array_get_min arr)\
                    (array_get_max arr)\
                )\
            )'
        )

        # op should take thunks and return actual values
        self.ripl.assume('lazy_fold',
            '(lambda (op arr min max)\
                (lambda ()\
                    (let ((avg (int_div (int_plus min max) 2)))\
                        (if (int_eq min avg)\
                            (arr min)\
                            (op\
                                (lazy_fold op arr min avg)\
                                (lazy_fold op arr avg max)\
                            )\
                        )\
                    )\
                )\
            )'
        )
        
        self.ripl.assume('iterate',
            '(lambda (op arr min max)\
                (let ((next (int_plus min 1)))\
                    (if (int_eq next max)\
                        (arr min)\
                        (op\
                            (arr min)\
                            (iterate op arr next max)\
                        )\
                    )\
                )\
            )'
        )
        
        # binary search
        self.ripl.assume('contains',
            '(lambda (arr min max val)\
                (if (int_eq min max)\
                    false\
                    (let ((avg (int_div (int_plus min max) 2)))\
                        (if (= val (arr avg))\
                            true\
                            (if (< val (arr avg))\
                                (contains arr min avg val)\
                                (contains arr avg max val)\
                            )\
                        )\
                    )\
                )\
            )'
        )
        
        # untested
        self.ripl.assume('indexof',
            '(lambda (arr min max val)\
                (if (int_eq min max)\
                    min\
                    (let ((avg (int_div (int_plus min max) 2)))\
                        (if (= val (arr avg))\
                            avg\
                            (if (< val (arr avg))\
                                (indexof arr min avg val)\
                                (indexof arr avg max val)\
                            )\
                        )\
                    )\
                )\
            )'
        )

    # currently only works on powers of 2
    def load_sort(self):
        self.load('array')
        
        self.ripl.assume('concatenate',
            '(lambda (arr1 arr2 avg)\
                (mem (lambda (index)\
                    (if (int_lt index avg)\
                        (arr1 index)\
                        (arr2 index)\
                    )\
                ))\
            )'
        )
        
        # lazy input
        self.ripl.assume('lazy_concatenate',
            '(lambda (arr1 arr2 avg)\
                (mem (lambda (index)\
                    (if (int_lt index avg)\
                        ((arr1) index)\
                        ((arr2) index)\
                    )\
                ))\
            )'
        )
        
        self.ripl.assume('compare',
            '(lambda (arr avg len up)\
                (mem (lambda (index)\
                    (if (int_lt index avg)\
                        (let ((i (int_plus index len)))\
                            (if (eq (< (arr index) (arr i)) up)\
                                (arr index)\
                                (arr i)\
                            )\
                        )\
                        (let ((i (int_minus index len)))\
                            (if (eq (< (arr i) (arr index)) up)\
                                (arr index)\
                                (arr i)\
                            )\
                        )\
                    )\
                ))\
            )'
        )
        
        # not lazy
        self.ripl.assume('randomized_compare',
            '(lambda (arr avg len)\
                (let ((flips (mem (lambda (i) (flip)))))\
                    (mem (lambda (index)\
                        (if (int_lt index avg)\
                            (let ((i (int_plus index len)))\
                                (if (flips index)\
                                    (arr index)\
                                    (arr i)\
                                )\
                            )\
                            (let ((i (int_minus index len)))\
                                (if (flips i)\
                                    (arr index)\
                                    (arr i)\
                                )\
                            )\
                        )\
                    ))\
                )\
            )'
        )
        
        self.ripl.assume('merge',
            '(lambda (arr min max up)\
                (let ((avg (int_div (int_plus max min) 2)))\
                    (if (int_eq min avg)\
                        arr\
                        (let ((a (compare arr avg (int_minus avg min) up)))\
                            (concatenate\
                                (merge a min avg up)\
                                (merge a avg max up)\
                                avg\
                            )\
                        )\
                    )\
                )\
            )'
        )
        
        # output is lazy
        # input not lazy
        self.ripl.assume('randomized_merge',
            '(lambda (arr min max)\
                (mem (lambda ()\
                    (let ((avg (int_div (int_plus max min) 2)))\
                        (if (int_eq min avg)\
                            arr\
                            (let ((a (randomized_compare arr avg (int_minus avg min))))\
                                (lazy_concatenate\
                                    (randomized_merge a min avg)\
                                    (randomized_merge a avg max)\
                                    avg\
                                )\
                            )\
                        )\
                    )\
                ))\
            )'
        )
        
        self.ripl.assume('sort',
            '(lambda (arr min max up)\
                (let ((avg (int_div (int_plus min max) 2)))\
                    (if (int_eq avg min)\
                        arr\
                        (merge\
                            (concatenate\
                                (sort arr min avg true)\
                                (sort arr avg max false)\
                                avg\
                            )\
                            min max up\
                        )\
                    )\
                )\
            )'
        )
        
        # output is lazy
        # input not lazy
        self.ripl.assume('randomized_sort',
            '(lambda (arr min max)\
                (mem (lambda ()\
                    (let ((avg (int_div (int_plus min max) 2)))\
                        (if (int_eq avg min)\
                            arr\
                            ((randomized_merge\
                                (lazy_concatenate\
                                    (randomized_sort arr min avg)\
                                    (randomized_sort arr avg max)\
                                    avg\
                                )\
                                min max\
                            ))\
                        )\
                    )\
                ))\
            )'
        )
        
        self.ripl.assume('array_sort',
            '(lambda (array up)\
                (array\
                    (lambda (min max map)\
                        (make_array min max\
                            (sort map min max up)\
                        )\
                    )\
                )\
            )'
        )
        
        self.ripl.assume('array_randomized_sort',
            '(lambda (array)\
                (array\
                    (lambda (min max map)\
                        (make_array min max\
                            (randomized_sort map min max)\
                        )\
                    )\
                )\
            )'
        )
    
    # trees are always lazy
    # so is the count
    def load_tree(self):
        self.load('misc')
        self.load('array')
        
        self.make_struct('tree', 'min', 'max', 'count', 'left', 'right')
        
        # unlazes the tree and the count
        self.ripl.assume('tree_count',
            '(lambda (tree)\
                ((tree_get_count (tree)))\
            )'
        )
        
        self.ripl.assume('map_to_tree',
            '(lambda (min max map)\
                (mem (lambda ()\
                    (let ((avg (int_div (int_plus min max) 2)))\
                        (if (int_eq min avg)\
                            (make_tree min max\
                                (mem (lambda ()\
                                    (map avg)\
                                ))\
                                false false\
                            )\
                            (let\
                                (\
                                    (left (map_to_tree min avg map))\
                                    (right (map_to_tree avg max map))\
                                )\
                                (make_tree min max\
                                    (mem (lambda ()\
                                        (int_plus\
                                            (tree_count left)\
                                            (tree_count right)\
                                        )\
                                    ))\
                                    left right\
                                )\
                            )\
                        )\
                    )\
                ))\
            )'
        )
        
        self.ripl.assume('array_to_tree',
            '(lambda (array)\
                (array\
                    (lambda (min max map)\
                        (map_to_tree min max map)\
                    )\
                )\
            )'
        )
        
        # gets the count at a specific index
        self.ripl.assume('tree_get',
            '(lambda (tree index)\
                ((tree)\
                    (lambda (min max count left right)\
                        (let ((avg (average min max)))\
                            (if (int_eq min avg)\
                                (count)\
                                (if (int_lt index avg)\
                                    (tree_get left index)\
                                    (tree_get right index)\
                                )\
                            )\
                        )\
                    )\
                )\
            )'
        )
        
        self.ripl.assume('tree_to_map',
            '(lambda (tree)\
                (mem (lambda (index)\
                    (tree_get tree index)\
                ))\
            )'
        )
        
        self.ripl.assume('tree_to_array',
            '(lambda (tree)\
                (make_array\
                    (tree_get_min (tree))\
                    (tree_get_max (tree))\
                    (tree_to_map tree)\
                )\
            )'
        )
        
        self.ripl.assume('tree_nth',
            '(lambda (tree n)\
                ((tree)\
                    (lambda (min max count left right)\
                        (if (int_eq (int_minus max min) 1)\
                            min\
                            (if (int_lt n (tree_count left))\
                                (tree_nth left n)\
                                (tree_nth right (int_minus n (tree_count left)))\
                            )\
                        )\
                    )\
                )\
            )'
        )
        
        self.ripl.assume('tree_range',
            '(lambda (tree min max)\
                ((tree)\
                    (lambda (t_min t_max count left right)\
                        (let ((avg (average t_min t_max)))\
                            (if (int_eq t_min avg)\
                                (count)\
                                (int_plus\
                                    (tree_range left min avg)\
                                    (tree_range right avg max)\
                                )\
                            )\
                        )\
                    )\
                )\
            )'
        )
        
        self.ripl.assume('in_range',
            '(lambda (min max key)\
                (and\
                    (int_lte min key)\
                    (int_lt key max)\
                )\
            )'
        )
        
        # inserts a single key with count num into the tree
        self.ripl.assume('tree_from_key',
            '(lambda (min max key num)\
                (mem (lambda ()\
                    (let\
                        (\
                            (avg (average min max))\
                            (n\
                                (if\
                                    (and\
                                        (int_gt num 0)\
                                        (in_range min max key)\
                                    )\
                                    num 0\
                                )\
                            )\
                        )\
                        (if (int_eq min avg)\
                            (make_tree min max (thunk n) false false)\
                            (make_tree min max (thunk n)\
                                (tree_from_key min avg key n)\
                                (tree_from_key avg max key n)\
                            )\
                        )\
                    )\
                ))\
            )'
        )
        
        # inserts a a range of keys with count num into the tree
        self.ripl.assume('tree_from_range',
            '(lambda (min max rmin rmax num)\
                (mem (lambda ()\
                    (let\
                        (\
                            (avg (average min max))\
                            (n\
                                (if\
                                    (and\
                                        (int_gt num 0)\
                                        (in_range min max key)\
                                    )\
                                    num 0\
                                )\
                            )\
                        )\
                        (if (int_eq min avg)\
                            (make_tree min max (thunk n) false false)\
                            (make_tree min max (thunk n)\
                                (tree_from_key min avg key n)\
                                (tree_from_key avg max key n)\
                            )\
                        )\
                    )\
                ))\
            )'
        )
        
        # combines two adjacent trees
        self.ripl.assume('tree_combine',
            '(lambda (left right)\
                (make_tree\
                    (tree_get_min (left))\
                    (tree_get_max (right))\
                    (lazy_int_plus\
                        (tree_get_count (left))\
                        (tree_get_count (right))\
                    )\
                    left right\
                )\
            )'
        )
        
        # merges two trees over the same range
        self.ripl.assume('tree_merge',
            '(lambda (tree1 tree2)\
                (mem (lambda ()\
                    ((tree1) (lambda (min1 max1 count1 left1 right1)\
                        ((tree2) (lambda (min2 max2 count2 left2 right2)\
                            (let ((avg (average min1 max1)))\
                                (if (int_eq min1 avg)\
                                    (make_tree min1 max1\
                                        (lazy_int_plus count1 count2)\
                                        false false\
                                    )\
                                    (make_tree min1 max1\
                                        (lazy_int_plus count1 count2)\
                                        (tree_merge left1 left2)\
                                        (tree_merge right1 right2)\
                                    )\
                                )\
                            )\
                        ))\
                    ))\
                ))\
            )'
        )
        
        self.ripl.assume('tree_sample',
            '(lambda (tree)\
                ((tree) (lambda (min max count left right)\
                    (if (int_eq min (int_minus max 1))\
                        min\
                        (if (flip (/ (tree_count left) (count)))\
                            (tree_sample left)\
                            (tree_sample right)\
                        )\
                    )\
                ))\
            )'
        )
    
    def load_dpmem(self):
        # doesn't quite work as intended
        # an extra apply is needed to sample from the crp
        self.ripl.assume('dpmem',
            '(lambda (alpha proc)\
                (let\
                    (\
                        (crp (crp_make alpha))\
                        (procs (mem (lambda (table) (mem proc))))\
                    )\
                    (lambda () (procs (crp)))\
                )\
            )'
        )
        
        self.ripl.assume('dpmem0',
            '(lambda (alpha proc)\
                (let\
                    (\
                        (crp (crp_make alpha))\
                        (procs (mem (lambda (table) (mem proc))))\
                    )\
                    (lambda () ((procs (crp))))\
                )\
            )'
        )
        
        self.ripl.assume('dpmem1',
            '(lambda (alpha proc)\
                (let\
                    (\
                        (crp (crp_make alpha))\
                        (procs (mem (lambda (table) (mem proc))))\
                    )\
                    (lambda (arg) ((procs (crp)) arg))\
                )\
            )'
        )

