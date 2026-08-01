# Calculus Volume 3 — Chapter 6
# Vector Calculus / 벡터미적분

## 선수 개념

- 2차원 벡터
- 3차원 벡터
- 내적
- 외적
- 벡터값 함수
- 매개곡선
- 곡면의 매개화
- 편도함수
- 그래디언트
- 이중적분
- 삼중적분
- 극좌표
- 원기둥좌표
- 구면좌표
- 접선벡터
- 법선벡터
- 방향도함수
- 다변수 연쇄법칙
- 영역의 경계
- 곡선의 방향

---

## 6.1 Vector Fields
## 벡터장

### 벡터장의 정의

평면의 각 점에 벡터를 대응시키는 함수를 2차원 벡터장이라고 한다.

$$\mathbf{F}(x,y)=\langle P(x,y),Q(x,y)\rangle$$

공간의 각 점에 벡터를 대응시키는 함수를 3차원 벡터장이라고 한다.

$$\mathbf{F}(x,y,z)=\langle P(x,y,z),Q(x,y,z),R(x,y,z)\rangle$$

---

### 벡터장의 정의역

벡터장의 정의역은 모든 성분함수의 공통 정의역이다.

$$\operatorname{Dom}(\mathbf{F})=\operatorname{Dom}(P)\cap\operatorname{Dom}(Q)\cap\operatorname{Dom}(R)$$

---

### 벡터장의 시각화

벡터장은 여러 점에 벡터를 그려 표현한다.

벡터의 방향은 장의 흐름 방향을 나타내고, 벡터의 길이는 장의 세기를 나타낸다.

---

### 속도장

유체가 움직일 때 각 점에서의 속도를 나타내는 벡터장을 속도장이라고 한다.

$$\mathbf{v}(x,y,z)$$

---

### 힘장

중력장, 전기장과 같이 각 점에서 작용하는 힘을 나타내는 벡터장을 힘장이라고 한다.

$$\mathbf{F}(x,y,z)$$

---

### 방사형 벡터장

원점에서 바깥쪽으로 향하는 대표적인 방사형 벡터장은

$$\mathbf{F}(x,y)=\langle x,y\rangle$$

이다.

원점으로 향하는 장은

$$\mathbf{F}(x,y)=\langle -x,-y\rangle$$

이다.

---

### 회전형 벡터장

원점을 중심으로 회전하는 대표적인 벡터장은

$$\mathbf{F}(x,y)=\langle -y,x\rangle$$

이다.

---

### 적용 조건과 주의사항

- 벡터장은 스칼라값 함수와 다르다.
- 성분함수의 정의역을 모두 확인해야 한다.
- 같은 벡터장이라도 그림에서는 화살표 길이를 일정 비율로 조정할 수 있다.
- 벡터장의 방향과 크기를 따로 해석해야 한다.
- 벡터장의 각 성분은 좌표별 변화량을 나타낸다.

---

## 6.2 Line Integrals
## 선적분

### 스칼라함수의 선적분

매끄러운 곡선 $C$가

$$\mathbf{r}(t)=\langle x(t),y(t),z(t)\rangle,\qquad a\le t\le b$$

로 주어질 때 스칼라함수 $f$의 선적분은

$$\int_C f\,ds=\int_a^b f(\mathbf{r}(t))\|\mathbf{r}'(t)\|\,dt$$

이다.

성분으로 쓰면

$$\int_C f\,ds=\int_a^b f(x(t),y(t),z(t))\sqrt{[x'(t)]^2+[y'(t)]^2+[z'(t)]^2}\,dt$$

이다.

---

### 질량

곡선 $C$에 선밀도 $\rho$가 주어지면 질량은

$$m=\int_C \rho\,ds$$

이다.

---

### 곡선의 질량중심

질량 $m$에 대해

$$\bar{x}=\frac{1}{m}\int_C x\rho\,ds$$

$$\bar{y}=\frac{1}{m}\int_C y\rho\,ds$$

$$\bar{z}=\frac{1}{m}\int_C z\rho\,ds$$

이다.

---

### 벡터장의 선적분

벡터장 $\mathbf{F}$와 방향을 가진 곡선 $C$에 대해

$$\int_C \mathbf{F}\cdot d\mathbf{r}$$

로 나타낸다.

곡선이

$$\mathbf{r}(t),\qquad a\le t\le b$$

로 주어지면

$$\int_C\mathbf{F}\cdot d\mathbf{r}=\int_a^b\mathbf{F}(\mathbf{r}(t))\cdot\mathbf{r}'(t)\,dt$$

이다.

---

### 성분형

2차원 벡터장

$$\mathbf{F}=\langle P,Q\rangle$$

에 대해

$$\int_C\mathbf{F}\cdot d\mathbf{r}=\int_C P\,dx+Q\,dy$$

이다.

3차원에서는

$$\int_C\mathbf{F}\cdot d\mathbf{r}=\int_C P\,dx+Q\,dy+R\,dz$$

이다.

---

### 일

힘장 $\mathbf{F}$가 입자를 곡선 $C$를 따라 이동시킬 때 한 일은

$$W=\int_C\mathbf{F}\cdot d\mathbf{r}$$

이다.

---

### 방향 반전

곡선의 방향을 반대로 하면

$$\int_{-C}\mathbf{F}\cdot d\mathbf{r}=-\int_C\mathbf{F}\cdot d\mathbf{r}$$

이다.

그러나 스칼라 선적분은 방향에 영향을 받지 않는다.

$$\int_{-C}f\,ds=\int_C f\,ds$$

---

### 구간별 매끄러운 곡선

곡선이 여러 조각으로 이루어지면

$$C=C_1\cup C_2\cup\cdots\cup C_n$$

이고

$$\int_C\mathbf{F}\cdot d\mathbf{r}=\sum_{k=1}^{n}\int_{C_k}\mathbf{F}\cdot d\mathbf{r}$$

이다.

---

### 적용 조건과 주의사항

- 스칼라 선적분에는 $\|\mathbf{r}'(t)\|$가 들어간다.
- 벡터장 선적분에는 $\mathbf{F}\cdot\mathbf{r}'(t)$가 들어간다.
- 벡터장 선적분은 곡선의 방향에 의존한다.
- 매개화가 곡선을 중복 추적하지 않는지 확인해야 한다.
- 곡선이 여러 조각이면 각 조각을 따로 적분한다.

---

## 6.3 Conservative Vector Fields
## 보존적 벡터장

### 보존적 벡터장

벡터장 $\mathbf{F}$가 어떤 스칼라함수 $f$의 그래디언트로 표현되면 보존적 벡터장이라고 한다.

$$\mathbf{F}=\nabla f$$

이때 $f$를 퍼텐셜 함수라고 한다.

---

### 2차원 보존적 벡터장

$$\mathbf{F}(x,y)=\langle P(x,y),Q(x,y)\rangle$$

가 보존적이면

$$f_x=P$$

$$f_y=Q$$

를 만족하는 함수 $f$가 존재한다.

---

### 3차원 보존적 벡터장

$$\mathbf{F}(x,y,z)=\langle P,Q,R\rangle$$

가 보존적이면

$$f_x=P,\qquad f_y=Q,\qquad f_z=R$$

를 만족하는 퍼텐셜 함수가 존재한다.

---

### 선적분의 기본정리

$\mathbf{F}=\nabla f$이고 곡선 $C$가 점 $A$에서 점 $B$로 향하면

$$\int_C\mathbf{F}\cdot d\mathbf{r}=f(B)-f(A)$$

이다.

---

### 경로독립성

보존적 벡터장의 선적분은 경로에 의존하지 않고 시작점과 끝점에만 의존한다.

즉, 같은 두 점을 연결하는 두 곡선 $C_1,C_2$에 대해

$$\int_{C_1}\mathbf{F}\cdot d\mathbf{r}=\int_{C_2}\mathbf{F}\cdot d\mathbf{r}$$

이다.

---

### 폐곡선에서의 선적분

보존적 벡터장에 대해 폐곡선 $C$에서는

$$\oint_C\mathbf{F}\cdot d\mathbf{r}=0$$

이다.

---

### 2차원 판정조건

벡터장

$$\mathbf{F}=\langle P,Q\rangle$$

에서 $P,Q$의 편도함수가 연속이고 정의역이 단순연결영역이면

$$P_y=Q_x$$

는 $\mathbf{F}$가 보존적인 것과 동치다.

---

### 3차원 판정조건

3차원에서

$$\nabla\times\mathbf{F}=\mathbf{0}$$

이고 정의역이 단순연결이면 $\mathbf{F}$는 보존적이다.

---

### 퍼텐셜 함수 구하기

$$f_x=P$$

를 $x$에 대해 적분하면

$$f(x,y)=\int P(x,y)\,dx+g(y)$$

이다.

그다음 $f_y=Q$를 이용하여 $g(y)$를 결정한다.

3차원에서는 적분상수가 나머지 변수들의 함수가 된다.

---

### 단순연결영역

영역 내부에 구멍이 없고 모든 폐곡선을 영역 안에서 한 점으로 연속적으로 줄일 수 있는 영역을 단순연결영역이라고 한다.

---

### 적용 조건과 주의사항

- $P_y=Q_x$만으로 항상 보존성을 결론 낼 수는 없다.
- 정의역의 단순연결성을 확인해야 한다.
- 퍼텐셜 함수의 적분상수는 다른 변수의 함수가 될 수 있다.
- 보존적 벡터장의 선적분은 끝점만으로 계산할 수 있다.
- 폐곡선 적분이 $0$인 성질은 보존적 장에서 성립한다.

---

## 6.4 Green's Theorem
## Green 정리

### 양의 방향

단순폐곡선 $C$의 양의 방향은 곡선을 따라 움직일 때 영역이 왼쪽에 놓이는 방향이다.

평면에서는 일반적으로 반시계방향이다.

---

### Green 정리

양의 방향을 가진 단순폐곡선 $C$가 영역 $D$의 경계이고 $P,Q$가 필요한 연속 편도함수를 가지면

$$\oint_C P\,dx+Q\,dy=\iint_D\left(\frac{\partial Q}{\partial x}-\frac{\partial P}{\partial y}\right)\,dA$$

이다.

---

### 순환형 Green 정리

$$\oint_C\mathbf{F}\cdot d\mathbf{r}=\iint_D(Q_x-P_y)\,dA$$

이다.

이 식은 경계에서의 순환과 내부의 회전량을 연결한다.

---

### 유출형 Green 정리

바깥쪽 단위법선벡터를 $\mathbf{n}$이라고 하면

$$\oint_C\mathbf{F}\cdot\mathbf{n}\,ds=\iint_D(P_x+Q_y)\,dA$$

이다.

---

### 넓이 공식

Green 정리를 이용하면 영역 $D$의 넓이를 다음과 같이 구할 수 있다.

$$A=\oint_C x\,dy$$

$$A=-\oint_C y\,dx$$

$$A=\frac{1}{2}\oint_C(x\,dy-y\,dx)$$

---

### 여러 경계성분

영역에 구멍이 있으면 바깥 경계는 반시계방향, 안쪽 경계는 시계방향으로 잡는다.

---

### 적용 조건과 주의사항

- 곡선은 닫혀 있어야 한다.
- 경계의 방향은 양의 방향이어야 한다.
- $P,Q$의 필요한 편도함수가 연속이어야 한다.
- 영역에 구멍이 있으면 안쪽 경계의 방향은 반대다.
- Green 정리는 선적분을 이중적분으로 바꾸거나 그 반대로 바꾼다.

---

## 6.5 Divergence and Curl
## 발산과 회전

### 발산

3차원 벡터장

$$\mathbf{F}=\langle P,Q,R\rangle$$

의 발산은

$$\nabla\cdot\mathbf{F}=P_x+Q_y+R_z$$

이다.

2차원에서는

$$\nabla\cdot\mathbf{F}=P_x+Q_y$$

이다.

---

### 발산의 의미

발산은 한 점에서 벡터장이 얼마나 퍼져나가거나 모이는지를 나타낸다.

- 양의 발산: 원천
- 음의 발산: 흡수
- 발산이 $0$: 국소적으로 순유출이 없음

---

### 회전

3차원 벡터장의 회전은

$$\nabla\times\mathbf{F}=\begin{vmatrix}\mathbf{i}&\mathbf{j}&\mathbf{k}\\\frac{\partial}{\partial x}&\frac{\partial}{\partial y}&\frac{\partial}{\partial z}\\P&Q&R\end{vmatrix}$$

이다.

성분으로 쓰면

$$\nabla\times\mathbf{F}=\langle R_y-Q_z,\ P_z-R_x,\ Q_x-P_y\rangle$$

이다.

---

### 2차원 회전

2차원 벡터장

$$\mathbf{F}=\langle P,Q\rangle$$

의 회전은 보통 스칼라로

$$Q_x-P_y$$

로 나타낸다.

3차원 벡터로 해석하면

$$\nabla\times\mathbf{F}=\langle0,0,Q_x-P_y\rangle$$

이다.

---

### 회전의 의미

회전은 벡터장이 한 점 근처에서 얼마나 회전하려는지를 나타낸다.

회전벡터의 방향은 회전축을, 크기는 회전의 세기를 나타낸다.

---

### 보존적 벡터장과 회전

필요한 편도함수가 연속이면

$$\mathbf{F}=\nabla f$$

에 대해

$$\nabla\times\mathbf{F}=\mathbf{0}$$

이다.

---

### 기본 항등식

스칼라함수 $f$에 대해

$$\nabla\times(\nabla f)=\mathbf{0}$$

이다.

벡터장 $\mathbf{F}$에 대해

$$\nabla\cdot(\nabla\times\mathbf{F})=0$$

이다.

---

### 라플라시안

스칼라함수 $f$의 라플라시안은

$$\nabla^2f=\nabla\cdot(\nabla f)$$

이다.

3차원에서는

$$\nabla^2f=f_{xx}+f_{yy}+f_{zz}$$

이다.

---

### 적용 조건과 주의사항

- 발산의 결과는 스칼라다.
- 회전의 결과는 3차원에서 벡터다.
- 보존적 장이면 회전은 $0$이지만, 역은 정의역 조건이 필요하다.
- 발산과 회전은 서로 다른 기하학적 의미를 가진다.
- 미분연산의 순서를 정확히 구분해야 한다.

---

## 6.6 Surface Integrals
## 면적분

### 매개곡면

곡면 $S$가 두 매개변수 $u,v$에 의해

$$\mathbf{r}(u,v)=\langle x(u,v),y(u,v),z(u,v)\rangle$$

로 주어지면 이를 매개곡면이라고 한다.

---

### 접선벡터

곡면의 두 접선벡터는

$$\mathbf{r}_u=\frac{\partial\mathbf{r}}{\partial u}$$

$$\mathbf{r}_v=\frac{\partial\mathbf{r}}{\partial v}$$

이다.

---

### 법선벡터

곡면의 법선벡터는

$$\mathbf{r}_u\times\mathbf{r}_v$$

이다.

단,

$$\mathbf{r}_u\times\mathbf{r}_v\ne\mathbf{0}$$

이어야 한다.

---

### 곡면적

매개곡면의 넓이는

$$A(S)=\iint_D\|\mathbf{r}_u\times\mathbf{r}_v\|\,dA$$

이다.

---

### 그래프형 곡면의 넓이

곡면이

$$z=g(x,y)$$

형태이면

$$A(S)=\iint_D\sqrt{1+g_x^2+g_y^2}\,dA$$

이다.

---

### 스칼라함수의 면적분

곡면 $S$ 위에서 스칼라함수 $f$의 면적분은

$$\iint_S f\,dS=\iint_D f(\mathbf{r}(u,v))\|\mathbf{r}_u\times\mathbf{r}_v\|\,dA$$

이다.

---

### 곡면의 질량

면밀도 $\rho$가 주어지면 질량은

$$m=\iint_S \rho\,dS$$

이다.

---

### 방향을 가진 곡면

곡면의 각 점에서 연속적으로 단위법선벡터를 선택할 수 있으면 방향가능곡면이라고 한다.

선택된 단위법선벡터는

$$\mathbf{n}=\frac{\mathbf{r}_u\times\mathbf{r}_v}{\|\mathbf{r}_u\times\mathbf{r}_v\|}$$

이다.

---

### 벡터장의 플럭스

벡터장 $\mathbf{F}$가 방향을 가진 곡면 $S$를 통과하는 플럭스는

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS$$

이다.

매개화하면

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS=\iint_D\mathbf{F}(\mathbf{r}(u,v))\cdot(\mathbf{r}_u\times\mathbf{r}_v)\,dA$$

이다.

---

### 그래프형 곡면의 플럭스

곡면이

$$z=g(x,y)$$

이고 위쪽 방향이면 법선벡터 요소는

$$\langle-g_x,-g_y,1\rangle\,dA$$

이다.

따라서

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS=\iint_D\mathbf{F}(x,y,g(x,y))\cdot\langle-g_x,-g_y,1\rangle\,dA$$

이다.

아래쪽 방향이면 부호가 반대다.

---

### 닫힌 곡면

경계가 없는 곡면을 닫힌 곡면이라고 한다.

닫힌 곡면에서는 일반적으로 바깥쪽 방향을 양의 방향으로 선택한다.

---

### 적용 조건과 주의사항

- 곡면적 적분에는 $\|\mathbf{r}_u\times\mathbf{r}_v\|$가 들어간다.
- 플럭스 적분에는 방향이 있으므로 법선벡터의 부호가 중요하다.
- 매개변수 순서를 바꾸면 외적의 방향이 반대가 된다.
- 곡면이 방향가능한지 확인해야 한다.
- 닫힌 곡면에서는 보통 바깥쪽 법선을 사용한다.

---

## 6.7 Stokes' Theorem
## Stokes 정리

### 경계곡선의 방향

방향을 가진 곡면 $S$의 경계곡선 $C$의 양의 방향은 오른손법칙으로 결정한다.

오른손 엄지가 곡면의 법선방향을 가리킬 때 손가락이 감기는 방향이 경계의 양의 방향이다.

---

### Stokes 정리

방향을 가진 매끄러운 곡면 $S$의 경계가 $C$이고 벡터장 $\mathbf{F}$가 필요한 연속 편도함수를 가지면

$$\oint_C\mathbf{F}\cdot d\mathbf{r}=\iint_S(\nabla\times\mathbf{F})\cdot\mathbf{n}\,dS$$

이다.

---

### 의미

Stokes 정리는 경계곡선에서의 순환과 곡면 위 회전의 총량을 연결한다.

---

### 곡면 선택

같은 경계곡선 $C$를 가지는 여러 곡면 중 계산이 쉬운 곡면을 선택할 수 있다.

단, 곡면의 방향은 경계방향과 일치해야 한다.

---

### 폐곡선 적분

경계가 없는 닫힌 곡면에서는

$$\partial S=\varnothing$$

이므로 Stokes 정리에 의해 회전의 총 플럭스는 $0$이다.

$$\iint_S(\nabla\times\mathbf{F})\cdot\mathbf{n}\,dS=0$$

---

### Green 정리와의 관계

Green 정리는 평면영역에 대한 Stokes 정리의 특수한 경우다.

---

### 적용 조건과 주의사항

- 경계곡선의 방향과 곡면 법선방향이 일치해야 한다.
- 경계가 같은 다른 곡면으로 바꿔 계산할 수 있다.
- 벡터장의 필요한 편도함수가 연속이어야 한다.
- 곡면이 조각별로 매끄럽고 방향가능해야 한다.
- 방향을 반대로 바꾸면 양변의 부호가 모두 바뀐다.

---

## 6.8 The Divergence Theorem
## 발산정리

### 발산정리

닫힌 곡면 $S$가 공간영역 $E$의 경계이고 바깥쪽 방향을 가지며 벡터장 $\mathbf{F}$가 필요한 연속 편도함수를 가지면

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS=\iiint_E\nabla\cdot\mathbf{F}\,dV$$

이다.

---

### 의미

발산정리는 닫힌 곡면을 통과하는 총 유출량과 내부 전체의 발산량을 연결한다.

---

### 바깥쪽 방향

닫힌 곡면에서는 법선벡터를 영역의 바깥쪽으로 선택한다.

안쪽 방향을 사용하면 결과의 부호가 반대가 된다.

---

### 여러 조각으로 이루어진 곡면

닫힌 곡면이 여러 곡면 조각으로 이루어지면

$$S=S_1\cup S_2\cup\cdots\cup S_n$$

이고

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS=\sum_{k=1}^{n}\iint_{S_k}\mathbf{F}\cdot\mathbf{n}\,dS$$

이다.

---

### 구멍이 있는 영역

영역 내부에 빈 공간이 있으면 바깥 경계는 외부방향, 내부 경계는 빈 공간 쪽을 향하는 방향이 영역 기준의 바깥쪽 방향이다.

---

### 발산이 $0$인 경우

영역 안에서

$$\nabla\cdot\mathbf{F}=0$$

이면 닫힌 곡면을 통과하는 총 플럭스는

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS=0$$

이다.

---

### 적용 조건과 주의사항

- 곡면은 닫혀 있어야 한다.
- 법선방향은 바깥쪽이어야 한다.
- 벡터장의 필요한 편도함수가 연속이어야 한다.
- 열린 곡면에는 발산정리를 직접 적용할 수 없다.
- 곡면적분을 삼중적분으로 바꾸면 계산이 단순해질 수 있다.
- 내부에 특이점이 있으면 정리의 적용조건을 다시 확인해야 한다.

---

## Chapter 6 핵심 공식 요약

### 스칼라 선적분

$$\int_C f\,ds=\int_a^b f(\mathbf{r}(t))\|\mathbf{r}'(t)\|\,dt$$

### 벡터장 선적분

$$\int_C\mathbf{F}\cdot d\mathbf{r}=\int_a^b\mathbf{F}(\mathbf{r}(t))\cdot\mathbf{r}'(t)\,dt$$

### 선적분의 기본정리

$$\int_C\nabla f\cdot d\mathbf{r}=f(B)-f(A)$$

### Green 정리

$$\oint_C P\,dx+Q\,dy=\iint_D(Q_x-P_y)\,dA$$

### 발산

$$\nabla\cdot\mathbf{F}=P_x+Q_y+R_z$$

### 회전

$$\nabla\times\mathbf{F}=\langle R_y-Q_z,\ P_z-R_x,\ Q_x-P_y\rangle$$

### 곡면적

$$A(S)=\iint_D\|\mathbf{r}_u\times\mathbf{r}_v\|\,dA$$

### 플럭스

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS$$

### Stokes 정리

$$\oint_C\mathbf{F}\cdot d\mathbf{r}=\iint_S(\nabla\times\mathbf{F})\cdot\mathbf{n}\,dS$$

### 발산정리

$$\iint_S\mathbf{F}\cdot\mathbf{n}\,dS=\iiint_E\nabla\cdot\mathbf{F}\,dV$$

---

## 자주 혼동하는 사항

- 스칼라 선적분과 벡터장 선적분의 공식은 다르다.
- 벡터장 선적분은 곡선의 방향에 의존한다.
- $P_y=Q_x$만으로 보존성을 결론 내리려면 정의역 조건이 필요하다.
- Green 정리는 평면의 닫힌 곡선에 적용한다.
- 발산의 결과는 스칼라이고 회전의 결과는 벡터다.
- 곡면적에는 외적의 크기가 들어가고 플럭스에는 방향 있는 법선벡터가 들어간다.
- Stokes 정리에서는 경계방향과 법선방향을 오른손법칙으로 맞춘다.
- 발산정리는 닫힌 곡면과 바깥쪽 법선을 사용한다.
