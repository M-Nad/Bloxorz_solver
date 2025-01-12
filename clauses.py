from abc import ABC, abstractmethod

class Clause(ABC):
    @abstractmethod
    def not_(self):
        pass
    
    @abstractmethod
    def __repr__(self):
        pass
    
    def get_cnf_list(self): # return cnf list[list], s.t. AND[OR[VAR, ...], OR[VAR, ...], ...]
        pass
    
class VAR(Clause):
    def __init__(self, VAR:int):
        assert isinstance(VAR, int)
        self.VAR=VAR
    
    def get_cnf_list(self):
        return [[self.VAR]]
        
    def not_(self):
        return VAR(-self.VAR)
        
    def __repr__(self):
        return str(self.VAR)

class OR(Clause):
    def __init__(self, *l:Clause):
        if len(l) == 0:
            self.clauses = []
        else :
            if isinstance(l[0], (list,tuple)):
                l = l[0]
            self.clauses = [clause if isinstance(clause,Clause) else VAR(clause) for clause in l]
    
    def not_(self):
        return AND([clause.not_() for clause in self.clauses])
    
    def add_clause(self, clause):
        if not isinstance(clause, Clause):
            clause = VAR(clause)
        self.clauses.append(clause)
            
        
    def get_cnf_list(self):
        cnfs_ = [clause.get_cnf_list() for clause in self.clauses]
        cnf_ = cnfs_[0]
        for other_cnf_ in cnfs_[1:]:
            temp_cnf_ = cnf_.copy()
            cnf_ = []
            for clause_A in temp_cnf_:
                for clause_B in other_cnf_:
                    cnf_.append(clause_A+clause_B)
        return cnf_
        
    def __repr__(self):
        return f"[ {' | '.join(map(str,self.clauses))} ]"

class AND(Clause):
    def __init__(self, *l:Clause):
        if len(l) == 0:
            self.clauses = []
        else :
            if isinstance(l[0], (list,tuple)):
                l = l[0]
            self.clauses = [clause if isinstance(clause,Clause) else VAR(clause) for clause in l]
        
    def add_clause(self, clause):
        if not isinstance(clause, Clause):
            clause = VAR(clause)
        self.clauses.append(clause)
        
    def get_cnf_list(self):
        cnfs_ = [clause.get_cnf_list() for clause in self.clauses]
        cnf_ = []
        for other_cnf_ in cnfs_:
            cnf_ += other_cnf_
        return cnf_
    
    def not_(self):
        return OR([clause.not_() for clause in self.clauses])
    
    def __repr__(self):
        return f"( {' ^ '.join(map(str,self.clauses))} )"
    
class IMPLIES(Clause):
    def __init__(self, clause_A:Clause, clause_B:Clause):
        self.clauses = [clause if isinstance(clause,Clause) else VAR(clause) for clause in (clause_A,clause_B)]
        
    def get_cnf_list(self):
        return OR(self.clauses[0].not_(), self.clauses[1]).get_cnf_list()
        
    def not_(self):
        return AND(self.clauses[0], self.clauses[1].not_())
    
    def __repr__(self):
        return f"{self.clauses[0]} -> {self.clauses[1]}"