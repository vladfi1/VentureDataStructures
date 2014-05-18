from venture import shortcuts
from venture.unit import *
from library import Library

ripl = shortcuts.make_church_prime_ripl()

class DictionaryUnit(VentureUnit):
    def makeAssumes(self):
        lib = Library(self)
        lib.load('matrix')
        #lib.load('sort')
        
        N = self.parameters['N']
        
        self.assume('N', N)
        self.assume('inv_sqrt_N', pow(N, -0.5))
        
        self.assume('A', '(make_matrix N N (mem (lambda (i j) (uniform_continuous 0 1))))')
        self.assume('x', '(make_matrix N 1 (mem (lambda (i j) (if (flip inv_sqrt_N) (normal 0 1) 0))))')
        self.assume('b', '(matrix_prod A x)')
        self.assume('noise', '(inv_gamma 1 1)')
    
    def makeObserves(self):
        N = self.parameters['N']
        for i in range(N):
            self.observe("(normal (matrix_get_entry b %d 1) noise)" % i, 1)

def runner(params):
    return DictionaryUnit(ripl, params).runConditionedFromPrior(sweeps=(50**2 / params['N']**2), runs=1, verbose=True)

parameters = {'N': range(5, 30, 5)}
histories = produceHistories(parameters, runner, verbose=True)
plotAsymptotics(parameters, histories, 'sweep_time', fmt='png')
