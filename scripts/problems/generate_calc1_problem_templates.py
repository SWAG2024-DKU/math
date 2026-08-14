from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any


def p(
    type_: str,
    description: str,
    *,
    min_: int | float | None = None,
    max_: int | float | None = None,
    choices: list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": type_,
        "required": True,
        "min": min_,
        "max": max_,
        "exclude": [],
        "choices": choices or [],
        "step": None,
        "distribution": "uniform",
        "description": description,
    }


# ============================================================================
# BLUEPRINTS: Calculus I Ch.09 ~ Ch.10
# ============================================================================

BLUEPRINTS: dict[str, dict[str, Any]] = {
    # ------------------------------------------------------------------------
    # Chapter 09: Parametric Equations and Polar Coordinates
    # ------------------------------------------------------------------------
    "parametric_curve_sketching": {
        "answer_type": "equation",
        "parameters": {
            "x_t": p("expression", "매개변수 t로 주어진 x(t)."),
            "y_t": p("expression", "매개변수 t로 주어진 y(t)."),
            "t_min": p("real", "매개변수 구간의 시작값.", min_=-10, max_=10),
            "t_max": p("real", "매개변수 구간의 끝값.", min_=-10, max_=10),
        },
        "text": "매개곡선 x={{ x_t }}, y={{ y_t }}, {{ t_min }}<=t<={{ t_max }}의 곡선을 나타내는 관계식과 진행 방향을 구하시오.",
        "latex": r"x=x(t),\quad y=y(t)",
        "builder_cas": "eliminate_parameter(x_t, y_t, t)",
        "answer_cas": "eliminate_parameter(x_t, y_t, t)",
        "answer_latex": r"F(x,y)=0",
        "validators": ["symbolic_equivalence"],
    },
    "parameter_elimination": {
        "answer_type": "equation",
        "parameters": {
            "x_t": p("expression", "매개변수 t로 주어진 x(t)."),
            "y_t": p("expression", "매개변수 t로 주어진 y(t)."),
        },
        "text": "x={{ x_t }}, y={{ y_t }}에서 매개변수 t를 소거하여 x,y 사이의 방정식을 구하시오.",
        "latex": r"x=x(t),\quad y=y(t)",
        "builder_cas": "eliminate_parameter(x_t, y_t, t)",
        "answer_cas": "eliminate_parameter(x_t, y_t, t)",
        "answer_latex": r"F(x,y)=0",
        "validators": ["symbolic_equivalence"],
    },
    "parametric_tangent_slope_calculation": {
        "answer_type": "expression",
        "parameters": {
            "x_t": p("expression", "x(t)."),
            "y_t": p("expression", "y(t)."),
            "t0": p("real", "기울기를 계산할 t값.", min_=-5, max_=5),
        },
        "text": "x={{ x_t }}, y={{ y_t }}인 매개곡선에서 t={{ t0 }}일 때 dy/dx를 구하시오.",
        "latex": r"\frac{dy}{dx}=\frac{dy/dt}{dx/dt}",
        "builder_cas": "diff(y_t,t)/diff(x_t,t)",
        "answer_cas": "(diff(y_t,t)/diff(x_t,t)).subs(t,t0)",
        "answer_latex": r"\left.\frac{dy/dt}{dx/dt}\right|_{t=t_0}",
        "validators": ["symbolic_equivalence"],
    },
    "horizontal_vertical_tangent_identification": {
        "answer_type": "set",
        "parameters": {
            "x_t": p("expression", "x(t)."),
            "y_t": p("expression", "y(t)."),
        },
        "text": "x={{ x_t }}, y={{ y_t }}인 매개곡선의 수평접선 또는 수직접선이 나타나는 t값을 구하시오.",
        "latex": r"\frac{dy}{dt}=0\ \text{or}\ \frac{dx}{dt}=0",
        "builder_cas": "solve_tangent_conditions(x_t,y_t,t)",
        "answer_cas": "solve_tangent_conditions(x_t,y_t,t)",
        "answer_latex": r"\{t:\ y'(t)=0\ \text{or}\ x'(t)=0\}",
        "validators": ["symbolic_equivalence"],
    },
    "parametric_second_derivative_calculation": {
        "answer_type": "expression",
        "parameters": {
            "x_t": p("expression", "x(t)."),
            "y_t": p("expression", "y(t)."),
        },
        "text": "x={{ x_t }}, y={{ y_t }}인 매개곡선의 d^2y/dx^2를 구하시오.",
        "latex": r"\frac{d^2y}{dx^2}=\frac{d}{dt}\left(\frac{dy}{dx}\right)\Big/\frac{dx}{dt}",
        "builder_cas": "diff(diff(y_t,t)/diff(x_t,t),t)/diff(x_t,t)",
        "answer_cas": "diff(diff(y_t,t)/diff(x_t,t),t)/diff(x_t,t)",
        "answer_latex": r"\frac{d}{dt}(dy/dx)/(dx/dt)",
        "validators": ["symbolic_equivalence"],
    },
    "parametric_area_calculation": {
        "answer_type": "scalar",
        "parameters": {
            "x_t": p("expression", "x(t)."),
            "y_t": p("expression", "y(t)."),
            "a": p("real", "적분구간 시작값."),
            "b": p("real", "적분구간 끝값."),
        },
        "text": "x={{ x_t }}, y={{ y_t }}, {{ a }}<=t<={{ b }}인 매개곡선 아래 넓이를 구하시오.",
        "latex": r"A=\int_a^b y(t)x'(t)\,dt",
        "builder_cas": "integrate(y_t*diff(x_t,t),(t,a,b))",
        "answer_cas": "integrate(y_t*diff(x_t,t),(t,a,b))",
        "answer_latex": r"\int_a^b y(t)x'(t)\,dt",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "parametric_arc_length_calculation": {
        "answer_type": "scalar",
        "parameters": {
            "x_t": p("expression", "x(t)."),
            "y_t": p("expression", "y(t)."),
            "a": p("real", "적분구간 시작값."),
            "b": p("real", "적분구간 끝값."),
        },
        "text": "x={{ x_t }}, y={{ y_t }}, {{ a }}<=t<={{ b }}인 매개곡선의 호의 길이를 구하시오.",
        "latex": r"L=\int_a^b\sqrt{x'(t)^2+y'(t)^2}\,dt",
        "builder_cas": "integrate(sqrt(diff(x_t,t)**2+diff(y_t,t)**2),(t,a,b))",
        "answer_cas": "integrate(sqrt(diff(x_t,t)**2+diff(y_t,t)**2),(t,a,b))",
        "answer_latex": r"\int_a^b\sqrt{x'(t)^2+y'(t)^2}\,dt",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "parametric_surface_area_calculation": {
        "answer_type": "scalar",
        "parameters": {
            "x_t": p("expression", "x(t)."),
            "y_t": p("expression", "y(t), x축 회전에서는 y(t)>=0."),
            "a": p("real", "적분구간 시작값."),
            "b": p("real", "적분구간 끝값."),
        },
        "text": "매개곡선 x={{ x_t }}, y={{ y_t }}를 x축 둘레로 회전시킨 곡면의 넓이를 구하시오. 구간은 {{ a }}<=t<={{ b }}이다.",
        "latex": r"S=\int_a^b2\pi y(t)\sqrt{x'(t)^2+y'(t)^2}\,dt",
        "builder_cas": "integrate(2*pi*y_t*sqrt(diff(x_t,t)**2+diff(y_t,t)**2),(t,a,b))",
        "answer_cas": "integrate(2*pi*y_t*sqrt(diff(x_t,t)**2+diff(y_t,t)**2),(t,a,b))",
        "answer_latex": r"\int_a^b2\pi y(t)\sqrt{x'(t)^2+y'(t)^2}\,dt",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "polar_cartesian_conversion": {
        "answer_type": "expression",
        "parameters": {
            "r": p("expression", "극좌표 반지름 또는 극곡선 r(theta)."),
            "theta": p("expression", "극각 theta."),
        },
        "text": "극좌표 (r,theta)=({{ r }},{{ theta }})를 직교좌표로 변환하시오.",
        "latex": r"x=r\cos\theta,\quad y=r\sin\theta",
        "builder_cas": "(r*cos(theta), r*sin(theta))",
        "answer_cas": "(r*cos(theta), r*sin(theta))",
        "answer_latex": r"(r\cos\theta,r\sin\theta)",
        "validators": ["symbolic_equivalence"],
    },
    "polar_symmetry_classification": {
        "answer_type": "classification",
        "parameters": {
            "r_theta": p("expression", "극곡선 r=f(theta)."),
        },
        "text": "극곡선 r={{ r_theta }}의 대칭성을 판정하시오.",
        "latex": r"r=f(\theta)",
        "builder_cas": "classify_polar_symmetry(r_theta,theta)",
        "answer_cas": "classify_polar_symmetry(r_theta,theta)",
        "answer_latex": r"\text{polar symmetry class}",
        "validators": ["symbolic_equivalence"],
    },
    "polar_curve_identification": {
        "answer_type": "classification",
        "parameters": {
            "r_theta": p("expression", "분류할 극곡선."),
        },
        "text": "극곡선 r={{ r_theta }}의 종류를 분류하시오.",
        "latex": r"r=f(\theta)",
        "builder_cas": "classify_polar_curve(r_theta,theta)",
        "answer_cas": "classify_polar_curve(r_theta,theta)",
        "answer_latex": r"\text{circle/cardioid/limacon/rose/...}",
        "validators": ["symbolic_equivalence"],
    },
    "polar_area_calculation": {
        "answer_type": "scalar",
        "parameters": {
            "r_theta": p("expression", "극곡선 r=f(theta)."),
            "a": p("real", "각 구간 시작값."),
            "b": p("real", "각 구간 끝값."),
        },
        "text": "극곡선 r={{ r_theta }}가 {{ a }}<=theta<={{ b }}에서 만드는 영역의 넓이를 구하시오.",
        "latex": r"A=\frac12\int_a^b r^2\,d\theta",
        "builder_cas": "integrate(r_theta**2/2,(theta,a,b))",
        "answer_cas": "integrate(r_theta**2/2,(theta,a,b))",
        "answer_latex": r"\frac12\int_a^b r^2\,d\theta",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "polar_curve_intersection": {
        "answer_type": "set",
        "parameters": {
            "r1": p("expression", "첫 번째 극곡선."),
            "r2": p("expression", "두 번째 극곡선."),
        },
        "text": "극곡선 r={{ r1 }}과 r={{ r2 }}의 교점을 구하시오. 원점 교점도 확인하시오.",
        "latex": r"r_1(\theta)=r_2(\theta)",
        "builder_cas": "polar_intersections(r1,r2,theta)",
        "answer_cas": "polar_intersections(r1,r2,theta)",
        "answer_latex": r"\{(r,\theta)\}",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "area_between_polar_curves": {
        "answer_type": "scalar",
        "parameters": {
            "r_outer": p("expression", "바깥쪽 극곡선."),
            "r_inner": p("expression", "안쪽 극곡선."),
            "a": p("real", "각 구간 시작값."),
            "b": p("real", "각 구간 끝값."),
        },
        "text": "r={{ r_outer }}와 r={{ r_inner }} 사이 영역의 넓이를 {{ a }}<=theta<={{ b }}에서 구하시오.",
        "latex": r"A=\frac12\int_a^b(r_{\rm out}^2-r_{\rm in}^2)\,d\theta",
        "builder_cas": "integrate((r_outer**2-r_inner**2)/2,(theta,a,b))",
        "answer_cas": "integrate((r_outer**2-r_inner**2)/2,(theta,a,b))",
        "answer_latex": r"\frac12\int_a^b(r_{\rm out}^2-r_{\rm in}^2)\,d\theta",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "polar_arc_length_calculation": {
        "answer_type": "scalar",
        "parameters": {
            "r_theta": p("expression", "극곡선."),
            "a": p("real", "각 구간 시작값."),
            "b": p("real", "각 구간 끝값."),
        },
        "text": "극곡선 r={{ r_theta }}의 {{ a }}<=theta<={{ b }}에서의 호의 길이를 구하시오.",
        "latex": r"L=\int_a^b\sqrt{r^2+(dr/d\theta)^2}\,d\theta",
        "builder_cas": "integrate(sqrt(r_theta**2+diff(r_theta,theta)**2),(theta,a,b))",
        "answer_cas": "integrate(sqrt(r_theta**2+diff(r_theta,theta)**2),(theta,a,b))",
        "answer_latex": r"\int_a^b\sqrt{r^2+(r')^2}\,d\theta",
        "validators": ["symbolic_equivalence"],
    },
    "polar_tangent_slope_calculation": {
        "answer_type": "expression",
        "parameters": {
            "r_theta": p("expression", "극곡선."),
            "theta0": p("real", "기울기를 계산할 각."),
        },
        "text": "극곡선 r={{ r_theta }}에서 theta={{ theta0 }}일 때 접선의 기울기 dy/dx를 구하시오.",
        "latex": r"\frac{dy}{dx}=\frac{r'\sin\theta+r\cos\theta}{r'\cos\theta-r\sin\theta}",
        "builder_cas": "(diff(r_theta,theta)*sin(theta)+r_theta*cos(theta))/(diff(r_theta,theta)*cos(theta)-r_theta*sin(theta))",
        "answer_cas": "((diff(r_theta,theta)*sin(theta)+r_theta*cos(theta))/(diff(r_theta,theta)*cos(theta)-r_theta*sin(theta))).subs(theta,theta0)",
        "answer_latex": r"\left.\frac{r'\sin\theta+r\cos\theta}{r'\cos\theta-r\sin\theta}\right|_{\theta=\theta_0}",
        "validators": ["symbolic_equivalence"],
    },
    "pole_tangent_calculation": {
        "answer_type": "expression",
        "parameters": {"r_theta": p("expression", "극을 지나는 극곡선.")},
        "text": "극곡선 r={{ r_theta }}가 극(r=0)을 지나는 지점에서 접선의 방향을 구하시오.",
        "latex": r"r(\theta_0)=0",
        "builder_cas": "pole_tangent_angles(r_theta,theta)",
        "answer_cas": "pole_tangent_angles(r_theta,theta)",
        "answer_latex": r"\theta=\theta_0",
        "validators": ["symbolic_equivalence"],
    },
    "conic_type_classification": {
        "answer_type": "classification",
        "parameters": {
            "A": p("real", "x^2 계수."),
            "B": p("real", "xy 계수."),
            "C": p("real", "y^2 계수."),
            "D": p("real", "x 계수."),
            "E": p("real", "y 계수."),
            "F": p("real", "상수항."),
        },
        "text": "Ax^2+Bxy+Cy^2+Dx+Ey+F=0에서 A={{ A }}, B={{ B }}, C={{ C }}, D={{ D }}, E={{ E }}, F={{ F }}일 때 원뿔곡선의 종류를 분류하시오.",
        "latex": r"Ax^2+Bxy+Cy^2+Dx+Ey+F=0",
        "builder_cas": "classify_conic(A,B,C,D,E,F)",
        "answer_cas": "classify_conic(A,B,C,D,E,F)",
        "answer_latex": r"\text{parabola/ellipse/hyperbola}",
        "validators": ["symbolic_equivalence"],
    },
    "conic_element_calculation": {
        "answer_type": "expression",
        "parameters": {"standard_equation": p("equation", "표준형 원뿔곡선 방정식.")},
        "text": "원뿔곡선 {{ standard_equation }}의 중심/꼭짓점/초점 등 주요 요소를 구하시오.",
        "latex": r"\text{conic standard form}",
        "builder_cas": "extract_conic_elements(standard_equation)",
        "answer_cas": "extract_conic_elements(standard_equation)",
        "answer_latex": r"\text{conic elements}",
        "validators": ["symbolic_equivalence"],
    },
    "general_to_standard_form_conversion": {
        "answer_type": "equation",
        "parameters": {"general_equation": p("equation", "일반형 원뿔곡선 방정식.")},
        "text": "원뿔곡선 {{ general_equation }}을 완전제곱을 이용하여 표준형으로 변환하시오.",
        "latex": r"Ax^2+Cy^2+Dx+Ey+F=0",
        "builder_cas": "conic_to_standard_form(general_equation)",
        "answer_cas": "conic_to_standard_form(general_equation)",
        "answer_latex": r"\text{standard conic equation}",
        "validators": ["symbolic_equivalence"],
    },

    # ------------------------------------------------------------------------
    # Chapter 10: Sequences and Series
    # ------------------------------------------------------------------------
    "sequence_convergence_check": {
        "answer_type": "boolean",
        "parameters": {"a_n": p("expression", "일반항 a_n.")},
        "text": "수열 a_n={{ a_n }}이 수렴하는지 판정하시오.",
        "latex": r"\lim_{n\to\infty}a_n",
        "builder_cas": "sequence_converges(a_n,n)",
        "answer_cas": "sequence_converges(a_n,n)",
        "answer_latex": r"\mathrm{True}\ \text{or}\ \mathrm{False}",
        "validators": ["numeric_tolerance", "symbolic_equivalence"],
    },
    "sequence_limit_calculation": {
        "answer_type": "scalar",
        "parameters": {"a_n": p("expression", "일반항 a_n.")},
        "text": "수열 a_n={{ a_n }}의 n->infinity 극한을 구하시오.",
        "latex": r"\lim_{n\to\infty}a_n",
        "builder_cas": "limit(a_n,n,oo)",
        "answer_cas": "limit(a_n,n,oo)",
        "answer_latex": r"\lim_{n\to\infty}a_n",
        "validators": ["numeric_tolerance", "symbolic_equivalence"],
    },
    "geometric_sequence_limit_classification": {
        "answer_type": "classification",
        "parameters": {"r": p("real", "등비수열 r^n의 공비.", min_=-3, max_=3)},
        "text": "수열 a_n=({{ r }})^n의 수렴/발산과 극한을 분류하시오.",
        "latex": r"a_n=r^n",
        "builder_cas": "classify_geometric_sequence_limit(r)",
        "answer_cas": "classify_geometric_sequence_limit(r)",
        "answer_latex": r"\text{convergent/divergent}",
        "validators": ["numeric_tolerance", "symbolic_equivalence"],
    },
    "monotonicity_boundedness_classification": {
        "answer_type": "classification",
        "parameters": {"a_n": p("expression", "일반항 a_n.")},
        "text": "수열 a_n={{ a_n }}의 단조성과 유계성을 분류하시오.",
        "latex": r"a_n",
        "builder_cas": "classify_monotonicity_boundedness(a_n,n)",
        "answer_cas": "classify_monotonicity_boundedness(a_n,n)",
        "answer_latex": r"\text{increasing/decreasing/bounded/...}",
        "validators": ["symbolic_equivalence"],
    },
    "monotonic_theorem_application": {
        "answer_type": "boolean",
        "parameters": {"a_n": p("expression", "단조수열 정리를 적용할 수열.")},
        "text": "수열 a_n={{ a_n }}에 단조수열 정리를 적용하여 수렴을 보일 수 있는지 판정하시오.",
        "latex": r"\text{monotone}+\text{bounded}\Rightarrow\text{convergent}",
        "builder_cas": "monotonic_theorem_applies(a_n,n)",
        "answer_cas": "monotonic_theorem_applies(a_n,n)",
        "answer_latex": r"\mathrm{True}\ \text{or}\ \mathrm{False}",
        "validators": ["symbolic_equivalence"],
    },
    "recursive_sequence_limit_calculation": {
        "answer_type": "scalar",
        "parameters": {
            "F_L": p("expression", "점화식 a_(n+1)=F(a_n)의 F(L)."),
            "initial": p("real", "초기값."),
        },
        "text": "a_(n+1)=F(a_n), a_1={{ initial }}이고 수렴이 보장된다고 할 때 L=F(L)을 이용하여 극한 L을 구하시오. F(L)={{ F_L }}",
        "latex": r"L=F(L)",
        "builder_cas": "solve(Eq(L,F_L),L)",
        "answer_cas": "select_valid_recursive_limit(solve(Eq(L,F_L),L),initial)",
        "answer_latex": r"L",
        "validators": ["symbolic_equivalence"],
    },
    "geometric_series_sum_calculation": {
        "answer_type": "scalar",
        "parameters": {
            "a": p("real", "기하급수 첫 항.", min_=-10, max_=10),
            "r": p("real", "공비, |r|<1.", min_=-0.9, max_=0.9),
        },
        "text": "기하급수 sum a*r^(n-1)에서 a={{ a }}, r={{ r }}일 때 합을 구하시오.",
        "latex": r"\sum_{n=1}^{\infty}ar^{n-1}=\frac{a}{1-r}",
        "builder_cas": "a/(1-r)",
        "answer_cas": "a/(1-r)",
        "answer_latex": r"\frac{a}{1-r}",
        "validators": ["symbolic_equivalence"],
    },
    "divergence_test_application": {
        "answer_type": "boolean",
        "parameters": {"a_n": p("expression", "급수의 일반항.")},
        "text": "급수 sum({{ a_n }})에 발산판정법을 적용하여 발산을 확정할 수 있는지 판정하시오.",
        "latex": r"\lim_{n\to\infty}a_n\neq0\Rightarrow\sum a_n\text{ diverges}",
        "builder_cas": "limit(a_n,n,oo) != 0",
        "answer_cas": "limit(a_n,n,oo) != 0",
        "answer_latex": r"\mathrm{True}\ \text{or}\ \mathrm{False}",
        "validators": ["symbolic_equivalence"],
    },
    "telescoping_series_calculation": {
        "answer_type": "scalar",
        "parameters": {"a_n": p("expression", "망원급수의 일반항.")},
        "text": "망원급수 sum({{ a_n }}, n=1..infinity)의 합을 구하시오.",
        "latex": r"\sum_{n=1}^{\infty}a_n",
        "builder_cas": "summation(a_n,(n,1,oo))",
        "answer_cas": "summation(a_n,(n,1,oo))",
        "answer_latex": r"\sum_{n=1}^{\infty}a_n",
        "validators": ["symbolic_equivalence"],
    },
    "integral_test_application": {
        "answer_type": "boolean",
        "parameters": {"a_n": p("expression", "양항 급수의 일반항.")},
        "text": "급수 sum({{ a_n }})에 적분판정법을 적용하여 수렴 여부를 판정하시오.",
        "latex": r"\sum a_n\text{ converges}\iff\int_1^\infty f(x)\,dx\text{ converges}",
        "builder_cas": "integral_test_result(a_n,n,x)",
        "answer_cas": "integral_test_result(a_n,n,x)",
        "answer_latex": r"\mathrm{True}\ \text{or}\ \mathrm{False}",
        "validators": ["symbolic_equivalence"],
    },
    "p_series_classification": {
        "answer_type": "classification",
        "parameters": {"p": p("real", "p급수의 지수.", min_=0.1, max_=5)},
        "text": "p={{ p }}일 때 p급수 sum 1/n^p의 수렴/발산을 판정하시오.",
        "latex": r"\sum_{n=1}^{\infty}\frac1{n^p}",
        "builder_cas": "'convergent' if p>1 else 'divergent'",
        "answer_cas": "'convergent' if p>1 else 'divergent'",
        "answer_latex": r"p>1\Rightarrow\text{convergent}",
        "validators": ["symbolic_equivalence"],
    },
    "remainder_estimation": {
        "answer_type": "numerical_approximation",
        "parameters": {
            "f_x": p("expression", "적분판정법 조건을 만족하는 감소 양함수."),
            "N": p("integer", "부분합 절단 지점.", min_=1, max_=100),
        },
        "text": "적분판정법의 나머지 추정을 사용하여 N={{ N }} 이후의 오차 R_N의 상한을 구하시오. f(x)={{ f_x }}",
        "latex": r"R_N\le\int_N^\infty f(x)\,dx",
        "builder_cas": "integrate(f_x,(x,N,oo))",
        "answer_cas": "integrate(f_x,(x,N,oo))",
        "answer_latex": r"\int_N^\infty f(x)\,dx",
        "validators": ["symbolic_equivalence"],
    },
    "direct_comparison_test_application": {
        "answer_type": "classification",
        "parameters": {
            "a_n": p("expression", "판정할 양항 급수의 일반항."),
            "b_n": p("expression", "비교 기준 급수의 일반항."),
        },
        "text": "a_n={{ a_n }}, b_n={{ b_n }}에 직접비교판정법을 적용하여 sum a_n의 수렴/발산을 판정하시오.",
        "latex": r"0\le a_n\le b_n",
        "builder_cas": "direct_comparison_result(a_n,b_n,n)",
        "answer_cas": "direct_comparison_result(a_n,b_n,n)",
        "answer_latex": r"\text{convergent/divergent}",
        "validators": ["symbolic_equivalence"],
    },
    "limit_comparison_test_application": {
        "answer_type": "classification",
        "parameters": {
            "a_n": p("expression", "판정할 급수 일반항."),
            "b_n": p("expression", "비교 급수 일반항."),
        },
        "text": "a_n={{ a_n }}, b_n={{ b_n }}에 대해 극한비교판정법으로 sum a_n의 수렴/발산을 판정하시오.",
        "latex": r"\lim_{n\to\infty}\frac{a_n}{b_n}=c,\quad0<c<\infty",
        "builder_cas": "limit_comparison_result(a_n,b_n,n)",
        "answer_cas": "limit_comparison_result(a_n,b_n,n)",
        "answer_latex": r"\text{convergent/divergent}",
        "validators": ["symbolic_equivalence"],
    },
    "comparison_series_construction": {
        "answer_type": "classification",
        "parameters": {"a_n": p("expression", "지배항을 분석할 급수 일반항.")},
        "text": "급수 a_n={{ a_n }}의 수렴성 판정을 위해 적절한 비교급수 유형을 선택하시오.",
        "latex": r"a_n\sim b_n",
        "builder_cas": "choose_comparison_series(a_n,n)",
        "answer_cas": "choose_comparison_series(a_n,n)",
        "answer_latex": r"\text{p-series/geometric/...}",
        "validators": ["symbolic_equivalence"],
    },
    "alternating_series_test_application": {
        "answer_type": "boolean",
        "parameters": {"b_n": p("expression", "교대급수의 양의 크기 b_n.")},
        "text": "교대급수 sum (-1)^(n-1)b_n, b_n={{ b_n }}에 교대급수판정법을 적용하여 수렴하는지 판정하시오.",
        "latex": r"\sum(-1)^{n-1}b_n",
        "builder_cas": "alternating_series_test(b_n,n)",
        "answer_cas": "alternating_series_test(b_n,n)",
        "answer_latex": r"\mathrm{True}\ \text{or}\ \mathrm{False}",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "alternating_series_error_estimation": {
        "answer_type": "numerical_approximation",
        "parameters": {
            "b_n": p("expression", "감소하는 교대급수의 양의 항."),
            "N": p("integer", "부분합 항수.", min_=1, max_=100),
        },
        "text": "교대급수의 N={{ N }}번째 부분합을 사용했을 때 오차의 상한을 구하시오. b_n={{ b_n }}",
        "latex": r"|R_N|\le b_{N+1}",
        "builder_cas": "b_n.subs(n,N+1)",
        "answer_cas": "b_n.subs(n,N+1)",
        "answer_latex": r"b_{N+1}",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "absolute_conditional_classification": {
        "answer_type": "classification",
        "parameters": {"a_n": p("expression", "부호가 변할 수 있는 급수 일반항.")},
        "text": "급수 sum({{ a_n }})가 절대수렴, 조건수렴, 발산 중 어느 것인지 분류하시오.",
        "latex": r"\sum a_n,\quad\sum|a_n|",
        "builder_cas": "classify_absolute_conditional(a_n,n)",
        "answer_cas": "classify_absolute_conditional(a_n,n)",
        "answer_latex": r"\text{absolute/conditional/divergent}",
        "validators": ["symbolic_equivalence", "numeric_tolerance"],
    },
    "ratio_test_application": {
        "answer_type": "classification",
        "parameters": {"a_n": p("expression", "비판정법을 적용할 급수 일반항.")},
        "text": "급수 sum({{ a_n }})에 비판정법을 적용하여 수렴/발산/판정불능을 분류하시오.",
        "latex": r"L=\lim_{n\to\infty}\left|\frac{a_{n+1}}{a_n}\right|",
        "builder_cas": "ratio_test_result(a_n,n)",
        "answer_cas": "ratio_test_result(a_n,n)",
        "answer_latex": r"L<1,\ L>1,\ L=1",
        "validators": ["symbolic_equivalence"],
    },
    "root_test_application": {
        "answer_type": "classification",
        "parameters": {"a_n": p("expression", "근판정법을 적용할 급수 일반항.")},
        "text": "급수 sum({{ a_n }})에 근판정법을 적용하여 수렴/발산/판정불능을 분류하시오.",
        "latex": r"L=\lim_{n\to\infty}\sqrt[n]{|a_n|}",
        "builder_cas": "root_test_result(a_n,n)",
        "answer_cas": "root_test_result(a_n,n)",
        "answer_latex": r"L<1,\ L>1,\ L=1",
        "validators": ["symbolic_equivalence"],
    },
    "test_selection_reasoning": {
        "answer_type": "classification",
        "parameters": {"a_n": p("expression", "판정법 선택 대상 급수 일반항.")},
        "text": "급수 sum({{ a_n }})에 가장 적절한 수렴판정법을 선택하시오.",
        "latex": r"\sum a_n",
        "builder_cas": "choose_series_test(a_n,n)",
        "answer_cas": "choose_series_test(a_n,n)",
        "answer_latex": r"\text{ratio/root/comparison/integral/...}",
        "validators": ["symbolic_equivalence"],
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", value).strip("_")


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def choose_answer_type(concept: dict[str, Any], problem_type: str) -> str:
    bp_answer = BLUEPRINTS[problem_type]["answer_type"]
    supported = concept["generation_profile"].get("supported_answer_types", [])
    # 일부 problem_type은 concept catalog가 넓은 answer_type 묶음만 제공하므로
    # blueprint가 더 구체적인 타입(set 등)을 사용할 수 있게 허용한다.
    return bp_answer


def make_distractor_rules(concept: dict[str, Any]) -> list[dict[str, Any]]:
    rules = []
    for i, m in enumerate(concept.get("misconceptions", []), start=1):
        rules.append(
            {
                "rule_id": f"{slug(concept['concept_id'])}.misconception.{i}",
                "misconception_id": m["misconception_id"],
                "transformation": m.get("diagnosis_tag", "misconception_transform"),
                "validator": "distractor_validity_check",
            }
        )
    return rules


def build_template(catalog: dict[str, Any], concept: dict[str, Any], problem_type: str) -> dict[str, Any]:
    bp = BLUEPRINTS[problem_type]
    gp = concept["generation_profile"]
    diff = gp.get("difficulty_range", {"min": 1, "max": 5})
    dmin, dmax = diff["min"], diff["max"]
    dbase = (dmin + dmax) // 2

    formula_ids = [f["formula_id"] for f in concept.get("formulas", [])]
    validators = unique(bp.get("validators", gp.get("recommended_validators", [])))

    return {
        "schema_version": "1.0.0",
        "object_type": "problem_template",
        "template_id": f"{catalog['subject']['subject_id']}.{catalog['unit']['unit_id']}.{concept['concept_id']}.{problem_type}.v1",
        "template_version": "1.0.0",
        "status": "draft",
        "taxonomy": {
            "subject_id": catalog["subject"]["subject_id"],
            "subject_name_ko": catalog["subject"]["name_ko"],
            "unit_id": catalog["unit"]["unit_id"],
            "unit_name_ko": catalog["unit"]["name_ko"],
            "concept_ids": [concept["concept_id"]],
            "formula_ids": formula_ids,
            "tags": concept.get("tags", []),
        },
        "classification": {
            "problem_type": problem_type,
            "answer_type": choose_answer_type(concept, problem_type),
            "difficulty": {"base": dbase, "min": dmin, "max": dmax},
            "generation_strategy": "forward_generation",
            "language": catalog.get("language", "ko-KR"),
        },
        "parameters": copy.deepcopy(bp.get("parameters", {})),
        "parameter_dependencies": [],
        "constraints": [],
        "problem_builder": {
            "text_templates_ko": [bp["text"]],
            "latex_templates": [bp.get("latex", "")],
            "cas_template": bp.get("builder_cas", ""),
            "context_templates": [],
            "render_engine": "jinja2",
        },
        "answer_spec": {
            "answer_type": choose_answer_type(concept, problem_type),
            "cas_template": bp.get("answer_cas", ""),
            "latex_template": bp.get("answer_latex", ""),
            "canonicalization": {
                "method": "simplify",
                "exact_value_preferred": True,
            },
            "equivalence": {
                "method": "symbolic_equivalence",
                "tolerance": None,
            },
            "required_checks": validators,
        },
        "solution_spec": {
            "solution_strategy": bp.get("solution_strategy", "formula_substitution"),
            "solution_plan": [
                {
                    "step": 1,
                    "action": "문제에 주어진 값을 확인하고 적용 공식을 선택한다.",
                    "formula_id": formula_ids[0] if formula_ids else None,
                    "cas_expression": bp.get("builder_cas", ""),
                },
                {
                    "step": 2,
                    "action": "CAS 식으로 계산한 뒤 결과를 정규화한다.",
                    "formula_id": None,
                    "cas_expression": bp.get("answer_cas", ""),
                },
            ],
            "explanation_policy": {
                "use_verified_answer_only": True,
                "use_knowledge_base": True,
                "allow_llm_calculation": False,
            },
        },
        "validation": {
            "validators": [{"name": v, "required": True, "config": {}} for v in validators],
            "generation_max_attempts": 100,
            "all_required_must_pass": True,
        },
        "distractor_rules": make_distractor_rules(concept),
        "quality_rules": {
            "duplicate_check": True,
            "answer_complexity_check": True,
            "ambiguity_check": True,
            "maximum_answer_complexity": None,
            "maximum_denominator": None,
            "allow_decimal_answer": False,
            "minimum_distinct_parameter_sets": 20,
        },
        "storage_policy": {
            "save_failed_generations": True,
            "save_validation_trace": True,
            "save_seed": True,
            "save_template_snapshot": True,
        },
        "metadata": {
            "created_at": None,
            "updated_at": None,
            "created_by": "generate_calc1_problem_templates.py",
            "reviewed_by": None,
            "review_status": "not_reviewed",
            "notes": "",
        },
    }


def validate_catalog_coverage(catalog: dict[str, Any]) -> list[str]:
    missing = []
    for concept in catalog.get("concepts", []):
        gp = concept.get("generation_profile", {})
        if not gp.get("enabled", False):
            continue
        for problem_type in gp.get("supported_problem_types", []):
            if problem_type not in BLUEPRINTS:
                missing.append(f"{concept['concept_id']}::{problem_type}")
    return missing


def generate_catalog(catalog_path: Path, output_dir: Path) -> list[Path]:
    catalog = load_json(catalog_path)
    missing = validate_catalog_coverage(catalog)
    if missing:
        raise RuntimeError("Missing blueprints:\n  - " + "\n  - ".join(missing))

    unit_dir = output_dir / catalog["unit"]["unit_id"]
    written = []
    manifest = []

    for concept in catalog.get("concepts", []):
        gp = concept.get("generation_profile", {})
        if not gp.get("enabled", False):
            continue

        for problem_type in gp.get("supported_problem_types", []):
            data = build_template(catalog, concept, problem_type)
            filename = f"{concept['order']:02d}_{slug(concept['concept_id'])}__{slug(problem_type)}.json"
            path = unit_dir / filename
            dump_json(data, path)
            written.append(path)
            manifest.append(
                {
                    "template_id": data["template_id"],
                    "concept_id": concept["concept_id"],
                    "problem_type": problem_type,
                    "file": filename,
                }
            )

    dump_json(
        {
            "subject_id": catalog["subject"]["subject_id"],
            "unit_id": catalog["unit"]["unit_id"],
            "template_count": len(written),
            "templates": manifest,
        },
        unit_dir / "manifest.json",
    )
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ProblemTemplate JSON files for Calculus I concept catalogs."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="One concept catalog JSON or a directory containing calculus concept catalogs.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("data/problem_templates/calculus_1"),
    )
    parser.add_argument(
        "--chapters",
        nargs="*",
        type=int,
        default=None,
        help="Directory input일 때 생성할 chapter order 목록. 예: --chapters 9 10",
    )
    args = parser.parse_args()

    if args.input.is_file():
        catalog_files = [args.input]
    elif args.input.is_dir():
        catalog_files = sorted(args.input.glob("*.json"))
        if args.chapters:
            selected = []
            for path in catalog_files:
                try:
                    catalog = load_json(path)
                    if catalog.get("unit", {}).get("order") in args.chapters:
                        selected.append(path)
                except Exception:
                    continue
            catalog_files = selected
    else:
        raise FileNotFoundError(args.input)

    total = []
    for catalog_path in catalog_files:
        written = generate_catalog(catalog_path, args.output)
        total.extend(written)
        print(f"[OK] {catalog_path.name}: {len(written)} templates")

    print()
    print(f"Generated {len(total)} templates in total: {args.output.resolve()}")


if __name__ == "__main__":
    main()
