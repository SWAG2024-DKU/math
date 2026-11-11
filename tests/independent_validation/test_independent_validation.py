"""생성기 호출 없이 정상 답·오답·저장 무결성·프로세스 제한 시간을 검사한다."""
import copy
import json
import os
from pathlib import Path
import time
from uuid import uuid4
from zipfile import ZipFile
import pytest
import sympy as s
from scripts.problems.common.independent_instance_validator import (validate_payload, parse, digest, math_check, SUPPORTED_TYPES)
from scripts.InstanceDB_MAKE.validate_stored_instances import (validate_with_timeout, storage_check, iterate_rows, save_result)

FIXTURES=json.loads(Path(__file__).with_name('representative_previews.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('payload',FIXTURES,ids=lambda x:x['problem_type'])
def test_supported_examples(payload):
    assert validate_payload(payload)['result']=='passed'

@pytest.mark.parametrize('payload',FIXTURES,ids=lambda x:x['problem_type'])
def test_wrong_answer_is_blocked(payload):
    bad=copy.deepcopy(payload);answer=bad['expected_answer']
    if type(answer) is bool:bad['expected_answer']=not answer
    elif isinstance(answer,(int,float)):bad['expected_answer']=answer+1
    elif isinstance(answer,list):bad['expected_answer']=['999999']
    elif answer=='해 존재':bad['expected_answer']='해 없음'
    elif answer=='해 없음':bad['expected_answer']='해 존재'
    elif answer=='가역':bad['expected_answer']='비가역'
    elif answer=='비가역':bad['expected_answer']='가역'
    else:bad['expected_answer']='999999'
    assert validate_payload(bad)['result']!='passed'


def test_every_type_covered():assert {p['problem_type'] for p in FIXTURES}==SUPPORTED_TYPES


def test_statement_changes_are_blocked():
    p=copy.deepcopy(FIXTURES[0]);p['statement']+=' 다른 문제'
    assert validate_payload(p)['result']=='failed'


def test_unknown_wording_is_not_approved():
    p=copy.deepcopy(FIXTURES[0]);p['template_snapshot']['problem_builder']['text_templates_ko'][0]='임의의 문제'
    assert validate_payload(p)['result']=='unsupported'


def test_generator_trace_and_calculation_are_not_trusted():
    p=copy.deepcopy(next(p for p in FIXTURES if p['problem_type']=='matrix_multiplication'))
    p['validation_trace']={'passed':True}
    p['template_snapshot']['answer_spec']['cas_template']='__import__("os").system("echo unsafe")'
    # Schema가 expression을 저장할 뿐 검증기에서는 이를 실행하지 않는다.
    assert validate_payload(p)['result']=='passed'
    p['expected_answer']=[[999]]
    assert validate_payload(p)['result']!='passed'


def test_expression_parser_does_not_execute_code(tmp_path):
    marker=tmp_path/'executed'
    with pytest.raises(ValueError):parse(f'__import__("pathlib").Path({str(marker)!r}).touch()')
    assert not marker.exists()


def test_equivalent_basis_is_allowed_and_missing_vector_rejected():
    A=s.Matrix([[1,0,0],[0,0,0]])
    assert math_check('null_space_basis',{'A':A},[[0,2,0],[0,0,-3]])
    assert not math_check('null_space_basis',{'A':A},[[0,2,0]])
    assert not math_check('null_space_basis',{'A':A},[[0,2,0],[0,4,0]])


def test_repeated_eigenvalues_have_distinct_value_contract():
    A=s.diag(2,2,3)
    assert math_check('eigenvalue_calculation',{'A':A},[s.Integer(3),s.Integer(2)])
    assert not math_check('eigenvalue_calculation',{'A':A},[s.Integer(2)])


def sleeping_worker(pipe,payload):time.sleep(5)


def test_spawn_timeout():
    r=validate_with_timeout({},1,worker=sleeping_worker)
    assert r['result']=='unsupported' and r['report']['timeout']
    assert r['report']['elapsed_seconds']<4


def test_spawn_success():assert validate_with_timeout(FIXTURES[0],10)['result']=='passed'


def stored_row():
    p=copy.deepcopy(FIXTURES[0]);row={k:p[k] for k in ('template_id','template_version','subject_id','problem_type','seed','statement','expected_answer')}
    row.update(instance_id=uuid4(),payload=p,template_content_hash=digest(p['template_snapshot']),current_template_hash=digest(p['template_snapshot']),problem_hash=digest([p['template_id'],p['statement'],p['expected_answer']]),source_sha256='a'*64)
    return row


def test_storage_integrity():
    row=stored_row();storage_check(row)
    row['statement']='변조'
    with pytest.raises(ValueError,match='statement'):storage_check(row)


class Cursor:
    def __init__(self,one=None,many=None):self.one=one;self.many=many
    def fetchone(self):return self.one
    def fetchall(self):return self.many
class Transaction:
    def __init__(self,db):self.db=db
    def __enter__(self):self.db.transactions+=1
    def __exit__(self,*args):self.db.rolled_back=args[0] is not None
class Database:
    def __init__(self,row):self.row=row;self.queries=[];self.transactions=0;self.rolled_back=False
    def transaction(self):return Transaction(self)
    def execute(self,sql,args):
        self.queries.append((sql,args))
        if 'SELECT content_hash' in sql:return Cursor({'content_hash':self.row['current_template_hash']})
        if 'SELECT *' in sql:return Cursor(self.row)
        return Cursor()


def test_save_result_only_adds_validation_history():
    row=stored_row();db=Database(copy.deepcopy(row));save_result(db,row,validate_payload(row['payload']))
    assert db.transactions==1 and not db.rolled_back
    inserts=[q for q in db.queries if 'INSERT' in q[0]]
    assert len(inserts)==1 and 'instance_validation_runs' in inserts[0][0]
    assert all('UPDATE problem.problem_instances' not in q[0] for q in db.queries)


def test_changed_record_cannot_receive_stale_pass():
    row=stored_row();current=copy.deepcopy(row);current['expected_answer']=False;db=Database(current)
    with pytest.raises(ValueError,match='내용 변경'):save_result(db,row,validate_payload(row['payload']))
    assert db.rolled_back and not any('INSERT' in q[0] for q in db.queries)


def test_keyset_pagination_without_status_filter():
    rows=[{'instance_id':uuid4()} for _ in range(5)];rows.sort(key=lambda r:r['instance_id'])
    class Reader:
        def execute(self,sql,args):
            assert "subject_id='linear_algebra'" in sql and "status =" not in sql
            after,_,size=args
            return Cursor(many=[r for r in rows if after is None or r['instance_id']>after][:size])
    assert list(iterate_rows(Reader(),2))==rows
    assert list(iterate_rows(Reader(),2,rows[1]['instance_id'],2))==rows[2:4]


def test_optional_full_corpus():
    source=os.environ.get('LA_PREVIEW_TEST_ZIP')
    if not source:pytest.skip('LA_PREVIEW_TEST_ZIP 지정 시 전체 Preview 검사')
    count=0
    with ZipFile(source) as z:
        for n in z.namelist():
            if Path(n).name.startswith('start_') and n.endswith('.json'):
                assert validate_payload(json.loads(z.read(n)))['result']=='passed',n
                count+=1
    assert count>0
