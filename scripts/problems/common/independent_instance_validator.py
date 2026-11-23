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
    """제한된 AST 문법으로 저장된 수학 표현식을 안전하게 복원한다."""
    names = {} if names is None else names

    if not isinstance(names, dict):
        raise Invalid("names는 딕셔너리여야 합니다")

    if value is None or type(value) is bool:
        return value

    if type(value) is int:
        if value.bit_length() > 1024:
            raise Invalid("너무 큰 정수")
        return s.Integer(value)

    if type(value) is float:
        if not math.isfinite(value):
            raise Invalid("비유한 숫자")
        return s.Rational(str(value))

    if isinstance(value, list):
        if len(value) > 64:
            raise Invalid("배열 크기 초과")
        return [parse(v, names, symbols=symbols) for v in value]

    if not isinstance(value, str) or len(value) > 20000:
        raise Invalid("미지원 직렬화 구조")

    try:
        tree = ast.parse(value, mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise Invalid("잘못된 수식 문법") from exc

    count = 0

    def walk(node, depth=0):
        nonlocal count
        count += 1

        if depth > 32 or count > 512:
            raise Invalid("수식 복잡도 초과")

        if isinstance(node, ast.Constant):
            return parse(node.value, names, symbols=symbols)

        if isinstance(node, ast.Name):
            if node.id in names:
                return names[node.id]
            if node.id == "I":
                return s.I
            if node.id == "pi":
                return s.pi
            if node.id == "E":
                return s.E
            if symbols and node.id.isidentifier() and not node.id.startswith("_"):
                return s.Symbol(node.id)
            raise Unsupported("허용되지 않은 이름: " + node.id)

        if isinstance(node, ast.List):
            if len(node.elts) > 64:
                raise Invalid("배열 크기 초과")
            return [walk(x, depth + 1) for x in node.elts]

        if isinstance(node, ast.Tuple):
            if len(node.elts) > 64:
                raise Invalid("튜플 크기 초과")
            return tuple(walk(x, depth + 1) for x in node.elts)

        if isinstance(node, ast.UnaryOp):
            x = walk(node.operand, depth + 1)
            if isinstance(node.op, ast.UAdd):
                return +x
            if isinstance(node.op, ast.USub):
                return -x

        if isinstance(node, ast.BinOp):
            a = walk(node.left, depth + 1)
            b = walk(node.right, depth + 1)

            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                return a * b
            if isinstance(node.op, ast.Div):
                if b == 0:
                    raise Invalid("0으로 나눌 수 없음")
                return a / b
            if isinstance(node.op, ast.Pow):
                if not isinstance(b, s.Integer) or abs(b) > 32:
                    raise Unsupported("지원하지 않는 거듭제곱")
                return a ** b

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.keywords:
                raise Unsupported("허용되지 않은 함수 호출")

            fn = node.func.id
            args = [walk(x, depth + 1) for x in node.args]

            if fn == "Rational" and len(args) in (1, 2):
                if not all(isinstance(x, s.Integer) for x in args):
                    raise Invalid("Rational에는 정수가 필요")
                if len(args) == 2 and args[1] == 0:
                    raise Invalid("분모가 0")
                return s.Rational(*args)

            if fn == "sqrt" and len(args) == 1:
                return s.sqrt(args[0])

            if fn == "Matrix" and len(args) == 1:
                return matrix(args[0])

            raise Unsupported("미지원 함수: " + fn)

        raise Unsupported("미지원 AST 표현")

    try:
        result = walk(tree.body)
        finite(result)
        return result
    except (Invalid, Unsupported):
        raise
    except (ArithmeticError, TypeError, ValueError, RecursionError, OverflowError) as exc:
        raise Invalid("수학 표현식 변환 실패") from exc



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



def math_check(kind, p, answer):
    """문제 조건으로 정답의 수학적 타당성을 독립 검증한다."""

    if not isinstance(p, dict):
        raise Invalid("파라미터 딕셔너리 필요")

    if kind == "matrix_multiplication":
        require("A" in p and "B" in p, "A, B 필요")
        A = matrix(p["A"])
        B = matrix(p["B"])
        require(A.cols == B.rows, "행렬 곱 차원 불일치")
        require(eq(matrix(answer), A * B), "행렬 곱 정답 불일치")
        return True

    if kind in (
        "determinant_by_ero",
        "determinant_cofactor_expansion",
    ):
        require("A" in p, "A 필요")
        A = square(matrix(p["A"]))
        require(eq(answer, A.det()), "행렬식 정답 불일치")
        return True

    if kind == "rank_calculation":
        require("A" in p, "A 필요")
        A = matrix(p["A"])
        require(eq(answer, s.Integer(A.rank())), "랭크 정답 불일치")
        return True

    if kind == "inverse_calculation":
        require("A" in p, "A 필요")
        A = square(matrix(p["A"]))
        X = matrix(answer)
        require(X.shape == A.shape, "역행렬 차원 불일치")
        I = s.eye(A.rows)
        require(
            eq(A * X, I) and eq(X * A, I),
            "역행렬 정답 불일치",
        )
        return True

    if kind == "null_space_basis":
        require("A" in p, "A 필요")
        A = matrix(p["A"])
        require(nullbasis(answer, A), "영공간 기저 불일치")
        return True

    if kind == "column_space_basis":
        require("A" in p, "A 필요")
        A = matrix(p["A"])
        require(basis(answer, A), "열공간 기저 불일치")
        return True

    if kind == "row_space_basis":
        require("A" in p, "A 필요")
        A = matrix(p["A"])
        require(basis(answer, A.T), "행공간 기저 불일치")
        return True

    if kind == "eigenvector_calculation":
        require(
            "A" in p and "lambda_val" in p,
            "A와 lambda_val 필요",
        )
        A = square(matrix(p["A"]))
        lam = p["lambda_val"]
        require(
            isinstance(lam, s.Expr) and not lam.free_symbols,
            "스칼라 고윳값 필요",
        )
        N = A - lam * s.eye(A.rows)
        require(N.det() == 0, "지정된 고윳값이 아님")
        require(
            nullbasis(answer, N),
            "고유공간 기저 불일치",
        )
        return True

    raise Unsupported("미구현 문제 유형: " + str(kind))



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



def parameter_checks(raw, p):
    """문제의 실제 파라미터와 명시된 정책을 독립적으로 검사한다."""

    require(isinstance(raw, dict), "원본 payload 필요")
    require(isinstance(p, dict), "파라미터 딕셔너리 필요")

    def check_value(value, depth=0):
        if depth > 16:
            raise Invalid("파라미터 중첩 깊이 초과")

        if isinstance(value, s.MatrixBase):
            matrix(value)
        elif isinstance(value, (list, tuple)):
            require(len(value) <= 64, "배열 길이 초과")
            for item in value:
                check_value(item, depth + 1)
        elif isinstance(value, dict):
            require(len(value) <= 64, "딕셔너리 크기 초과")
            for item in value.values():
                check_value(item, depth + 1)
        elif isinstance(value, s.Basic):
            finite(value)
        elif type(value) is float:
            require(math.isfinite(value), "비유한 숫자")
        elif value is None or type(value) in (bool, int, str):
            pass
        else:
            raise Unsupported("미지원 파라미터 자료형")

    check_value(p)

    snapshot = raw.get("template_snapshot")
    if not isinstance(snapshot, dict):
        raise Unsupported("Template snapshot이 없어 정책 검증 불가")

    specs = snapshot.get("parameters")
    if not isinstance(specs, dict):
        raise Unsupported("파라미터 정책이 없음")

    def compare_bound(value, limit, lower):
        a = parse(value) if type(value) in (int, float, str) else value
        b = parse(limit)

        if not isinstance(a, s.Expr) or not isinstance(b, s.Expr):
            raise Unsupported("미지원 범위 자료형")

        if a.is_real is not True or b.is_real is not True:
            raise Unsupported("실수 범위 비교 불가")

        comparison = s.Ge(a, b) if lower else s.Le(a, b)

        if comparison is s.false:
            raise Invalid("정책 범위 위반")
        if comparison is not s.true:
            raise Unsupported("범위 비교 결과가 불확정")

    def check_range(value, spec, low, high):
        if spec.get(low) is not None:
            compare_bound(value, spec[low], True)
        if spec.get(high) is not None:
            compare_bound(value, spec[high], False)

    def expected_dimension(rule):
        if isinstance(rule, bool):
            raise Invalid("잘못된 크기 정책")

        if isinstance(rule, int):
            return rule

        if isinstance(rule, str):
            result = condition_value(rule, p)
            if isinstance(result, (int, s.Integer)):
                return int(result)
            raise Unsupported("미지원 크기 참조")

        raise Unsupported("미지원 크기 정책")

    def check_dimension(actual, rule):
        if isinstance(rule, dict):
            if set(rule) != {"min", "max"}:
                raise Unsupported("미지원 크기 범위")
            require(
                rule["min"] <= actual <= rule["max"],
                "크기 범위 위반",
            )
        else:
            require(
                actual == expected_dimension(rule),
                "크기 조건 불일치",
            )

    for name, spec in specs.items():
        if not isinstance(spec, dict):
            raise Unsupported("파라미터 정책 형식 오류")

        if name not in p:
            require(
                spec.get("required", True) is False,
                "필수 파라미터 누락: " + name,
            )
            continue

        value = p[name]
        param_type = spec.get("type")

        if param_type in ("matrix", "vector"):
            M = vector(value) if param_type == "vector" else matrix(value)

            shape = spec.get("shape") or {}
            if not isinstance(shape, dict):
                raise Unsupported("shape 정책 형식 오류")

            actual = {
                "rows": M.rows,
                "cols": M.cols,
                "dimension": M.rows,
                "length": M.rows,
            }

            for field, rule in shape.items():
                if field not in actual:
                    raise Unsupported("미지원 shape 필드: " + field)
                check_dimension(actual[field], rule)

            legacy = {
                "rows": M.rows,
                "cols": M.cols,
                "dimension": M.rows,
            }

            for field, current in legacy.items():
                check_range(
                    current, spec,
                    field + "_min",
                    field + "_max",
                )

            if spec.get("element_type") == "integer":
                require(
                    all(x.is_Integer is True for x in M),
                    "정수 원소 조건 위반",
                )
            elif spec.get("element_type") not in (
                None, "rational", "real", "number"
            ):
                raise Unsupported("미지원 행렬 원소 유형")

            for element in M:
                check_range(
                    element, spec,
                    "element_min", "element_max",
                )

        elif param_type in ("integer", "int"):
            require(
                isinstance(value, (int, s.Integer))
                and not isinstance(value, bool),
                "정수 파라미터 필요",
            )
            check_range(value, spec, "min", "max")

        elif param_type in ("scalar", "number", "rational"):
            require(
                isinstance(value, (int, float, s.Expr))
                and not isinstance(value, bool),
                "스칼라 파라미터 필요",
            )
            check_range(value, spec, "min", "max")

        else:
            raise Unsupported(
                "미지원 파라미터 유형: " + str(param_type)
            )

        if spec.get("choices") or spec.get("exclude"):
            raise Unsupported("선택·제외 정책 검증 미구현")

        if spec.get("derived") is not None:
            raise Unsupported("파생 파라미터 검증 미구현")

    if set(p) - set(specs):
        raise Unsupported("정책에 정의되지 않은 파라미터 존재")

    constraints = snapshot.get("constraints", [])
    if not isinstance(constraints, list):
        raise Unsupported("제약 조건 형식 오류")

    
    def resolve_operand(value):
        if isinstance(value, str):
            return condition_value(value, p)
        if isinstance(value, (bool, int, float)):
            return parse(value)
        raise Unsupported("미지원 제약 조건 피연산자")

    def check_rule(rule):
        if not isinstance(rule, dict):
            raise Unsupported("제약 조건 rule 형식 오류")

        op = rule.get("operator")
        if not isinstance(op, str):
            raise Unsupported("제약 조건 연산자 누락")

        op = op.strip().lower().replace("-", "_").replace(" ", "_")

        aliases = {
            "==": "equals",
            "eq": "equals",
            "!=": "not_equals",
            "ne": "not_equals",
            "<": "less_than",
            "lt": "less_than",
            "<=": "less_than_or_equal",
            "le": "less_than_or_equal",
            ">": "greater_than",
            "gt": "greater_than",
            ">=": "greater_than_or_equal",
            "ge": "greater_than_or_equal",
        }
        op = aliases.get(op, op)

        left = resolve_operand(rule.get("left"))
        right_raw = rule.get("right")
        args = rule.get("args", [])

        if not isinstance(args, list) or args:
            raise Unsupported("다중 인자 제약 조건 미지원")

        properties = {
            "square", "is_square",
            "symmetric", "is_symmetric",
            "invertible", "is_invertible",
            "full_rank", "is_full_rank",
        }

        if op in properties:
            M = matrix(left)
            if op in ("square", "is_square"):
                actual = M.rows == M.cols
            elif op in ("symmetric", "is_symmetric"):
                actual = M.rows == M.cols and eq(M, M.T)
            elif op in ("invertible", "is_invertible"):
                actual = M.rows == M.cols and M.rank() == M.rows
            else:
                actual = M.rank() == min(M.shape)

            expected = True if right_raw is None else resolve_operand(right_raw)
            if not isinstance(expected, (bool, s.logic.boolalg.BooleanAtom)):
                raise Unsupported("속성 조건에는 불리언 값 필요")

            return actual == bool(expected)

        right = resolve_operand(right_raw)

        if op == "equals":
            return eq(left, right)

        if op == "not_equals":
            return not eq(left, right)

        order_ops = {
            "less_than": "negative",
            "less_than_or_equal": "nonpositive",
            "greater_than": "positive",
            "greater_than_or_equal": "nonnegative",
        }

        if op in order_ops:
            if not isinstance(left, (int, float, s.Expr)):
                raise Unsupported("순서 비교는 스칼라만 지원")
            if not isinstance(right, (int, float, s.Expr)):
                raise Unsupported("순서 비교는 스칼라만 지원")

            delta = s.simplify(left - right)
            if delta.is_real is not True:
                raise Unsupported("실수 순서 비교 불가")

            attr = "is_" + order_ops[op]
            result = getattr(delta, attr)

            if result is None:
                raise Unsupported("순서 비교 결과 불확정")
            return bool(result)

        raise Unsupported("미지원 제약 연산자: " + op)

    for constraint in constraints:
        if not isinstance(constraint, dict):
            raise Unsupported("제약 조건 구조 오류")

        if constraint.get("required", True) is False:
            continue

        expression = constraint.get("expression")

        if not isinstance(expression, dict):
            raise Unsupported("문자열/미지원 제약 조건")

        rule = expression.get("rule")
        if not check_rule(rule):
            raise Invalid("필수 제약 조건 위반")

    return True




def validate_payload(payload):
    """저장된 선형대수 문제를 독립적으로 검증한다."""

    checks = []

    def record(name, passed, message):
        checks.append({
            "name": name,
            "passed": passed,
            "message": message,
        })

    def result(verdict):
        return {
            "validator_version": VALIDATOR_VERSION,
            "result": verdict,
            "report": {"checks": checks},
        }

    try:
        # 1. 기본 payload 구조 확인
        require(isinstance(payload, dict), "payload 딕셔너리 필요")
        require(
            payload.get("subject_id") == "linear_algebra",
            "선형대수 문제가 아님",
        )

        kind = payload.get("problem_type")

        if not isinstance(kind, str) or kind not in SUPPORTED_TYPES:
            raise Unsupported("지원하지 않는 문제 유형")

        raw_parameters = payload.get("parameters")
        require(
            isinstance(raw_parameters, dict),
            "parameters 딕셔너리 필요",
        )
        require("expected_answer" in payload, "정답 누락")

        record("payload_structure", True, "기본 구조 확인")
        
        # 2. 실제 검증 구현이 있는 문제 유형만 허용
        implemented = {
            "matrix_multiplication",
            "determinant_by_ero",
            "determinant_cofactor_expansion",
            "rank_calculation",
            "inverse_calculation",
            "null_space_basis",
            "column_space_basis",
            "row_space_basis",
            "eigenvector_calculation",
        }

        if kind not in implemented:
            raise Unsupported("독립 수학 검사 미구현: " + kind)

        # 3. 파라미터 복원
        p = {
            name: parse(value)
            for name, value in raw_parameters.items()
        }

        record("parse_parameters", True, "파라미터 복원 완료")

        # 4. Template 및 문장 계약 검사
        snapshot = payload.get("template_snapshot")

        if not isinstance(snapshot, dict):
            raise Unsupported("Template snapshot 누락")

        builder = snapshot.get("problem_builder")
        if not isinstance(builder, dict):
            raise Unsupported("문제 문장 템플릿 누락")

        templates = builder.get("text_templates_ko")

        if not isinstance(templates, list) or not templates:
            raise Unsupported("문장 템플릿 없음")

        contract = STATEMENTS[kind]

        if templates[0] != contract:
            raise Unsupported("등록된 문장 계약과 템플릿 불일치")

        # 현재 구현은 단순 변수 치환 계약만 처리한다.
        placeholder = re.compile(
            r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}"
        )

        def display(name):
            if name not in p:
                raise Unsupported("문장 변수 누락: " + name)

            value = p[name]
            spec = snapshot.get("parameters", {}).get(name, {})

            if isinstance(spec, dict):
                if spec.get("type") == "matrix":
                    value = matrix(value)
                elif spec.get("type") == "vector":
                    value = vector(value)

            return str(value)

        rendered = placeholder.sub(
            lambda match: display(match.group(1)),
            contract,
        )

        if "{{" in rendered or "{%" in rendered:
            raise Unsupported("미지원 문장 템플릿 구문")

        if payload.get("statement") != rendered:
            raise Unsupported("문장 렌더링 일치 여부 미확정")

        record("statement_contract", True, "문장 계약 일치")

        # 5. 문제 파라미터의 실제 정책 검사
        parameter_checks(payload, p)
        record("parameter_checks", True, "파라미터 조건 통과")

        # 6. 저장된 정답 복원
        answer = parse(payload["expected_answer"])

        answer_type = payload.get("answer_type")

        if answer_type == "matrix":
            answer = matrix(answer)
        elif answer_type == "vector":
            answer = vector(answer)

        record("parse_answer", True, "정답 복원 완료")

        # 7. 독립 수학 검증
        require(
            math_check(kind, p, answer) is True,
            "수학적 정답 검증 실패",
        )

        record("math_check", True, "수학적 정답 확인")

        return result("passed")

    except Unsupported as exc:
        record("independent_validation", False, str(exc))
        return result("unsupported")

    except Invalid as exc:
        record("independent_validation", False, str(exc))
        return result("failed")
