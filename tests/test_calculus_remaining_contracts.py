"""원본 입력에서 유도한 수작업 기준값과 조건 경계/오답을 검사한다."""
import pytest
import sympy as s
from scripts.problems.calculus_1.calculus_1_remaining_profiles import calculate,validate,PROFILES
x,y=s.symbols('x y',real=True)
P={'a':2,'b':3,'c':1,'k':-1,'N':3,'x':x,'y':y}
MANUAL={
 'domain_range_identification':s.S.Reals,
 'vertical_line_test_check':False,
 'piecewise_evaluation':-2,
 'domain_segment_identification':1,
 'monotonic_interval_identification':s.Interval.open(1,s.oo),
 'domain_by_family':s.Complement(s.S.Reals,s.FiniteSet(1)),
 'domain_of_combination':s.Complement(s.Interval(1,s.oo),s.FiniteSet(3)),
 'inverse_function_derivation':(x-3)/2,
 'change_of_base':3,
 'inverse_trig_evaluation':-s.pi/2,
 'trig_domain_range_period_identification':s.pi,
 'limit_numeric_estimation':5,
 'infinite_limit_identification':False,
 'ivt_condition_check':True,
 'root_interval_location':s.Interval(0,3),
 'limit_at_infinity_calculation':s.Rational(2,3),
 'implicit_differentiation':-x/(2*y),
 'implicit_second_derivative':-3/(4*y**3),
 'tangent_normal_line_derivation':s.Eq(y,5-(x-1)/4,evaluate=False),
 'inverse_trig_derivative_calculation':2/(1+4*x*x),
 'related_rates_solving':-48*s.pi,
 'motion_reconstruction':x*x+3*x+1,
 'riemann_sum_calculation':s.Rational(28,27),
 'midpoint_rule_estimation':s.Rational(35,54),
 'integral_inequality_proof':True,
 'variable_bound_integral_derivative':4*x**3+6*x,
 'displacement_and_distance_calculation':2,
 'cylindrical_shell_volume_calculation':4*s.pi/3,
 'partial_fraction_decomposition':1/(2*x)-1/(2*(x+2)),
 'improper_integral_evaluation':s.Rational(1,2),
 'arc_length_calculation':3*s.sqrt(5),
 'surface_area_calculation':18*s.pi*s.sqrt(5),
 'hydrostatic_force_calculation':9,
 'pappus_theorem_application':40*s.pi**2,
 'numeric_integration_from_data':5,
 'cardiac_output_calculation':s.Rational(2,5),
 'parameter_elimination':s.Eq(y,3*x/2+1,evaluate=False),
 'parametric_tangent_slope_calculation':-3,
 'parametric_second_derivative_calculation':s.Rational(3,2),
 'parametric_area_calculation':2,
 'parametric_arc_length_calculation':s.sqrt(13),
 'parametric_surface_area_calculation':3*s.pi*s.sqrt(13),
 'polar_cartesian_conversion':0,
 'polar_area_calculation':s.pi,
 'polar_curve_intersection':s.pi/3,
 'area_between_polar_curves':21*s.pi/4,
 'polar_arc_length_calculation':s.pi,
 'conic_type_classification':'쌍곡선',
 'conic_element_calculation':2,
 'sequence_limit_calculation':s.Rational(2,3),
 'geometric_sequence_limit_classification':'발산(진동)',
 'recursive_sequence_limit_calculation':2,
 'telescoping_series_calculation':2,
 'remainder_estimation':s.Rational(1,3),
 'alternating_series_error_estimation':s.Rational(1,4),
 'absolute_conditional_classification':'절대수렴',
 'ratio_test_application':'수렴',
 'root_test_application':'수렴',
}

@pytest.mark.parametrize('name',sorted(MANUAL))
def test_manual_reference(name):
    expected=MANUAL[name]
    assert validate(expected,P,{'operation':name})
    actual=calculate(P,name)
    if isinstance(expected,(s.Set,s.Equality)):assert actual==expected
    elif isinstance(expected,(str,bool)):assert actual==expected
    else:assert s.simplify(actual-expected)==0

@pytest.mark.parametrize('name',sorted(PROFILES))
def test_outside_contract_rejected(name):
    with pytest.raises(ValueError):calculate({**P,'a':1000},name)
    with pytest.raises(ValueError):calculate({**P,'a':True},name)
    with pytest.raises(ValueError):calculate({**P,'y':x},name)

@pytest.mark.parametrize('name',['ratio_test_application','root_test_application'])
@pytest.mark.parametrize('aa,bb,expected',[(1,2,'수렴'),(2,1,'발산'),(2,2,'판정 불가')])
def test_inconclusive_is_not_success(name,aa,bb,expected):
    assert calculate({**P,'a':aa,'b':bb},name)==expected
    assert not validate('수렴' if expected!='수렴' else '발산',{**P,'a':aa,'b':bb},{'operation':name})


def test_conditions_and_open_boundaries():
    assert calculate({**P,'a':1,'b':2},'ivt_condition_check')
    assert not calculate({**P,'a':5,'b':1},'ivt_condition_check')
    assert calculate({**P,'a':2},'direct_comparison_test_application')
    assert not calculate({**P,'a':1},'direct_comparison_test_application')
    assert not calculate({**P,'c':0},'evt_condition_check')
    assert calculate({**P,'c':2},'evt_condition_check')
    assert not validate(s.Interval(1,s.oo),P,{'operation':'monotonic_interval_identification'})
    assert not validate(s.S.Reals,P,{'operation':'domain_by_family'})


def test_antiderivative_has_correct_domain_and_allows_constant():
    name='trig_substitution_integral_calculation'
    answer=s.asin(x/2)
    assert validate(answer+7,P,{'operation':name})
    assert not validate(answer+x,P,{'operation':name})
    assert s.diff(answer,x).subs(x,0)==s.Rational(1,2)


def test_equation_allows_only_constant_multiple():
    name='parameter_elimination';cfg={'operation':name}
    assert validate(s.Eq(2*y,3*x+2,evaluate=False),P,cfg)
    assert not validate(s.Eq(x*(y-3*x/2-1),0,evaluate=False),P,cfg)


def test_unknown_or_string_executable_inputs_fail():
    with pytest.raises(ValueError):calculate(P,'unregistered')
    with pytest.raises(ValueError):calculate({**P,'a':'2'},'arc_length_calculation')
    assert not validate('sqrt(13)',P,{'operation':'parametric_arc_length_calculation'})
