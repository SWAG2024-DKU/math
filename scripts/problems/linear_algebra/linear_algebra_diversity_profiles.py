"""선형대수 다양성 정책의 Python 원본 — 함수별 구현 TODO.

아직 구현되지 않은 설계 뼈대입니다. 기존 생성기에는 연결하지 않았습니다.
정책의 숫자 값/가중치는 명시적으로 검토한 후 결정하세요.
"""
from __future__ import annotations
from typing import Any

def get_policy(problem_type: str, mode: str = "legacy") -> dict[str, Any]:
    # TODO[LA-N01] get_policy 구현
    # 1. 62개 실행 유형과 6단원을 매핑한다.
    # 2. legacy 기본값과 opt-in extended 모드를 분리한다.
    # 3. 정수/기약분수 혼합,.
    # 4. 분자·분모 범위, 구조 family와 가중치, 차원 및 난도 예산을 정의한다.
    # 5. 지정 범위를 실제 생성기가 사용하는지 검증한다.
    # 6. 미지원 유형은 명시적 오류.
    raise NotImplementedError("TODO[LA-N01]: get_policy")

def snapshot_reviewed_contract(rule: Any) -> dict[str, Any]:
    # TODO[LA-N02] snapshot_reviewed_contract 구현
    # 1. 기존 ID/version/status/executable/manual_review_required,.
    # 2. source_* IDs, 공식, symbol_spec, constraints, construction, answer_spec,.
    # 3. validation, difficulty, notes를 정확히 보존할 비교 스냅샷을 반환한다.
    # 4. 원본 hash 및 승인된 생성 범위와 확장 후보의 차이를 보고서에서 추적한다.
    raise NotImplementedError("TODO[LA-N02]: snapshot_reviewed_contract")

def apply_policy(rule: Any, policy: dict[str, Any]) -> Any:
    # TODO[LA-N03] apply_policy 구현
    # 1. 입력을 변경하지 않고 허용된 생성 설정만 병합한다.
    # 2. 기존 reviewed 규칙을 fallback 기본값으로 초기화하지 않는다.
    # 3. 사용자 설정과.
    # 4. 정책이 충돌하면 조용히 덮지 않고 보고한다.
    # 5. 멱등성 및 다른 과목 무변경 보장.
    # 6. 원본 승인 이력은 보존하고 확장 후보의 검수 상태는 별도로 관리한다.
    raise NotImplementedError("TODO[LA-N03]: apply_policy")

def validate_candidate(before: Any, after: Any) -> dict[str, Any]:
    # TODO[LA-N04] validate_candidate 구현
    # 1. 허용된 변경만 발생했는지, 참조/차원/제약/정답/검증기.
    # 2. 계약을 만족하는지 검사한다.
    # 3. 형식 검사만으로 수학 검증 완료 처리하지 않는다.
    raise NotImplementedError("TODO[LA-N04]: validate_candidate")
