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
    # TODO[LA-D031] parse 구현
    # 1. 정확한 기약분수·복소수·행렬 값의 저장 표현을 기존 안전 AST 파서로 처리하는지 확인한다.
    # 2. eval 또는 문자열 sympify로 우회하지 않는다.
    raise NotImplementedError("TODO[LA-D031]: parse")


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
    # TODO[LA-D032] math_check 구현
    # 1. 분수·조밀 행렬·유사변환 입력을 생성기의 helper를 호출하지 않고 재계산한다.
    # 2. 기저/고유벡터/QR/SVD/PCA의 비유일한 정답은 해당 수학 조건과 동치로 검사한다.
    raise NotImplementedError("TODO[LA-D032]: math_check")


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
    # TODO[LA-D033] parameter_checks 구현
    # 1. 확장 정책의 범위·랭크·대칭·중심화·중복도·행렬 크기를 원본 문제 파라미터에서 확인한다.
    # 2. 생성 시 validation_trace나 정책 label만으로 통과시키지 않는다.
    raise NotImplementedError("TODO[LA-D033]: parameter_checks")


def validate_payload(payload):
    # TODO[LA-D034] validate_payload 구현
    # 1. 기존 문장 계약은 그대로 두고 숫자·행렬 표현이 바뀐 문제를 검증한다.
    # 2. 문장 의미까지 바꾸는 확장은 별도 계약 작업으로 분리한다.
    # 3. 미지원 유형/조건은 unsupported로 집계하고 성공률 분모에서 숨기지 않는다.
    raise NotImplementedError("TODO[LA-D034]: validate_payload")
