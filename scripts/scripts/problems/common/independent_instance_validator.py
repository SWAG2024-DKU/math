"""저장된 선형대수 문제를 생성기의 계산식/validation_trace 없이 재검증한다.

문제 문장은 지원 문장 계약과 비교한다. 자유로운 한국어 의미 이해는 수행하지
않는다. 지원하지 않는 문장/조건은 unsupported이고, 사람 승인을 대신하지 않는다.
문자열은 AST를 직접 해석하며 eval/sympify(문자열)를 사용하지 않는다.
"""
from __future__ import annotations
import ast
import hashlib
import json
import math
import operator
import re
from pathlib import Path
import sympy as s

VALIDATOR_VERSION = 'independent-linear-algebra-1.0.0'
STATEMENTS = json.loads(Path(__file__).with_name('independent_statement_contracts.json').read_text(encoding='utf-8'))
SUPPORTED_TYPES = frozenset(STATEMENTS)

class Unsupported(ValueError):
    """검사 계약으로 판정할 수 없는 입력이다."""

class Invalid(ValueError):
    """구조/문제 조건/정답이 잘못됐다."""


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if condition is not True and condition is not s.true:
        raise Invalid(message)


def parse(value, names=None, *, symbols=False):
    """제한 AST 문법을 정확한 유리수/SymPy 객체로 복원한다."""
    names = names or {}
    if type(value) is bool or value is None:
        return value
    if type(value) is int:
        if value.bit_length()>1024:raise Invalid('너무 큰 정수')
        return s.Integer(value)
    if type(value) is float:
        if not math.isfinite(value):raise Invalid('비유한 숫자')
        return s.Rational(str(value))
    if isinstance(value,list):return [parse(v,names,symbols=symbols) for v in value]
    if not isinstance(value,str) or len(value)>20000:raise Invalid('미지원 직렬화 구조')
    try:tree=ast.parse(value,mode='eval')
    except (SyntaxError,RecursionError) as exc:raise Invalid('수식 문법 오류') from exc
    if sum(1 for _ in ast.walk(tree))>4000:raise Invalid('수식 복잡도 상한 초과')
    funcs={'sqrt':s.sqrt,'Rational':s.Rational,'Matrix':s.Matrix,'Eq':lambda a,b:s.Eq(a,b,evaluate=False)}
    def walk(n):
        if isinstance(n,ast.Constant):return parse(n.value,names,symbols=symbols)
        if isinstance(n,ast.Name):
            if n.id in names:return names[n.id]
            if n.id=='I':return s.I
            if n.id=='EmptySet':return s.EmptySet
            if symbols and re.fullmatch(r'(?:x_\d+|tau\d+|y\d+)',n.id):return s.Symbol(n.id,real=True)
            raise Unsupported('미지원 기호: '+n.id)
        if isinstance(n,(ast.List,ast.Tuple)):
            return [walk(v) for v in n.elts] if isinstance(n,ast.List) else s.Tuple(*(walk(v) for v in n.elts))
        if isinstance(n,ast.Set):return s.FiniteSet(*(walk(v) for v in n.elts))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=walk(n.operand);return v if isinstance(n.op,ast.UAdd) else -v
        if isinstance(n,ast.BinOp):
            a,b=walk(n.left),walk(n.right)
            if isinstance(n.op,ast.Pow):
                if not isinstance(b,s.Rational) or abs(b)>128:raise Invalid('지수 상한 초과')
                return a**b
            ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
            if type(n.op) in ops:return ops[type(n.op)](a,b)
        if isinstance(n,ast.Call) and not n.keywords and isinstance(n.func,ast.Name):
            if n.func.id in funcs and len(n.args)==({'Rational':2,'Eq':2}.get(n.func.id,1)):
                return funcs[n.func.id](*(walk(a) for a in n.args))
        raise Unsupported('미지원 AST 문법: '+type(n).__name__)
    result=walk(tree.body)
    finite(result)
    return result


def finite(v):
    if isinstance(v,(list,tuple,s.Tuple,s.FiniteSet)):
        for a in v:finite(a)
    elif isinstance(v,s.MatrixBase):
        for a in v:finite(a)
    elif isinstance(v,s.Equality):finite(v.lhs);finite(v.rhs)
    elif isinstance(v,s.Expr):
        if v.has(s.nan,s.zoo,s.oo,-s.oo):raise Invalid('비유한 수식')


def matrix(v):
    if isinstance(v,s.MatrixBase):
        require(1<=v.rows<=8 and 1<=v.cols<=8,'행렬 크기 상한 8');finite(v);return v
    if not isinstance(v,(list,tuple)) or not v:raise Invalid('행렬/벡터 배열 필요')
    if isinstance(v[0],list):
        require(all(isinstance(row,list) and len(row)==len(v[0]) for row in v),'행 길이 불일치')
        require(1<=len(v)<=8 and 1<=len(v[0])<=8,'행렬 크기 상한 8')
    else:require(len(v)<=8,'벡터 크기 상한 8')
    M=s.Matrix(v);finite(M);return M


def vector(v):
    M=matrix(v)
    if M.rows==1:M=M.T
    require(M.cols==1,'열벡터 필요');return M


def square(M):
    require(M.rows==M.cols,'정사각행렬 필요');return M


def symmetric(M):
    square(M);require(all(v.is_real is True for v in M) and eq(M,M.T),'실수 대칭행렬 필요');return M


def zero(v):
    if v==0:return True
    q=s.cancel(s.expand(v))
    if q==0:return True
    return s.simplify(q)==0


def eq(a,b):
    if isinstance(a,s.MatrixBase) or isinstance(b,s.MatrixBase):
        return isinstance(a,s.MatrixBase) and isinstance(b,s.MatrixBase) and a.shape==b.shape and all(zero(u-v) for u,v in zip(a,b))
    if isinstance(a,(bool,s.logic.boolalg.BooleanAtom)) or isinstance(b,(bool,s.logic.boolalg.BooleanAtom)):
        return isinstance(a,(bool,s.logic.boolalg.BooleanAtom)) and isinstance(b,(bool,s.logic.boolalg.BooleanAtom)) and bool(a)==bool(b)
    return zero(a-b)


def columns(v,rows):
    if isinstance(v,s.MatrixBase):B=v
    else:
        require(isinstance(v,(list,tuple)),'기저 목록 필요')
        B=s.Matrix.hstack(*(vector(x) for x in v)) if v else s.zeros(rows,0)
    require(B.rows==rows,'기저 차원 불일치');return B


def basis(v,target):
    B=columns(v,target.rows)
    return B.cols==B.rank()==target.rank() and B.row_join(target).rank()==target.rank()


def nullbasis(v,M):
    B=columns(v,M.cols)
    return B.cols==B.rank()==M.cols-M.rank() and eq(M*B,s.zeros(M.rows,B.cols))


def charpoly_matches(A,roots):
    z=s.Symbol('_characteristic_z');poly=s.Poly(A.charpoly(z).as_expr(),z)
    target=s.Poly(s.prod(z-r for r in roots),z)
    return all(zero(v) for v in (poly-target).all_coeffs())


def extreme_2x2(M,high):
    require(M.shape==(2,2),'2×2 계약 필요')
    delta=s.sqrt((M[0,0]-M[1,1])**2+4*M[0,1]*M[1,0])
    return (M.trace()+(delta if high else -delta))/2


def math_check(kind,p,answer):
    A=matrix(p['A']) if 'A' in p else None
    V=matrix(p['V']) if 'V' in p else None
    b=vector(p['b']) if 'b' in p else None
    if kind=='matrix_multiplication':return eq(matrix(answer),A*matrix(p['B']))
    if kind=='algebraic_expansion_verification':
        B=matrix(p['B']);return eq(matrix(answer),A*A+A*B+B*A+B*B)
    if kind=='transpose_algebra':return eq(matrix(answer),(A*matrix(p['B'])).T)
    if kind=='equation_to_matrix':return eq(matrix(answer),A.row_join(b))
    if kind=='matrix_to_vector_equation':
        require(isinstance(answer,s.Equality),'Eq 답 필요')
        x=p['x'];return eq(answer.lhs-answer.rhs,A*x-b) or eq(answer.lhs-answer.rhs,b-A*x)
    if kind in {'inverse_calculation','elementary_inverse_calculation'}:
        M=square(A if A is not None else matrix(p['E']));B=matrix(answer)
        require(M.det()!=0,'가역행렬 필요')
        return B.shape==M.shape and eq(M*B,s.eye(M.rows)) and eq(B*M,s.eye(M.rows))
    if kind=='change_of_basis_calculation':
        B,C= square(matrix(p['B'])),square(matrix(p['C']))
        require(B.det()!=0 and C.det()!=0,'두 기저는 가역이어야 함')
        return eq(C*matrix(answer),B)
    if kind in {'cramer_rule_solution','solve_by_lu'}:
        square(A);require(A.det()!=0,'유일해가 필요한 유형');return eq(A*vector(answer),b)
    if kind in {'least_squares_calculation','linear_regression_calculation'}:
        M=matrix(p['X']) if kind=='linear_regression_calculation' else A
        v=vector(p['y']) if kind=='linear_regression_calculation' else b
        require(M.rank()==M.cols,'full column rank 필요')
        return eq(M.H*(M*vector(answer)-v),s.zeros(M.cols,1))
    if kind in {'determinant_by_ero','determinant_cofactor_expansion'}:return eq(answer,square(A).det())
    if kind=='block_matrix_determinant':return eq(answer,square(matrix(p['B'])).det()*square(matrix(p['C'])).det())
    if kind=='geometric_area_volume_calculation':return eq(answer,abs(square(A).det()))
    if kind=='rank_calculation':return eq(answer,A.rank())
    if kind=='rank_nullity_calculation':return eq(answer,A.cols-A.rank())
    if kind=='matrix_rank_property':return eq(answer,min(int(p['m']),int(p['n'])))
    if kind=='matrix_power_calculation':return eq(matrix(answer),square(A)**int(p['k']))
    if kind=='norm_distance_calculation':return eq(answer,(vector(p['u'])-vector(p['v'])).norm())
    if kind=='complex_inner_product_calculation':return eq(answer,(vector(p['u']).H*vector(p['v']))[0])
    if kind=='standard_matrix_derivation':return eq(matrix(answer),matrix(p['images']))
    if kind in {'elementary_matrix_construction','ero_application'}:
        M=s.eye(int(p['n'])) if kind=='elementary_matrix_construction' else A.copy()
        i,j,c=int(p['target_row']),int(p['source_row']),p['c']
        require(0<=i<M.rows and 0<=j<M.rows and i!=j and c!=0,'잘못된 행연산')
        M[i,:]=M[i,:]+c*M[j,:];return eq(matrix(answer),M)
    if kind=='consistency_check':
        M=matrix(p['Aug']);require(M.cols>=2,'첨가행렬 필요')
        return answer==('해 존재' if M[:,:-1].rank()==M.rank() else '해 없음')
    if kind=='invertibility_determination':return answer==('가역' if square(A).det()!=0 else '비가역')
    bools={
        'basis_verification':lambda:V.rows==V.cols==int(p['n']) and V.rank()==int(p['n']),
        'linear_independence_test':lambda:V.rank()==V.cols,
        'span_membership_test':lambda:V.rank()==V.row_join(b).rank(),
        'symmetry_classification':lambda:eq(square(A),A.T),
        'singular_matrix_identification':lambda:square(A).det()==0,
        'equivalence_theorem_check':lambda:square(A).det()!=0,
        'ref_identification':lambda:bool(A.is_echelon),
        'orthonormal_verification':lambda:eq(matrix(p['Q']).H*matrix(p['Q']),s.eye(matrix(p['Q']).cols)),
        'linear_transformation_verification':lambda:eq(b,s.zeros(A.rows,1)),
        'subspace_verification':lambda:eq(b,s.zeros(A.rows,1)),
        'positive_definite_test':lambda:all(symmetric(A)[:j,:j].det()>0 for j in range(1,A.rows+1)),
    }
    if kind in bools:return eq(answer,bool(bools[kind]()))
    if kind=='rref_calculation':return eq(matrix(answer),A.rref()[0])
    if kind=='free_variable_identification':
        require(isinstance(answer,list) and all(v.is_integer is True for v in answer),'정수 인덱스 목록 필요')
        return len(set(answer))==len(answer) and set(answer)==set(range(A.cols))-set(A.rref()[1])
    if kind=='column_space_basis':return basis(answer,A)
    if kind=='row_space_basis':return basis(answer,A.T)
    if kind=='null_space_basis':return nullbasis(answer,A)
    if kind=='left_null_space_basis':return nullbasis(answer,A.T)
    if kind=='orthogonal_complement_calculation':return nullbasis(answer,matrix(p['W']).T)
    if kind=='kernel_image_calculation':
        require(isinstance(answer,list) and len(answer)==2,'핵·상 기저 쌍 필요')
        return nullbasis(answer[0],A) and basis(answer[1],A)
    if kind=='eigenvector_calculation':
        N=square(A)-p['lambda_val']*s.eye(A.rows);require(N.det()==0,'제시된 λ가 고윳값이 아님')
        return nullbasis(answer,N)
    if kind=='eigenvalue_calculation':
        square(A);require(isinstance(answer,list) and bool(answer),'고윳값 목록 필요')
        # 서로 다른 고윳값 목록이다. 제곱인수를 제거한 특성다항식과 비교한다.
        z=s.Symbol('_characteristic_z');poly=s.Poly(A.charpoly(z).as_expr(),z).sqf_part().monic()
        require(len(answer)<=A.rows,'고윳값 개수 초과')
        return len(answer)==poly.degree() and all(not eq(a,b) for i,a in enumerate(answer) for b in answer[:i]) and all(zero(v) for v in (poly-s.Poly(s.prod(z-v for v in answer),z)).all_coeffs())
    if kind=='gram_schmidt_orthogonalization':
        require(V.rank()==V.cols,'선형독립 입력 필요');Q=columns(answer,V.rows)
        return Q.shape==V.shape and eq(Q.H*Q,s.eye(Q.cols)) and all(basis(Q[:,:i],V[:,:i]) for i in range(1,V.cols+1))
    if kind=='orthogonal_projection_calculation':
        a=vector(p['a']);require(not eq(b,s.zeros(b.rows,1)),'사영 방향은 비영벡터')
        v=vector(answer);return v.shape==b.shape and b.row_join(v).rank()==1 and eq(b.H*(a-v),s.zeros(1,1))
    if kind=='lu_factorization':
        square(A);M=matrix(answer);n=A.rows
        if M.shape!=(n,2*n):return False
        L,U=M[:,:n],M[:,n:]
        return bool(L.is_lower and U.is_upper) and all(eq(L[i,i],1) for i in range(n)) and eq(L*U,A)
    if kind in {'matrix_diagonalization','orthogonal_diagonalization_calculation','jordan_canonical_form_calculation'}:
        square(A);require(isinstance(answer,list) and len(answer)==2,'변환행렬·표준형 쌍 필요')
        P,D=map(matrix,answer)
        if P.shape!=A.shape or D.shape!=A.shape or P.det()==0:return False
        if kind=='jordan_canonical_form_calculation':
            require(A.shape==(2,2),'현재 Jordan 계약은 2×2 결함 행렬')
            require(A!=s.eye(2)*A.trace()/2,'결함 행렬 필요')
            return D==s.Matrix([[A.trace()/2,1],[0,A.trace()/2]]) and eq(A*P,P*D)
        if not D.is_diagonal():return False
        if kind=='orthogonal_diagonalization_calculation':
            symmetric(A)
            if not all(v.is_real is True for v in P) or not eq(P.T*P,s.eye(A.rows)):return False
        return eq(A*P,P*D)
    if kind=='qr_factorization_calculation':
        require(A.rank()==A.cols,'full column rank 필요')
        require(isinstance(answer,list) and len(answer)==2,'QR 쌍 필요');Q,R=map(matrix,answer)
        return Q.shape==A.shape and R.shape==(A.cols,A.cols) and bool(R.is_upper) and eq(Q.H*Q,s.eye(A.cols)) and eq(Q*R,A)
    if kind=='parametric_solution_extraction':
        if answer==s.EmptySet:return A.rank()!=A.row_join(b).rank()
        require(isinstance(answer,s.FiniteSet) and len(answer)==1,'한 매개변수 벡터 해집합 필요')
        x=vector(list(next(iter(answer))));require(x.rows==A.cols,'해 벡터 차원 불일치')
        syms=sorted(x.free_symbols,key=str);J=x.jacobian(syms) if syms else s.zeros(A.cols,0)
        if J.free_symbols:return False
        offset=x.subs(dict.fromkeys(syms,0))
        return eq(A*x,b) and J.rank()==A.cols-A.rank() and (not syms or eq(x,offset+J*s.Matrix(syms)))
    if kind=='quadratic_form_transformation':
        symmetric(A);require(isinstance(answer,s.Expr),'대각 이차형식 필요')
        vars=sorted(answer.free_symbols,key=str)
        if not vars:return answer==0 and A==s.zeros(A.rows)
        if len(vars)>A.rows or any(not re.fullmatch(r'y[1-9]\d*',str(v)) or int(str(v)[1:])>A.rows for v in vars):return False
        poly=s.Poly(answer,*vars)
        if any(sum(e)!=2 or sum(v!=0 for v in e)!=1 for e,_ in poly.terms()):return False
        coeff=[poly.coeff_monomial(v**2) for v in vars]+[s.Integer(0)]*(A.rows-len(vars))
        return charpoly_matches(A,coeff)
    if kind=='spectral_decomposition_calculation':
        symmetric(A);require(isinstance(answer,list) and bool(answer),'스펙트럼 항 목록 필요')
        total=s.zeros(A.rows);identity=s.zeros(A.rows);previous=[]
        for lam,raw in answer:
            P=matrix(raw)
            if P.shape!=A.shape or P.rank()==0 or not eq(P,P.T) or not eq(P*P,P) or not eq(A*P,lam*P):return False
            if any(not eq(P*Q,s.zeros(A.rows)) for Q in previous):return False
            previous.append(P);total+=lam*P;identity+=P
        return eq(total,A) and eq(identity,s.eye(A.rows))
    if kind=='pseudoinverse_calculation':
        B=matrix(answer)
        return B.shape==(A.cols,A.rows) and eq(A*B*A,A) and eq(B*A*B,B) and eq((A*B).H,A*B) and eq((B*A).H,B*A)
    if kind=='svd_calculation':
        require(isinstance(answer,list) and len(answer)==3,'U,Σ,V 필요');U,S,V=map(matrix,answer)
        if U.shape!=(A.rows,A.rows) or V.shape!=(A.cols,A.cols) or S.shape!=A.shape:return False
        diag=[S[i,i] for i in range(min(A.shape))]
        return all(S[i,j]==0 for i in range(S.rows) for j in range(S.cols) if i!=j) and all(v.is_real is True and v.is_nonnegative is True for v in diag) and all(diag[i]>=diag[i+1] for i in range(len(diag)-1)) and eq(U.H*U,s.eye(U.cols)) and eq(V.H*V,s.eye(V.cols)) and eq(U*S*V.H,A)
    if kind=='compact_svd_approximation':
        require(A.shape==(2,2),'현재 최적 근사 계약은 2×2');B=matrix(answer)
        if B.shape!=A.shape or B.rank()>1:return False
        M=A.H*A;lower=extreme_2x2(M,False);upper=extreme_2x2(M,True)
        require(upper>lower,'서로 다른 특잇값 필요')
        return eq(((A-B).H*(A-B)).trace(),lower)
    if kind=='pca_calculation':
        require(A.cols==2 and A.rows>=2 and all(sum(A[:,i])==0 for i in range(2)),'중심화 2변량 자료 필요')
        P=matrix(answer);C=A.T*A/(A.rows-1);top=extreme_2x2(C,True)
        require(top>extreme_2x2(C,False),'최대 고윳값의 유일성 필요')
        return P.shape==(2,2) and P.rank()==1 and eq(P,P.T) and eq(P*P,P) and eq(C*P,top*P)
    raise Unsupported('미구현 유형: '+kind)


def condition_value(text,p):
    """파라미터 참조/크기/조건에 필요한 작은 AST만 지원한다."""
    if not isinstance(text,str):return parse(text)
    def walk(n):
        if isinstance(n,ast.Name) and n.id in p:return p[n.id]
        if isinstance(n,ast.Constant):return parse(n.value)
        if isinstance(n,ast.Attribute) and n.attr in ('rows','cols','dimension','length'):
            return vector(walk(n.value)).rows if n.attr in ('dimension','length') else getattr(matrix(walk(n.value)),n.attr)
        if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            return {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(n.op)](walk(n.left),walk(n.right))
        if isinstance(n,ast.Call) and not n.keywords:
            if isinstance(n.func,ast.Name) and n.func.id in ('det','rank') and len(n.args)==1:
                M=matrix(walk(n.args[0]));return M.det() if n.func.id=='det' else M.rank()
            if isinstance(n.func,ast.Attribute) and n.func.attr=='dot' and len(n.args)==1:
                return vector(walk(n.func.value)).dot(vector(walk(n.args[0])))
        if isinstance(n,ast.Compare):
            left=walk(n.left);ops={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge}
            for op,node in zip(n.ops,n.comparators):
                right=walk(node)
                if type(op) not in ops:raise Unsupported('미지원 비교')
                if not bool(ops[type(op)](left,right)):return False
                left=right
            return True
        raise Unsupported('미지원 조건/차원 표현: '+text)
    tree=ast.parse(text,mode='eval');return walk(tree.body)


def parameter_checks(raw,p):
    specs=raw['parameters'];require(set(p)==set(specs),'파라미터 누락/미선언 값')
    for name,spec in specs.items():
        val=p[name];kind=spec['type']
        if kind in ('matrix','vector'):
            M=matrix(val) if kind=='matrix' else vector(val);p[name]=M
        elif kind=='integer':require(isinstance(val,s.Integer),'정수 파라미터 필요: '+name)
        elif kind=='rational':require(isinstance(val,s.Rational),'유리수 파라미터 필요: '+name)
        elif kind=='real':require(isinstance(val,s.Expr) and val.is_real is True,'실수 파라미터 필요: '+name)
        elif kind not in ('derived','choice'):raise Unsupported('파라미터 타입: '+kind)
    for name,spec in specs.items():
        val=p[name];M=val if isinstance(val,s.MatrixBase) else None
        elems=list(M) if M is not None else [val]
        for v in elems:
            if not isinstance(v,s.Expr) or v.free_symbols or v.is_finite is not True:raise Invalid('유한한 숫자 파라미터 필요: '+name)
            # 복소 벡터는 실수 범위 검사를 적용하지 않는다. 선언한 원소 타입은 검사한다.
            element_type=spec.get('element_type') if M is not None else None
            if element_type=='integer':
                # 이 두 복소 벡터 생성 계약의 integer는 실수부·허수부 각각의 정수를 뜻한다.
                components=v.as_real_imag() if spec.get('generator') in ('small_gaussian_vector','complex_real_inner_partner') else (v,)
                require(all(x.is_integer is True for x in components),'정수 원소/성분 필요: '+name)
                for component in components:
                    if spec.get('element_min') is not None:require(component>=spec['element_min'],'정수 성분 하한 위반')
                    if spec.get('element_max') is not None:require(component<=spec['element_max'],'정수 성분 상한 위반')
            elif element_type=='rational':require(isinstance(v,s.Rational),'유리수 원소 필요: '+name)
            elif element_type=='real':require(v.is_real is True,'실수 원소 필요: '+name)
            elif element_type not in (None,'complex'):raise Unsupported('미지원 원소 타입')
            if v.is_real is True:
                lo=spec.get('element_min') if M is not None else None
                hi=spec.get('element_max') if M is not None else None
                lo=spec.get('min') if lo is None else lo;hi=spec.get('max') if hi is None else hi
                if lo is not None:require(v>=lo,'파라미터 하한 위반: '+name)
                if hi is not None:require(v<=hi,'파라미터 상한 위반: '+name)
            if v in [parse(x) for x in spec.get('exclude',[])]:raise Invalid('제외값: '+name)
        if spec.get('choices'):require(val in [parse(x) for x in spec['choices']],'choices 위반: '+name)
        if M is not None:
            shape=spec.get('shape') or {}
            for field,actual in [('rows',M.rows),('cols',M.cols),('dimension',M.rows),('length',M.rows)]:
                size=shape.get(field)
                if size is None:continue
                if isinstance(size,dict):
                    if size.get('min') is not None:require(actual>=size['min'],'크기 하한 위반: '+name)
                    if size.get('max') is not None:require(actual<=size['max'],'크기 상한 위반: '+name)
                else:require(actual==condition_value(size,p),'크기 의존조건 위반: '+name)
            families=spec.get('allowed_families') or []
            if any(f not in ('symmetric','diagonal') for f in families):raise Unsupported('미지원 행렬 family')
            if families:
                valid_family=any((M.rows==M.cols and eq(M,M.T) and all(x.is_real is True for x in M)) if f=='symmetric' else bool(M.is_diagonal()) for f in families)
                require(valid_family,'허용 행렬 형태 불충족')
    for entry in raw.get('constraints',[]):
        if not entry.get('required',True):continue
        ex=entry['expression']
        if isinstance(ex,str):ok=condition_value(ex,p)
        else:
            if ex.get('scope') not in (None,'generation','both'):continue
            rule=ex['rule'];left=condition_value(rule['left'],p);op=rule['operator'];right=rule.get('right')
            if op in ('symmetric','diagonalizable','lu_without_pivoting'):
                M=matrix(left)
                if op=='symmetric':symmetric(M);ok=True
                elif op=='diagonalizable':ok=M.is_diagonalizable(reals_only=True)
                else:
                    _,_,swaps=M.LUdecomposition();ok=not swaps
            else:
                ops={'equals':operator.eq,'not_equals':operator.ne,'greater_than':operator.gt,'greater_or_equal':operator.ge,'less_than':operator.lt,'less_or_equal':operator.le}
                if op not in ops:raise Unsupported('미지원 필수 조건: '+op)
                ok=ops[op](left,condition_value(right,p))
        require(bool(ok),'필수 생성 조건 위반: '+entry['type'])


def validate_payload(payload):
    """DB 없이 한 문제를 검사하고 passed/failed/unsupported 보고서를 반환한다."""
    checks=[]
    result={'validator_version':VALIDATOR_VERSION,'result':'failed','report':{'checks':checks}}
    def done(name):checks.append({'name':name,'passed':True})
    try:
        from app.schemas.problem_template import ProblemTemplate
        from jinja2 import StrictUndefined
        from jinja2.sandbox import SandboxedEnvironment
        require(isinstance(payload,dict),'payload 객체 필요')
        raw=payload['template_snapshot'];t=ProblemTemplate.model_validate(raw)
        require(t.taxonomy.subject_id=='linear_algebra','선형대수만 지원')
        require(type(payload.get('seed')) is int,'seed 정수 필요')
        kind=payload['problem_type']
        if kind not in SUPPORTED_TYPES:raise Unsupported('미구현 유형: '+kind)
        for field,expected in {'subject_id':t.taxonomy.subject_id,'template_id':t.template_id,'template_version':t.template_version,'generation_rule_id':t.generation_rule_id,'generation_rule_version':t.generation_rule_version,'answer_type':t.answer_spec.answer_type}.items():
            require(payload[field]==expected,'Template 불일치: '+field)
        require(kind==t.classification.problem_type and t.classification.answer_type==t.answer_spec.answer_type,'문제/답 유형 불일치')
        require(payload.get('publishable') is False,'비공개 Preview payload 필요')
        done('template_and_payload_structure')
        p={name:parse(value) for name,value in payload['parameters'].items()};parameter_checks(raw,p)
        done('parameter_and_generation_conditions')
        # symbol 선언은 방정식 복원을 위한 x 벡터에만 사용한다.
        for name,spec in raw.get('symbols',{}).items():
            dim=spec.get('dimension')
            if dim is not None:
                size=int(condition_value(dim,p));require(1<=size<=8,'기호 벡터 크기 상한 8');p[name]=s.Matrix([s.Symbol(f'{name}_{i}',real=True) for i in range(1,size+1)])
            else:p[name]=s.Symbol(name,real=True)
        pattern=t.problem_builder.text_templates_ko[0]
        if pattern!=STATEMENTS[kind]:raise Unsupported('지원 문장 계약과 다름; 문장 계약 추가 필요')
        rendered=SandboxedEnvironment(undefined=StrictUndefined).from_string(pattern).render({k:str(v) for k,v in p.items()})
        require(rendered==payload['statement'],'문제 문장과 파라미터 불일치')
        done('statement_matches_parameters')
        rawanswer=payload['expected_answer']
        require(rawanswer is not None,'정답 null')
        answer=rawanswer if kind in ('consistency_check','invertibility_determination') else parse(rawanswer,symbols=True)
        require(bool(math_check(kind,p,answer)),'수학적 정답 조건 불충족')
        done('independent_mathematical_identity')
        result['result']='passed'
    except Unsupported as exc:
        result['result']='unsupported';checks.append({'name':'unsupported_contract','passed':False,'message':str(exc)})
    except Exception as exc:
        checks.append({'name':'validation_failure','passed':False,'message':f'{type(exc).__name__}: {exc}'})
    return result
