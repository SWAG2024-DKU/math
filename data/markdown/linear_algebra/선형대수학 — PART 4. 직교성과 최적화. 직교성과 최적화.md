# 선형대수학 — PART 4. 직교성과 최적화

> 각 개념은 **개념명 → 개념 정의 → 핵심 공식 → 공식의 적용 조건 → 주요 성질 → 선수 개념 → 자주 혼동하는 포인트(오개념 구조)** 순서로 정리한다.

벡터의 내적을 바탕으로 길이(Norm)와 직교성(Orthogonality)을 정의하고, 이를 활용해 기저를 직교화하는 알고리즘과 과결정계(Overdetermined system)에서의 최적 근사해를 구하는 최소제곱법(Least Squares)을 모델링한다.

---

## 4.1 내적 공간과 노름(Norm)·거리 계산

### 개념명
4.1 내적 공간과 노름(Norm)·거리 계산

### 개념 정의
공간 상의 두 벡터의 성분끼리 곱하고 합하여 하나의 실수(스칼라)로 매핑하는 점곱(Dot Product)을 통해 벡터의 기하학적 크기(길이)와 벡터 간의 거리 및 각도를 대수적으로 수치화한다.

### 핵심 공식
표준 내적 (Dot Product):
$$\mathbf{u} \cdot \mathbf{v} = \mathbf{u}^T \mathbf{v} = u_1 v_1 + u_2 v_2 + \cdots + u_n v_n$$

노름(Norm)과 거리(Distance):
$$\|\mathbf{u}\| = \sqrt{\mathbf{u} \cdot \mathbf{u}}$$
$$\text{dist}(\mathbf{u}, \mathbf{v}) = \|\mathbf{u} - \mathbf{v}\| = \sqrt{(\mathbf{u} - \mathbf{v}) \cdot (\mathbf{u} - \mathbf{v})}$$

코시-슈바르츠 부등식:
$$|\mathbf{u} \cdot \mathbf{v}| \le \|\mathbf{u}\| \|\mathbf{v}\|$$

### 공식의 적용 조건
유클리드 공간 $\mathbb{R}^n$에서 두 벡터 $\mathbf{u}, \mathbf{v}$는 반드시 동일한 차원(Dimension)인 $n \times 1$ 열벡터여야 내적 연산이 정의된다.

### 주요 성질
$\mathbf{u} \cdot \mathbf{u} = 0$이 될 필요충분조건은 오직 $\mathbf{u} = \mathbf{0}$일 때뿐이다(양의 정부호성). 내적 결과가 0이면 두 벡터는 직교(Orthogonal)한다.

### 선수 개념
벡터의 덧셈과 스칼라곱, 전치행렬 연산.

### 자주 혼동하는 포인트
- **결과값의 데이터 타입 혼동:** 벡터 간의 내적 결과 $\mathbf{u} \cdot \mathbf{v}$를 실수(스칼라)가 아닌 벡터 공간의 원소로 착각하여, 이어지는 연산에서 차원 불일치를 일으키는 파싱 오류.
- **정규화(Normalization) 인자 오류:** 벡터를 단위벡터로 만들 때 $\frac{\mathbf{u}}{\|\mathbf{u}\|}$가 아닌 노름의 제곱인 $\frac{\mathbf{u}}{\|\mathbf{u}\|^2}$로 나누어버리는 기하학적 척도 오류.

---

## 4.2 직교성과 직교 여공간 (Orthogonal Complement)

### 개념명
4.2 직교성(Orthogonality)과 직교 여공간 (Orthogonal Complement)

### 개념 정의
어떤 부분공간 $W$에 속한 '모든' 벡터와 내적이 0이 되는(수직인) 벡터들의 집합을 직교 여공간($W^\perp$)이라 하며, 행렬이 생성하는 4대 부분공간 간의 직교(수직) 관계를 대수적으로 모델링한다.

### 핵심 공식
직교 여공간의 정의:
$$W^\perp = \{\mathbf{z} \in \mathbb{R}^n \mid \mathbf{z} \cdot \mathbf{w} = 0 \text{ for all } \mathbf{w} \in W\}$$

행렬 부분공간의 기본 직교성:
$$N(A) = C(A^T)^\perp \quad \text{(영공간은 행공간과 직교)}$$
$$N(A^T) = C(A)^\perp \quad \text{(좌영공간은 열공간과 직교)}$$

### 공식의 적용 조건
부분공간 $W$에 직교하는 임의의 벡터를 구하려면, $W$를 구성하는 무한한 벡터와 모두 내적할 필요 없이 $W$의 **'기저(Basis) 벡터'**들과의 내적이 0이 되는지만 검증하면 충분하다.

### 주요 성질
공간과 그 직교 여공간의 차원을 합하면 항상 전체 공간의 차원이 된다. ($\dim(W) + \dim(W^\perp) = n$). $(W^\perp)^\perp = W$가 성립한다.

### 선수 개념
내적, 4대 핵심 부분공간(열공간, 영공간), 기저.

### 자주 혼동하는 포인트
- **부분공간 매핑 축 역전:** 행렬 $A$의 열공간 $C(A)$에 대한 직교 여공간을 구하라는 문제에서, 좌영공간 $N(A^T)$가 아닌 원본 영공간 $N(A)$를 계산하여 차원과 기저를 완전히 잘못 맵핑하는 구조적 오류.

---

## 4.3 직교집합 및 정규직교집합 (Orthonormal Set)

### 개념명
4.3 직교집합 및 정규직교집합 (Orthonormal Set)

### 개념 정의
집합 내 서로 다른 두 벡터 간의 내적이 모두 0인 벡터들의 모임을 직교집합(Orthogonal Set)이라 하며, 그중 모든 벡터의 크기(Norm)가 1로 정규화된 집합을 정규직교집합이라 한다.

### 핵심 공식
정규직교(Orthonormal) 조건:
$$
\mathbf{u}_i \cdot \mathbf{u}_j = 
\begin{cases} 
0 & (i \neq j) \\
1 & (i = j) 
\end{cases}
$$

직교 기저 좌표계수 분해:
$$\mathbf{y} = c_1\mathbf{u}_1 + \cdots + c_p\mathbf{u}_p \implies c_j = \frac{\mathbf{y} \cdot \mathbf{u}_j}{\mathbf{u}_j \cdot \mathbf{u}_j}$$

직교행렬(Orthogonal Matrix, $Q$)의 특성:
$$Q^T Q = I$$

### 공식의 적용 조건
영벡터($\mathbf{0}$)는 다른 어떤 벡터와도 내적이 0이므로 직교집합에는 포함될 수 있으나, 크기를 1로 만들 수 없으므로 정규직교집합에는 절대 포함될 수 없다.

### 주요 성질
영벡터를 포함하지 않는 모든 직교집합은 자동으로 '선형독립'이 되므로 그 자체로 기저가 된다. $n \times n$ 정규직교행렬 $Q$는 역행렬이 전치행렬과 같다 ($Q^{-1} = Q^T$).

### 선수 개념
선형독립, 선형결합 좌표(Weights), 기저.

### 자주 혼동하는 포인트
- **비정사각 직교행렬의 전치 역행렬화:** 열벡터가 정규직교인 직사각행렬 $Q$에 대하여 $Q^T Q = I$는 성립하지만, 교환법칙인 $Q Q^T = I$가 성립한다고 착각하여 사영행렬 계산식을 무너뜨리는 비대칭성 오개념.
- **좌표계수 분모 누락:** 정규직교기저가 아닌 일반 직교기저를 사용할 때, 좌표계수 $c_j$를 구하는 분모의 자기내적($\mathbf{u}_j \cdot \mathbf{u}_j$)을 생략하는 스케일링 오류.

---

## 4.4 부분공간으로의 직교 사영 (Orthogonal Projection)

### 개념명
4.4 부분공간으로의 직교 사영 (Orthogonal Projection)

### 개념 정의
어떤 벡터 $\mathbf{b}$를 특정 부분공간 $W$ 위에 가장 가까운 벡터 그림자인 투영 성분($\hat{\mathbf{b}}$)과 부분공간에 수직인 직교 오차 성분($\mathbf{z}$)으로 분해하는 기하학적 연산이다.

### 핵심 공식
부분공간 $W$로의 사영 (단, $\{\mathbf{u}_1, \dots, \mathbf{u}_p\}$는 $W$의 **직교기저**):
$$\hat{\mathbf{b}} = \text{proj}_W \mathbf{b} = \frac{\mathbf{b} \cdot \mathbf{u}_1}{\mathbf{u}_1 \cdot \mathbf{u}_1}\mathbf{u}_1 + \cdots + \frac{\mathbf{b} \cdot \mathbf{u}_p}{\mathbf{u}_p \cdot \mathbf{u}_p}\mathbf{u}_p$$

직교 분해 정리:
$$\mathbf{b} = \hat{\mathbf{b}} + \mathbf{z} \quad (\hat{\mathbf{b}} \in W, \mathbf{z} \in W^\perp)$$

일반 사영행렬 $P$ (열공간이 $W$인 행렬 $A$ 기준):
$$P = A(A^T A)^{-1}A^T \implies \hat{\mathbf{b}} = P\mathbf{b}$$

### 공식의 적용 조건
선형결합 형태의 간단한 사영 공식($\frac{\mathbf{b} \cdot \mathbf{u}}{\mathbf{u} \cdot \mathbf{u}}\mathbf{u}$의 합)을 쓰려면 투영 기준이 되는 부분공간 $W$의 기저가 **반드시 서로 직교(Orthogonal)**해야만 성립한다.

### 주요 성질
사영행렬 $P$는 대칭행렬($P^T=P$)이며, 한 번 사영된 벡터를 다시 사영해도 그대로 유지되는 멱등성($P^2=P$)을 가진다.

### 선수 개념
기저, 직교 여공간, 내적과 선형결합.

### 자주 혼동하는 포인트
- **비직교 기저에 직교 사영 공식 과적용:** 문제에서 주어진 기저가 서로 직교하지 않음에도 그람-슈미트 직교화를 거치지 않고, 기저 벡터 각각에 독립적인 1차원 사영 공식을 쓴 뒤 무작정 더해버리는 치명적 구조 오류.

---

## 4.5 그람-슈미트 직교화 (Gram-Schmidt Process)

### 개념명
4.5 그람-슈미트 직교화 (Gram-Schmidt Process)

### 개념 정의
임의의 일반 기저 벡터 집합으로부터, 순차적으로 이전 벡터가 만들어낸 공간으로의 직교 사영을 빼나감으로써 새로운 직교기저를 추출해내는 순환 알고리즘이다.

### 핵심 공식
직교기저 $\mathbf{v}_i$ 도출 순환식 (입력 기저 $\{\mathbf{x}_1, \dots, \mathbf{x}_p\}$):
$$\mathbf{v}_1 = \mathbf{x}_1$$
$$\mathbf{v}_2 = \mathbf{x}_2 - \frac{\mathbf{x}_2 \cdot \mathbf{v}_1}{\mathbf{v}_1 \cdot \mathbf{v}_1}\mathbf{v}_1$$
$$\mathbf{v}_k = \mathbf{x}_k - \sum_{j=1}^{k-1} \left( \frac{\mathbf{x}_k \cdot \mathbf{v}_j}{\mathbf{v}_j \cdot \mathbf{v}_j}\mathbf{v}_j \right)$$

정규화 (Orthonormal Basis):
$$\mathbf{q}_k = \frac{\mathbf{v}_k}{\|\mathbf{v}_k\|}$$

### 공식의 적용 조건
입력되는 초기 벡터 집합은 반드시 선형독립이어야 한다. 종속인 벡터가 포함되어 있으면 알고리즘 도중 $\mathbf{v}_k = \mathbf{0}$이 발생하여 영분모(ZeroDivision) 오류가 일어난다.

### 주요 성질
그람-슈미트 과정을 거쳐 생성된 직교 집합 $\{\mathbf{v}_1, \dots, \mathbf{v}_k\}$은 원래의 벡터 집합 $\{\mathbf{x}_1, \dots, \mathbf{x}_k\}$과 동일한 크기의 스팬(Span) 부분공간을 구성한다.

### 선수 개념
선형독립, 1차원 직교 사영.

### 자주 혼동하는 포인트
- **사영 기준 벡터의 순환 오류:** $\mathbf{v}_3$를 계산할 때, 빼주어야 할 사영의 축(분모)을 이미 깎여서 직교화된 $\mathbf{v}_1, \mathbf{v}_2$가 아닌 원래의 입력 벡터 $\mathbf{x}_1, \mathbf{x}_2$로 잘못 사용하는 기호 맵핑 오류.

---

## 4.6 $QR$ 분해 ($QR$ Decomposition)

### 개념명
4.6 $QR$ 분해 ($QR$ Decomposition)

### 개념 정의
행렬 $A$의 열벡터들에 그람-슈미트 직교화를 적용하여, 정규직교열을 가진 행렬 $Q$와 그 변환 계수(내적 값)들을 기록한 가역 상삼각행렬 $R$의 곱으로 행렬을 쪼개는 알고리즘이다.

### 핵심 공식
행렬 분해:
$$A = QR$$
$$Q^T Q = I \quad (Q \in \mathbb{R}^{m \times n}, R \in \mathbb{R}^{n \times n})$$

$R$ 행렬의 구성과 역산:
$$R = Q^T A$$
$$r_{ij} = \mathbf{q}_i \cdot \mathbf{a}_j \quad (i \le j, \text{나머지는 0})$$

### 공식의 적용 조건
축소된(Reduced) 형태의 $A=QR$ 분해를 온전히 수행하려면, 행렬 $A \in \mathbb{R}^{m \times n}$의 모든 열벡터가 선형독립($\text{Rank}(A)=n$)이어야 한다.

### 주요 성질
$QR$ 분해는 최소제곱법 해를 대수적으로 가장 안정적이고 빠르게 구하는 알고리즘($R\hat{\mathbf{x}} = Q^T\mathbf{b}$)의 뼈대가 되며 행렬의 고윳값을 근사하는 수치 기법에 활용된다.

### 선수 개념
그람-슈미트 정규직교화, 상삼각행렬.

### 자주 혼동하는 포인트
- **$R$ 행렬의 인덱스 한계 역전:** $r_{ij} = \mathbf{q}_i \cdot \mathbf{a}_j$를 계산하여 행렬을 채울 때, 인덱스 조건($i \le j$)을 무시하고 하삼각행렬 쪽에 값을 채워 넣어 삼각 분해 구조를 붕괴시키는 오류.

---

## 4.7 최소제곱법 (Least Squares Solution)

### 개념명
4.7 최소제곱법 (Least Squares Solution)

### 개념 정의
방정식의 개수가 미지수보다 많아 정확한 해가 존재하지 않는 불능 시스템($A\mathbf{x}=\mathbf{b}$)에서, 오차 벡터의 크기 $\|A\mathbf{x}-\mathbf{b}\|^2$를 가장 작게 만드는 최적의 근사해 $\hat{\mathbf{x}}$를 구하는 기법이다.

### 핵심 공식
정규방정식 (Normal Equation):
$$A^T A \hat{\mathbf{x}} = A^T \mathbf{b}$$

최소제곱해의 명시적 산출:
$$\hat{\mathbf{x}} = (A^T A)^{-1}A^T \mathbf{b}$$

### 공식의 적용 조건
$A^T A$가 역행렬을 가져서 유일한 최소제곱해를 산출하려면, 원본 설계행렬 $A$의 열벡터들이 모두 선형독립이어야 한다. 독립이 아니면 무수히 많은 근사해를 가진다.

### 주요 성질
기하학적으로 최소제곱해는 우변 벡터 $\mathbf{b}$를 $A$의 열공간으로 수직 투영시킨 사영 벡터 $\hat{\mathbf{b}}$를 생성하는 파라미터($A\hat{\mathbf{x}} = \hat{\mathbf{b}}$)이며, 이때 남은 잔차 벡터($\mathbf{b} - A\hat{\mathbf{x}}$)는 열공간 $C(A)$와 직교한다.

### 선수 개념
부분공간 사영, 직교성, 역행렬 계산.

### 자주 혼동하는 포인트
- **정규방정식 유도 차원 붕괴:** $A\mathbf{x}=\mathbf{b}$에서 양변 왼쪽에 $A^T$를 곱해야 차원이 매핑되는데, 역행렬이 존재하지 않는 비정사각 행렬 $A$에 억지로 가역행렬 정리(IMT)를 적용하여 분해하려다 알고리즘이 멈추는 오류.

---

## 4.8 데이터 피팅 및 선형 회귀 (Linear Regression)

### 개념명
4.8 데이터 피팅 및 선형 회귀 (Linear Regression)

### 개념 정의
다수의 관측된 데이터 포인트들을 가장 잘 설명하는 모델(직선, 포물선 등)의 계수 파라미터를 찾기 위해, 데이터를 최소제곱법 정규방정식 시스템으로 설계하고 행렬 텐서로 계산하는 과정이다.

### 핵심 공식
선형 회귀 설계모델 구축 ($y = \beta_0 + \beta_1 x$):
$$X \boldsymbol{\beta} = \mathbf{y}$$
$$\begin{bmatrix} 1 & x_1 \\ 1 & x_2 \\ \vdots & \vdots \\ 1 & x_m \end{bmatrix} \begin{bmatrix} \beta_0 \\ \beta_1 \end{bmatrix} = \begin{bmatrix} y_1 \\ y_2 \\ \vdots \\ y_m \end{bmatrix}$$

잔차 오차 제곱합 최소화:
$$\hat{\boldsymbol{\beta}} = (X^T X)^{-1}X^T \mathbf{y}$$

### 공식의 적용 조건
수학적으로 선형 회귀라 함은 독립변수 $x$의 형태가 아니라, **'구해야 하는 파라미터 $\beta$'에 대해 1차 선형결합 형태**여야 함을 의미한다. ($y = \beta_0 + \beta_1 \sin(x)$는 선형 회귀 모델 행렬로 구축 가능하다.)

### 주요 성질
설계 행렬(Design Matrix) $X$에 관측 데이터를 매핑하는 방식에 따라 다중 선형 회귀, 다항식 커브 피팅 등 통계적 모델링을 선형대수학적 연산으로 완벽히 치환할 수 있다.

### 선수 개념
최소제곱법, 행렬과 벡터의 곱.

### 자주 혼동하는 포인트
- **상수항 $\beta_0$의 절편 열 누락:** 설계 행렬 $X$를 구성할 때 상수항(절편)을 위한 모든 성분이 1인 0번 인덱스 열을 누락하여, 추세선이 무조건 원점(0,0)을 지나도록 강제해버리는 데이터 설계 오류.