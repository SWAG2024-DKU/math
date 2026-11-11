"""미적분 2 전체 생성/오답/수작업 기준/보존/전제조건 검증."""
from pathlib import Path
from copy import deepcopy
import json
import pytest
import sympy as s
from app.schemas.problem_template import ProblemTemplate
from scripts.problems.calculus_2.calculus_2_rule_profiles import PROFILES,calculate,validate,SYMBOLS,linear_ode
from scripts.problems.common.problem_instance_generator import generate_problem_instance,_symbolic_values,_bind_subject_symbols
from scripts.problems.common import parameter_sampler,math_validators
from scripts.problems.calculus_2.review_calculus_2_rules import inspect_and_apply
ROOT=Path(__file__).resolve().parents[1]
TYPES=sorted(PROFILES)
X={name:s.Symbol(name,real=True) for name in SYMBOLS}
x,y,z,t=X['x'],X['y'],X['z'],X['t']
P={**X,'a':2,'b':3,'c':1,'d':-1,'k':-1,'N':2}

@pytest.fixture(scope='module')
def templates():
    out={}
    for path in (ROOT/'data/problem_templates/calculus_2').rglob('*.json'):
        item=ProblemTemplate.model_validate_json(path.read_bytes())
        if item.executable:out[item.classification.problem_type]=item
    assert set(out)==set(PROFILES)
    return out

@pytest.mark.parametrize('kind',TYPES)
@pytest.mark.parametrize('seed',[0,17,42])
def test_generate_all_types(kind,seed,templates):
    result=generate_problem_instance(templates[kind],seed=seed,max_attempts=40)
    assert result.instance['publishable'] is False
    assert result.instance['template_status']=='draft'
    assert all(row['passed'] for row in result.instance['validation_trace']['validators'])


def wrong(answer):
    if isinstance(answer,bool) or answer is s.true or answer is s.false:return not bool(answer)
    if isinstance(answer,str):return '잘못된 분류'
    if isinstance(answer,s.Set):return s.FiniteSet(100)
    if isinstance(answer,s.MatrixBase):
        bad=answer.copy();bad[0]+=1;return bad
    if isinstance(answer,(tuple,list,s.Tuple)):return tuple([wrong(answer[0]),*answer[1:]])
    if isinstance(answer,s.Equality):return s.Eq(answer.lhs,answer.rhs+1,evaluate=False)
    if isinstance(answer,s.core.relational.Relational):return s.Le(answer.lhs,answer.rhs)
    return answer+1

@pytest.mark.parametrize('kind',TYPES)
def test_wrong_answer_rejected(kind,templates):
    template=templates[kind];result=generate_problem_instance(template,seed=17,max_attempts=40)
    values=parameter_sampler.sample_parameters(template.parameters,seed=result.seed)
    symbols=_symbolic_values(template,values);values={**_bind_subject_symbols(values,symbols),**symbols}
    answer=math_validators.compute_expected_answer(template.answer_spec,values)
    report=math_validators.run_math_validators(wrong(answer),values,template.validation.validators,
        answer_type=template.answer_spec.answer_type,required_checks=template.answer_spec.required_checks,
        problem_type=template.classification.problem_type)
    assert not report.passed,kind

MANUAL={
 'common_series_recall':1+2*x+2*x*x,
 'series_convergence_interval_identification':s.Interval(-s.Rational(1,2),s.Rational(1,2),left_open=True),
 'endpoint_convergence_check':s.Interval(-s.Rational(1,2),s.Rational(1,2)),
 'cauchy_product_calculation':7,
 'taylor_coefficient_extraction':2,
 'binomial_series_expansion':1+2*x+x*x,
 'series_based_integration':x+x*x+s.Rational(2,3)*x**3,
 'series_based_limit_evaluation':1,
 'taylor_error_estimation':s.Rational(1,3),
 'required_degree_determination':5,
 'surface_area_of_revolution_about_x_axis':18*s.pi*s.sqrt(5),
 'surface_area_of_revolution_about_y_axis':9*s.pi*s.sqrt(5),
 'conic_polar_equation_construction':s.Eq(z,2/(3+s.cos(t)),evaluate=False),
 'vector_from_points_construction':s.Matrix([1,-2,1]),
 '3d_distance_midpoint_calculation':s.sqrt(14),
 'dot_product_calculation':-1,
 'cross_product_calculation':s.Matrix([-1,5,-13]),
 'area_via_cross_product':3,
 'parallelepiped_volume_calculation':6,
 'point_line_distance_calculation':s.sqrt(10),
 'parallel_planes_distance_calculation':5/s.sqrt(3),
 'vector_function_domain_calculation':s.Interval.open(3,s.oo),
 'vector_derivative_calculation':s.Matrix([2,12,12]),
 'vector_chain_rule_application':s.Matrix([4,12,0]),
 'vector_integral_calculation':s.Matrix([1,1,s.Rational(1,4)]),
 'vector_initial_value_problem':s.Matrix([2,s.Rational(3,2),s.Rational(1,3)]),
 'space_curve_arc_length_calculation':2*s.sqrt(14),
 'curvature_calculation':s.Rational(1,2),
 'projectile_position_construction':s.Matrix([2,3,0]),
 'acceleration_decomposition':18,
 'partial_derivative_calculation':4*x+3*y,
 'clairaut_theorem_verification':4*x+6*y,
 'tangent_plane_construction':s.Eq(z,4*x+6*y-5,evaluate=False),
 'linearization_estimation':7,
 'total_differential_estimation':5,
 'multivariable_chain_rule_application':4*t+12*t**3,
 'directional_derivative_calculation':5/s.sqrt(2),
 'critical_point_calculation':s.FiniteSet(s.Tuple(-1,1)),
 'constrained_optimization_solving':2,
 'double_integral_rectangle_calculation':15,
 'average_value_2d_calculation':s.Rational(5,2),
 'integration_order_swap':2,
 'polar_double_integral_calculation':24*s.pi,
 'triple_integral_setup':x+y+s.Rational(1,2),
 'triple_integral_calculation':18,
 'moment_of_inertia_calculation':26,
 'cylindrical_triple_integral_calculation':24*s.pi,
 'spherical_triple_integral_calculation':32*s.pi,
 'jacobian_calculation':6,
 'scalar_line_integral_calculation':s.sqrt(13),
 'vector_line_integral_calculation':s.Rational(13,2),
 'line_integral_via_potential':14,
 'greens_theorem_application':8*s.pi,
 'region_with_hole_line_integral':42*s.pi,
 'divergence_calculation':6,
 'curl_calculation':s.Matrix([0,0,5]),
 'surface_normal_calculation':s.Matrix([-2,-3,1])/s.sqrt(14),
 'scalar_surface_integral_calculation':48*s.pi,
 'flux_calculation':6,
 'divergence_theorem_application':32*s.pi,
 'region_with_cavity_flux':468*s.pi,
 'characteristic_equation_solving':s.Tuple(2,-3),
 'undetermined_coefficients_solving':-s.Rational(3,4),
 'variation_of_parameters_application':s.Rational(3,4),
 'period_frequency_calculation':2*s.pi*s.sqrt(s.Rational(2,3)),
 'amplitude_phase_conversion':s.sqrt(13),
 'forced_oscillation_solving':-s.cos(3*x)/5,
 'rlc_equation_construction':(-1-3*y-x)/2,
 'power_series_solution_construction':1-2*x*x+s.Rational(2,3)*x**4,
 'bessel_series_derivation':1-x*x+x**4/4,
}

@pytest.mark.parametrize('name',sorted(MANUAL))
def test_manual_reference(name):
    assert validate(MANUAL[name],P,{'operation':name})

@pytest.mark.parametrize('name',TYPES)
def test_reject_invalid_parameter_contract(name):
    with pytest.raises(ValueError):calculate({**P,'a':1000},name)
    with pytest.raises(ValueError):calculate({**P,'a':True},name)
    with pytest.raises(ValueError):calculate({**P,'z':x},name)


def test_repeat_migration_and_human_changes():
    raw=json.loads((ROOT/'data/generation_rules/calculus_2.json').read_text())
    updated,records=inspect_and_apply(raw)
    assert updated==raw
    assert len(records)==166 and all(r['executable'] for r in updated['rules'])
    modified=deepcopy(raw)
    row=next(r for r in modified['rules'] if r['problem_type']=='dot_product_calculation')
    row['parameter_spec']['a']['max']=5
    new,_=inspect_and_apply(modified)
    assert new==modified


def test_ode_residual_and_initial_values_independent():
    answer=calculate(P,'second_order_ivp_solving')
    assert s.simplify(linear_ode(P,answer))==0
    assert answer.subs(x,0)==1
    assert s.diff(answer,x).subs(x,0)==-1
    general=calculate(P,'homogeneous_general_solution_construction')
    assert s.simplify(linear_ode(P,general))==0
    assert not validate(general,P,{'operation':'second_order_ivp_solving'})
    resonance={**P,'b':2}
    answer=calculate(resonance,'forced_oscillation_solving')
    assert s.simplify(s.diff(answer,x,2)+4*answer-s.cos(2*x))==0
    assert not validate(s.cos(2*x),resonance,{'operation':'forced_oscillation_solving'})


def test_vectors_potential_and_theorem_direction():
    unit=calculate(P,'magnitude_and_unit_vector_calculation')
    assert s.simplify(unit.dot(unit))==1
    projection=calculate(P,'projection_calculation');v=s.Matrix([3,-2,-1]);u=s.Matrix([2,3,1])
    assert s.simplify((u-projection).dot(v))==0
    potential=calculate(P,'potential_function_construction')
    assert [s.diff(potential,v) for v in (x,y,z)]==[4*x,6*y,2*z]
    assert not validate(-42*s.pi,P,{'operation':'region_with_hole_line_integral'})
    assert not validate(-468*s.pi,P,{'operation':'region_with_cavity_flux'})
    # 일정한 발산의 적분값을 별도로 삼중적분한다.
    assert s.integrate(3,(z,0,1),(y,0,3),(x,0,2))==18


def test_equations_inequality_endpoint_and_boolean_fail_closed():
    assert not validate(s.Le(x*x+y*y,4),P,{'operation':'multivariable_domain_calculation'})
    assert not validate(s.Interval.open(-s.Rational(1,2),s.Rational(1,2)),P,{'operation':'endpoint_convergence_check'})
    assert not validate('true',P,{'operation':'conservativeness_test'})
    with pytest.raises(ValueError):calculate(P,'unregistered')
    assert calculate({**P,'d':0},'coplanarity_check')
    assert not calculate(P,'coplanarity_check')
