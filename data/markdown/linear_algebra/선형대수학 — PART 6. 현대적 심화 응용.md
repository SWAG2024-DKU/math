# 선형대수학 — PART 6. 현대적 심화 응용

> 각 개념은 **개념명 → 개념 정의 → 핵심 공식 → 공식의 적용 조건 → 주요 성질 → 선수 개념 → 자주 혼동하는 포인트(오개념 구조)** 순서로 정리한다.

데이터 마이닝, 머신러닝, 시스템 제어에서 핵심적으로 사용되는 특이값 분해(SVD)와 차원 축소 이론을 다룬다. 정사각·대칭행렬의 성질을 임의의 직사각행렬과 복소수 공간으로 한계까지 일반화하는 최종 모듈이다.

---

## 6.1 특이값 분해 (Singular Value Decomposition, SVD)

### 개념명
6.1 특이값 분해 (Singular Value Decomposition, SVD)

### 개념 정의
정사각행렬에만 국한되던 고윳값 분해를 일반화하여, 임의의 $m \times n$ 직사각행렬 $A$를 회전, 스케일링, 회전이라는 세 가지 기하학적 직교 변환의 조합으로 완전 분해하는 궁극의 행렬 분해 기법이다.

### 핵심 공식
SVD 분해 모델 ($A \in \mathbb{R}^{m \times n}$):
$$A = U \Sigma V^T$$

$U$ (좌특이벡터 행렬) 및 $V$ (우특이벡터 행렬) 도출:
$$A^T A = V \Sigma^2 V^T \quad \text{($V$는 $A^T A$의 직교 고유벡터, $n \times n$)}$$
$$A A^T = U \Sigma^2 U^T \quad \text{($U$는 $A A^T$의 직교 고유벡터, $m \times m$)}$$

특이값(Singular Values) $\sigma_i$:
$$\sigma_i = \sqrt{\lambda_i(A^T A)} \quad (\sigma_1 \ge \sigma_2 \ge \cdots \ge \sigma_r > 0)$$

### 공식의 적용 조건
특이값 $\sigma_i$를 구하기 위한 $A^T A$는 무조건 양의 반정부호(Positive Semi-definite) 대칭행렬이므로, 고윳값은 항상 0 이상의 실수($\lambda_i \ge 0$)임이 완벽히 보장된다.

### 주요 성질
$U$의 열벡터들은 $A$의 열공간($C(A)$)과 좌영공간($N(A^T)$)의 정규직교기저를 형성하고, $V$의 열벡터들은 행공간($C(A^T)$)과 영공간($N(A)$)의 정규직교기저를 구성한다. 랭크($\text{Rank}(A)$)는 0이 아닌 특이값의 개수 $r$과 정확히 일치한다.

### 선수 개념
대칭행렬의 직교 대각화, 4대 부분공간, 직교행렬.

### 자주 혼동하는 포인트
- **$U$와 $V$의 연산 행렬 역전:** $V$를 구해야 하는데 $AA^T$를 계산하거나, $U$를 구해야 하는데 $A^TA$를 계산하여 변환 축의 도메인(Domain) 차원을 통째로 뒤바꿔버리는 텐서 매핑 오류.
- **특이값과 고윳값의 혼동:** $\sigma_i$를 구할 때 고윳값 $\lambda_i$에 루트($\sqrt{}$)를 씌우지 않고 그대로 대각행렬 $\Sigma$에 집어넣는 스케일링 폭주 오류.

---

## 6.2 축소 SVD (Compact SVD)와 행렬 근사

### 개념명
6.2 축소 SVD (Compact / Truncated SVD)와 행렬 근사

### 개념 정의
원본 SVD에서 0인 특이값과 그에 곱해지는 무의미한 영공간 벡터들을 제거하여 연산량을 최적화하고, 상위 $k$개의 특이값만 남겨 노이즈를 제거한 최적의 '저랭크 근사(Low-Rank Approximation)'를 구현하는 과정이다.

### 핵심 공식
축소 SVD (Compact SVD, $r = \text{Rank}(A)$):
$$A = U_r \Sigma_r V_r^T = \sum_{i=1}^{r} \sigma_i \mathbf{u}_i \mathbf{v}_i^T$$

절단 SVD ($k$-Rank Approximation, $k < r$):
$$A_k = \sum_{i=1}^{k} \sigma_i \mathbf{u}_i \mathbf{v}_i^T$$

Eckart-Young-Mirsky 정리 (오차 최소화 보장):
$$\min_{\text{Rank}(B)=k} \|A - B\|_F = \|A - A_k\|_F = \sqrt{\sum_{i=k+1}^{r} \sigma_i^2}$$

### 공식의 적용 조건
외적(Outer product) $\mathbf{u}_i \mathbf{v}_i^T$를 합산하는 스펙트럼 분해 방식을 적용할 때, 반드시 특이값이 큰 순서($\sigma_1 \ge \sigma_2 \ge \dots$)로 내림차순 정렬되어 있어야만 최적 근사 논리가 성립한다.

### 주요 성질
절단 SVD로 만든 랭크 $k$ 행렬 $A_k$는, 동일한 랭크 $k$를 가지는 세상의 모든 행렬 중 원본 $A$와의 프로베니우스 노름(정보 손실량) 오차가 가장 작은 최적의 수학적 근사치이다.

### 선수 개념
특이값 분해(SVD), 랭크-1 행렬 텐서(외적), 노름(Norm).

### 자주 혼동하는 포인트
- **축소 시 차원 분리 누락:** $\Sigma$ 행렬에서 $0$ 블록 행을 잘라낼 때, 이에 곱해지는 $U$ 행렬의 열(Column) 차원을 함께 제거하지 않고 연산을 시도하여 내적 차원 불일치(Dimension Mismatch)를 일으키는 현상.

---

## 6.3 의사역행렬 (Pseudoinverse)

### 개념명
6.3 의사역행렬 (Pseudoinverse / Moore-Penrose Inverse)

### 개념 정의
역행렬이 존재하지 않는 비정사각 행렬이나 특이행렬(Singular Matrix)에 대하여, 가역행렬의 역행렬 기능을 가장 완벽하게 흉내 내는 일반화된 역행렬 $A^+$를 SVD를 통해 구성한다.

### 핵심 공식
무어-펜로즈 역행렬 구성 ($A = U \Sigma V^T$):
$$A^+ = V \Sigma^+ U^T$$

$\Sigma^+$ 구성 규칙:
1. $\Sigma$를 전치(Transpose)한다. (크기 $m \times n \to n \times m$)
2. 0이 아닌 대각 성분 $\sigma_i$를 역수 $1/\sigma_i$로 뒤집는다.

의사역행렬을 이용한 최소제곱해:
$$\hat{\mathbf{x}} = A^+ \mathbf{b}$$

### 공식의 적용 조건
가역인 정사각행렬에 의사역행렬 알고리즘을 적용하면, 그 결과는 정확히 본래의 역행렬 $A^{-1}$과 100% 일치해야 한다.

### 주요 성질
최소제곱법 정규방정식($A^T A \hat{\mathbf{x}} = A^T \mathbf{b}$)에서 열벡터가 선형종속이라 무수히 많은 해가 존재할 경우, $\hat{\mathbf{x}} = A^+\mathbf{b}$는 그 해들 중 '노름(Norm, 길이)이 가장 짧은 최적의 해'를 유일하게 산출한다.

### 선수 개념
특이값 분해(SVD), 직교행렬의 전치, 최소제곱법.

### 자주 혼동하는 포인트
- **대각행렬 전치(Transpose) 누락:** $\Sigma$의 대각 성분만 역수로 바꾸고 행렬의 껍데기 차원(Shape)을 전치($n \times m$으로 전환)하는 것을 잊어버려, $V$나 $U^T$와의 행렬 곱에서 연산 충돌을 유발하는 형식 역전 오류.

---

## 6.4 주성분 분석 (Principal Component Analysis, PCA)

### 개념명
6.4 주성분 분석 (Principal Component Analysis, PCA)

### 개념 정의
다차원 공간의 데이터 포인트들이 가진 분산(Variance)이 가장 극대화되는 직교 축(주성분)을 순차적으로 찾아, 정보 손실을 최소화하며 데이터의 차원을 축소하는 통계적 선형대수 알고리즘이다.

### 핵심 공식
평균 중심화 데이터 행렬 (Mean-Centered Matrix): $X$
공분산 행렬 (Covariance Matrix):
$$S = \frac{1}{n-1} X^T X \quad (\text{단, } X \in \mathbb{R}^{n \times p})$$

PCA 매핑 (주성분 도출):
$S$를 대각화 ($S = V D V^T$)할 때 도출된 고유벡터 행렬 $V$의 열벡터들이 바로 주성분(PC) 축이다. (이는 $X$의 SVD 분해 시 $V$와 완벽히 동일하다).

### 공식의 적용 조건
공분산을 계산하기 전, 반드시 모든 데이터의 각 피처(열)에 대해 평균을 0으로 맞추는 중심화(Mean Centering) 전처리를 수행해야 한다.

### 주요 성질
제1 주성분(PC1)은 데이터의 분산이 가장 큰 축이며, 제2 주성분(PC2)은 PC1과 직교하면서 남은 분산이 가장 큰 축이다. 주성분들은 데이터 공간의 새로운 정규직교기저가 된다.

### 선수 개념
공분산 행렬, 대칭행렬의 직교 대각화, 축소 SVD.

### 자주 혼동하는 포인트
- **평균 중심화 전처리 누락:** 데이터의 원점을 맞추지 않고 원본 데이터를 그대로 $X^T X$ 연산에 넣어, 분산의 축이 아닌 원점에서 질량 중심을 향하는 엉뚱한 임의의 벡터를 주성분으로 잘못 도출하는 기하학적 설계 붕괴.

---

## 6.5 복소 내적 공간 (Hermitian & Unitary Matrices)

### 개념명
6.5 복소 내적 공간 (Hermitian & Unitary Matrices)

### 개념 정의
성분이 복소수(허수)인 벡터 공간으로 선형대수 체계를 확장한다. 단순 전치가 아닌 켤레 전치(Conjugate Transpose) 연산자를 도입하여 내적과 길이(Norm)가 실수계열과 동일하게 작동하도록 모델링한다.

### 핵심 공식
켤레 전치 연산자 (Hermitian Adjoint):
$$A^* = \overline{A}^T$$

복소 내적 (Complex Inner Product):
$$\langle \mathbf{u}, \mathbf{v} \rangle = \mathbf{u}^* \mathbf{v} = \overline{u}_1 v_1 + \overline{u}_2 v_2 + \cdots + \overline{u}_n v_n$$

실수 대칭/직교 행렬의 복소수 일반화:
$$A^* = A \quad (\text{에르미트 행렬, Hermitian})$$
$$U^* U = I \quad (\text{유니타리 행렬, Unitary})$$

### 공식의 적용 조건
복소 내적에서는 교환법칙이 성립하지 않는다. 순서를 바꿀 경우 켤레 복소수(Conjugate)가 튀어나오는 교대 대칭성($\langle \mathbf{v}, \mathbf{u} \rangle = \overline{\langle \mathbf{u}, \mathbf{v} \rangle}$) 제약을 반드시 반영해야 한다.

### 주요 성질
에르미트 행렬의 고윳값은 행렬 성분이 복소수임에도 불구하고 '무조건 100% 실수'라는 강력한 대수적 보장(Real spectrum)을 갖는다.

### 선수 개념
켤레 복소수, 대칭행렬, 직교행렬.

### 자주 혼동하는 포인트
- **복소 벡터의 자기 내적 차원 파괴:** 복소 벡터의 노름을 구할 때 $\mathbf{u}^* \mathbf{u}$가 아닌 실수에서의 방식인 $\mathbf{u}^T \mathbf{u}$를 강제 적용하여, 길이 값에 허수가 나타나는 유클리드 기하학 파괴 오류. (켤레 전치를 해야 $a^2+b^2$ 꼴이 되어 항상 0 이상의 실수가 나온다.)

---

## 6.6 조르당 표준형 (Jordan Canonical Form)

### 개념명
6.6 조르당 표준형 (Jordan Canonical Form)

### 개념 정의
고유벡터가 부족하여(대수적 중복도 $>$ 기하적 중복도) 대각화가 불가능한 결함 행렬(Defective matrix)을, 대각행렬에 가장 근사한 형태인 '주대각선 위가 1인 블록 행렬' 구조로 기저 변환하는 일반화 알고리즘이다.

### 핵심 공식
조르당 분해 모델:
$$A = M J M^{-1} \quad (J \text{는 조르당 블록들의 대각 조합})$$

일반화 고유벡터(Generalized Eigenvector, $\mathbf{v}_k$) 체인:
$$(A - \lambda I)\mathbf{v}_1 = \mathbf{0}$$
$$(A - \lambda I)\mathbf{v}_2 = \mathbf{v}_1$$
$$(A - \lambda I)\mathbf{v}_k = \mathbf{v}_{k-1}$$

조르당 블록 $J_i$ 구조:
$$J_i = \begin{bmatrix} \lambda & 1 & 0 \\ 0 & \lambda & 1 \\ 0 & 0 & \lambda \end{bmatrix}$$

### 공식의 적용 조건
대각화가 가능한 정상 행렬을 조르당 알고리즘에 통과시키면, 1이 붙은 블록은 생성되지 않으며 그 결과는 대각행렬 $D$ 그 자체($J=D$)와 완벽히 동일하게 출력되어야 한다.

### 주요 성질
조르당 체인 방정식을 통해 도출된 일반화 고유벡터들은 서로 완벽하게 선형독립이 보장되므로, 모자란 기저의 수를 채워 공간 전체($\mathbb{R}^n$)를 스팬할 수 있는 전이행렬 $M$을 완성하게 해준다.

### 선수 개념
대각화 가능성, 결함 행렬, 고유벡터 공간.

### 자주 혼동하는 포인트
- **고유벡터 체인의 매핑 역전:** 연쇄 방정식 $(A-\lambda I)\mathbf{v}_{k} = \mathbf{v}_{k-1}$을 통해 기저를 찾을 때, 일반 고유벡터 $\mathbf{v}_1$에서 출발하는 역추적 순서를 반대로 매핑하여, 행렬 $M$에 벡터들을 우측부터 채워 넣는 등 기저 결합 구조를 붕괴시키는 알고리즘 역전 오류.