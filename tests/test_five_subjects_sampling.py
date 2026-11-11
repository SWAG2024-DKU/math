"""새 과목 샘플러/조건 검사와 선형대수 공통 계약의 동작 테스트."""
from copy import deepcopy
import pytest
import sympy as sp
from app.schemas.generation_rule import ParameterSpec, ConstraintSpec
from scripts.problems.common import parameter_sampler as s, constraint_evaluator as c


def sample(kind, seed=17, **options):
    raw={'type':kind,'min':-3,'max':3,**options}
    return s.sample_parameters({'value':ParameterSpec.model_validate(raw)},seed=seed)['value']


@pytest.mark.parametrize('kind',list(s.NEW_TYPE_SAMPLERS))
def test_seed_reproduces_new_types(kind):
    options={}
    if kind in ('numeric_data','statistical_dataset'):options['shape']={'size':8}
    assert sample(kind,**options)==sample(kind,**options)


@pytest.mark.parametrize('family',['polynomial','rational','exponential','logarithmic','trigonometric'])
def test_function_families(family):
    f=sample('expression',family=family,degree=3)
    x=sp.Symbol('x',real=True)
    assert f.free_symbols=={x}
    if family=='polynomial':
        polynomial=sp.Poly(f,x)
        assert polynomial.degree()==3
        assert all(-3<=coefficient<=3 for coefficient in polynomial.all_coeffs())


def test_derived_polynomial_and_parameter_order():
    params={
        'f':ParameterSpec(type='expression',variable='x',depends_on=['a'],
                          derived={'depends_on':['a'],'expression':'a*x**2 + sin(x)','engine':'sympy'}),
        'a':ParameterSpec(type='integer',min=2,max=2),
    }
    values=s.sample_parameters(params,seed=2);x=sp.Symbol('x',real=True)
    assert values['f']==2*x**2+sp.sin(x)


@pytest.mark.parametrize('kind,options',[
    ('expression',{'family':'unsupported'}),('expression',{'degree':9}),
    ('expression',{'variables':['x','y']}),('expression',{'variables':['x','x']}),
    ('interval',{'lower':2,'upper':1}),('interval',{'lower':1}),
    ('interval',{'left_open':'yes'}),('sequence',{'start':0}),
    ('integration_region',{'coordinate_system':'polar'}),
    ('differential_equation',{'order':3}),('differential_equation',{'variables':['t','x']}),
    ('probability_distribution',{'family':'normal','parameters':{'sigma':0}}),
    ('probability_distribution',{'family':'binomial','parameters':{'p':2}}),
    ('numeric_data',{'shape':{'size':10001}}),('numeric_data',{'data_family':'unknown','shape':{'size':2}}),
])
def test_invalid_sampler_options_fail(kind,options):
    with pytest.raises(s.ParameterSamplingError):sample(kind,**options)


def test_interval_dependency_and_open_ends():
    specs={'D':ParameterSpec(type='interval',lower='a',upper='b',depends_on=['a','b'],left_open=True),
           'a':ParameterSpec(type='integer',min=1,max=1),'b':ParameterSpec(type='integer',min=3,max=3)}
    assert s.sample_parameters(specs,seed=4)['D']==sp.Interval.Lopen(1,3)


@pytest.mark.parametrize('family',['geometric','p_series','arithmetic'])
def test_series_outcomes(family):
    seq=sample('sequence',family=family,min=1,max=1)
    assert c.is_series_convergent(seq)==(family!='arithmetic')


@pytest.mark.parametrize('family',['box','triangle'])
def test_valid_regions_and_tampered_boundary(family):
    region=sample('integration_region',family=family)
    assert c.is_valid_integration_region(region)
    bad=deepcopy(region);bounds=list(bad['bounds']);v,_,hi=bounds[0];bounds[0]=(v,hi,hi);bad['bounds']=bounds
    assert not c.is_valid_integration_region(bad)


@pytest.mark.parametrize('order',[1,2])
def test_ode_initial_conditions(order):
    ode=sample('differential_equation',order=order)
    assert c.has_valid_ode_conditions(ode)
    bad=deepcopy(ode);bad['initial_conditions']=[]
    assert not c.has_valid_ode_conditions(bad)


@pytest.mark.parametrize('family',['bernoulli','binomial','poisson','normal','uniform','exponential'])
def test_distribution_parameters(family):
    assert c.is_valid_probability_distribution(sample('probability_distribution',family=family))


def test_invalid_probability_and_finite_pmf():
    assert not c.is_valid_probability_distribution({'family':'normal','parameters':{'mu':0,'sigma':-1}})
    d={'family':'finite_discrete','outcomes':[0,1],'probabilities':[sp.Rational(1,3),sp.Rational(2,3)]}
    assert c.is_valid_probability_distribution(d)
    d['probabilities']=[sp.Rational(1,3),sp.Rational(1,3)]
    assert not c.is_valid_probability_distribution(d)


def test_domain_endpoints_and_interior_pole():
    x=sp.Symbol('x',real=True)
    assert c.is_defined_on_domain(sp.sqrt(x),x,sp.Interval(0,2))
    assert not c.is_defined_on_domain(sp.log(x),x,sp.Interval(0,2))
    assert c.is_defined_on_domain(sp.log(x),x,sp.Interval.Lopen(0,2))
    assert not c.is_defined_on_domain(1/(x-sp.Rational(1,7)),x,sp.Interval(0,1))
    assert not c.is_continuous_on_interval(1/x,x,sp.Interval(-1,1))
    assert c.is_continuous_on_interval(sp.sin(x),x,sp.Interval(-1,1))
    f=sp.Piecewise((0,x<0),(1,True))
    assert c.is_defined_on_domain(f,x,sp.Interval(-1,1))


def test_regular_curve_and_surface():
    t=sp.Symbol('t',real=True)
    assert c.has_regular_parameterization({'variables':[t],'components':[sp.cos(t),sp.sin(t)]},sp.Interval(0,1))
    assert not c.has_regular_parameterization({'variables':[t],'components':[t**2,t**3]},sp.Interval(-1,1))
    region=sample('integration_region');x,y=region['variables']
    assert c.has_regular_parameterization({'variables':[x,y],'components':[x,y,x+y]},region)
    assert not c.has_regular_parameterization({'variables':[x,y],'components':[x,x,2*x]},region)


def test_laplace_and_fourier_sufficient_conditions():
    t=sp.Symbol('t',real=True)
    assert c.is_transform_admissible(t**2*sp.exp(3*t),{'transform':'laplace','variable':t})
    assert c.is_transform_admissible(t**2*sp.exp(-2*t**2),{'transform':'fourier','variable':t})
    assert not c.is_transform_admissible(1/t,{'transform':'laplace','variable':t})
    with pytest.raises(c.ConstraintEvaluationError):c.is_transform_admissible(sp.exp(t**2),{'transform':'laplace','variable':t})


def test_complex_poles_and_invalid_domain():
    z=sp.Symbol('z')
    assert c.is_analytic_on_domain(sp.exp(z),z,sp.S.Complexes)
    assert not c.is_analytic_on_domain(1/z,z,sp.S.Complexes)
    assert c.is_analytic_on_domain(1/(z-3),z,{'center':0,'radius':2})
    assert not c.is_analytic_on_domain(1/(z-1),z,{'center':0,'radius':2})
    with pytest.raises(c.ConstraintEvaluationError):c.is_analytic_on_domain(z,z,{'radius':-1})


def test_statistics_checks_do_not_invent_assumptions():
    assert c.satisfies_statistical_assumptions([1,2,3],{'nonzero_variance':True,'min_df':2})
    assert not c.satisfies_statistical_assumptions([2,2,2],{'nonzero_variance':True})
    assert not c.satisfies_statistical_assumptions([[1,2],[2,3],[3,4]],{'paired':True,'nonzero_variance':True})
    with pytest.raises(c.ConstraintEvaluationError):c.satisfies_statistical_assumptions([1,2,3],{'normal':True})


def test_string_and_structured_predicate_connections():
    x=sp.Symbol('x',real=True);values={'f':sp.log(x),'x':x,'D':sp.Interval(1,3)}
    assert c.evaluate_string_constraint('is_defined_on_domain(f, x, D)',values).passed
    rule=ConstraintSpec(type='domain',expression={'constraint_id':'domain','rule':{'left':'f','operator':'is_defined_on_domain','args':['x','D'],'right':True}})
    assert c.evaluate_constraints([rule],values).passed
    values['D']=sp.Interval(0,3)
    assert not c.evaluate_constraints([rule],values).passed
    assert c.evaluate_string_constraint('satisfies_statistical_assumptions(data, {"min_samples": 2})',{'data':[1,2]}).passed


def test_unsafe_strings_fail_closed():
    with pytest.raises(c.ConstraintEvaluationError):c.evaluate_string_constraint('__import__("os").getcwd()',{})
    with pytest.raises(c.ConstraintEvaluationError):c.is_defined_on_domain('x**2',sp.Symbol('x',real=True),sp.Interval(0,1))
    raw=ParameterSpec(type='expression',derived={'depends_on':['a'],'expression':'__import__("os")','engine':'sympy'})
    with pytest.raises(s.ParameterSamplingError):s.sample_parameters({'f':raw,'a':ParameterSpec(type='integer',min=1,max=1)},seed=3)


def test_linear_algebra_dimension_and_symmetric_contract():
    specs={'A':ParameterSpec(type='matrix',min=-3,max=3,shape={'rows':2,'cols':3}),
           'B':ParameterSpec(type='matrix',min=-3,max=3,shape={'rows':'A.cols','cols':2},depends_on=['A']),
           'S':ParameterSpec(type='matrix',min=-3,max=3,shape={'rows':3,'cols':3},allowed_families=['symmetric'])}
    values=s.sample_parameters(specs,seed=17)
    assert values['A'].shape==(2,3) and values['B'].shape==(3,2)
    assert c.evaluate_string_constraint('A.cols == B.rows and is_symmetric(S)',values).passed


def test_series_does_not_ignore_singular_initial_terms():
    n=sp.Symbol('n',integer=True,positive=True)
    assert not c.is_series_convergent(1/(n-1)**2,n,1)
    assert not c.is_series_convergent(1/(n-2)**2,n,1)
    assert c.is_series_convergent(1/(n-sp.Rational(1,2))**2,n,1)


def test_multivariate_constant_coefficient_stays_in_range():
    x,y=sp.symbols('x y',real=True)
    for seed in range(10):
        f=sample('multivariate_function',seed=seed,degree=2)
        assert all(-3<=v<=3 for v in sp.Poly(f,x,y).coeffs())


def test_ode_requires_continuity_near_initial_point():
    ode=sample('differential_equation',initial_point=0)
    t,y=ode['variable'],ode['function']
    ode['equation']=sp.Eq(sp.diff(y,t),sp.sqrt(t))
    assert not c.has_valid_ode_conditions(ode)


def test_numeric_normal_data_and_reference_parameters():
    data=sample('numeric_data',data_family='normal',element_type='real',min=-100,max=100,shape={'size':30},sigma=2)
    assert len(data)==30 and all(isinstance(v,float) for v in data)
    specs={'distribution':ParameterSpec(type='probability_distribution',family='binomial',parameters={'n':'n','p':'p'},depends_on=['n','p']),
           'n':ParameterSpec(type='integer',min=5,max=5),
           'p':ParameterSpec(type='rational',min=0,max=1,choices=[sp.Rational(1,3)])}
    values=s.sample_parameters(specs,seed=17)
    assert values['distribution']['parameters']=={'n':5,'p':sp.Rational(1,3)}


def test_structured_config_reference():
    t=sp.Symbol('t',real=True)
    rule=ConstraintSpec(type='transform',expression={'constraint_id':'laplace','rule':{'left':'f','operator':'is_transform_admissible','args':['config'],'right':True}})
    values={'f':sp.exp(-t),'config':{'transform':'laplace','variable':t}}
    assert c.evaluate_constraints([rule],values).passed
