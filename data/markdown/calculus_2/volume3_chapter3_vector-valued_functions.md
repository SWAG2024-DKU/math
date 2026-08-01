# Calculus Volume 3 — Chapter 3
# Vector-Valued Functions / 벡터값 함수

## 선수 개념

- 2차원 벡터
- 3차원 벡터
- 벡터의 크기
- 단위벡터
- 내적
- 외적
- 매개방정식
- 함수의 극한
- 함수의 연속
- 미분법
- 연쇄법칙
- 적분법
- 호의 길이
- 접선과 법선
- 원운동
- 속도와 가속도

---

## 3.1 Vector-Valued Functions and Space Curves
## 벡터값 함수와 공간곡선

### 벡터값 함수의 정의

실수 $t$에 벡터를 대응시키는 함수를 벡터값 함수라고 한다.

3차원에서는 보통

$$\mathbf{r}(t)=\langle f(t),g(t),h(t)\rangle$$

로 쓴다.

또는

$$\mathbf{r}(t)=f(t)\mathbf{i}+g(t)\mathbf{j}+h(t)\mathbf{k}$$

로 나타낼 수 있다.

- $f(t)$: $x$성분
- $g(t)$: $y$성분
- $h(t)$: $z$성분

---

### 벡터값 함수의 정의역

벡터값 함수의 정의역은 모든 성분함수 정의역의 교집합이다.

$$\operatorname{Dom}(\mathbf{r})=\operatorname{Dom}(f)\cap\operatorname{Dom}(g)\cap\operatorname{Dom}(h)$$

---

### 공간곡선

벡터값 함수

$$\mathbf{r}(t)=\langle x(t),y(t),z(t)\rangle$$

는 매개방정식

$$x=x(t),\qquad y=y(t),\qquad z=z(t)$$

을 갖는 공간곡선을 나타낸다.

$t$가 증가함에 따라 점

$$(x(t),y(t),z(t))$$

가 공간에서 이동한다.

---

### 평면곡선의 벡터표현

평면곡선도 3차원 벡터값 함수로 표현할 수 있다.

$$\mathbf{r}(t)=\langle x(t),y(t),0\rangle$$

예를 들어 반지름이 $a$인 원은

$$\mathbf{r}(t)=\langle a\cos t,a\sin t,0\rangle$$

이다.

---

### 나선곡선

대표적인 공간곡선은 원형 나선이다.

$$\mathbf{r}(t)=\langle a\cos t,a\sin t,bt\rangle$$

$xy$평면으로의 사영은 반지름이 $a$인 원이고, $z$좌표는 $bt$에 따라 선형적으로 변한다.

---

### 벡터값 함수의 극한

$$\mathbf{r}(t)=\langle f(t),g(t),h(t)\rangle$$

이면

$$\lim_{t\to a}\mathbf{r}(t)=\left\langle \lim_{t\to a}f(t),\lim_{t\to a}g(t),\lim_{t\to a}h(t)\right\rangle$$

이다.

각 성분의 극한이 모두 존재해야 전체 극한이 존재한다.

---

### 벡터값 함수의 연속

$\mathbf{r}(t)$가 $t=a$에서 연속이라는 것은

$$\lim_{t\to a}\mathbf{r}(t)=\mathbf{r}(a)$$

라는 뜻이다.

이는 각 성분함수가 $a$에서 연속인 것과 동치다.

---

### 같은 곡선의 다른 매개화

같은 기하학적 곡선은 여러 벡터값 함수로 나타낼 수 있다.

매개화가 달라지면 다음이 달라질 수 있다.

- 진행 방향
- 이동 속도
- 곡선을 추적하는 횟수
- 매개변수의 범위

---

### 곡선의 교점

두 곡선

$$\mathbf{r}_1(t),\qquad \mathbf{r}_2(s)$$

가 만나는 점은

$$\mathbf{r}_1(t)=\mathbf{r}_2(s)$$

를 만족하는 $t,s$를 찾아 결정한다.

두 곡선은 같은 공간점을 지나더라도 같은 시간이나 같은 방향으로 통과하지 않을 수 있다.

---

### 적용 조건과 주의사항

- 벡터값 함수의 정의역은 성분별 정의역의 교집합이다.
- 공간곡선의 모양과 진행 방향을 함께 확인해야 한다.
- 같은 곡선을 여러 번 추적할 수 있다.
- 두 곡선의 교점은 서로 다른 매개변수를 사용하여 비교해야 한다.
- 매개변수를 제거하면 곡선의 진행 방향 정보가 사라진다.

---

## 3.2 Calculus of Vector-Valued Functions
## 벡터값 함수의 미적분

### 도함수의 정의

벡터값 함수의 도함수는

$$\mathbf{r}'(t)=\lim_{h\to0}\frac{\mathbf{r}(t+h)-\mathbf{r}(t)}{h}$$

로 정의한다.

---

### 성분별 미분

$$\mathbf{r}(t)=\langle f(t),g(t),h(t)\rangle$$

이면

$$\mathbf{r}'(t)=\langle f'(t),g'(t),h'(t)\rangle$$

이다.

---

### 접선벡터

$$\mathbf{r}'(t)$$

는 곡선의 접선 방향을 나타낸다.

$t=t_0$에서 접선벡터는

$$\mathbf{r}'(t_0)$$

이다.

단,

$$\mathbf{r}'(t_0)\ne\mathbf{0}$$

이어야 일반적인 접선 방향이 정의된다.

---

### 접선의 벡터방정식

점 $\mathbf{r}(t_0)$에서의 접선은

$$\mathbf{L}(s)=\mathbf{r}(t_0)+s\mathbf{r}'(t_0)$$

이다.

---

### 단위접선벡터

$$\mathbf{r}'(t)\ne\mathbf{0}$$

일 때 단위접선벡터는

$$\mathbf{T}(t)=\frac{\mathbf{r}'(t)}{\|\mathbf{r}'(t)\|}$$

이다.

---

### 고계도함수

벡터값 함수도 성분별로 반복 미분할 수 있다.

$$\mathbf{r}''(t)=\langle f''(t),g''(t),h''(t)\rangle$$

일반적으로

$$\mathbf{r}^{(n)}(t)=\left\langle f^{(n)}(t),g^{(n)}(t),h^{(n)}(t)\right\rangle$$

이다.

---

### 벡터 미분법칙

벡터값 함수 $\mathbf{u}(t),\mathbf{v}(t)$와 스칼라함수 $f(t)$에 대해 다음이 성립한다.

$$\frac{d}{dt}[\mathbf{u}+\mathbf{v}]=\mathbf{u}'+\mathbf{v}'$$

$$\frac{d}{dt}[f\mathbf{u}]=f'\mathbf{u}+f\mathbf{u}'$$

$$\frac{d}{dt}[\mathbf{u}\cdot\mathbf{v}]=\mathbf{u}'\cdot\mathbf{v}+\mathbf{u}\cdot\mathbf{v}'$$

$$\frac{d}{dt}[\mathbf{u}\times\mathbf{v}]=\mathbf{u}'\times\mathbf{v}+\mathbf{u}\times\mathbf{v}'$$

---

### 합성함수의 미분

벡터값 함수 $\mathbf{u}$와 스칼라함수 $g$에 대해

$$\frac{d}{dt}\mathbf{u}(g(t))=\mathbf{u}'(g(t))g'(t)$$

이다.

---

### 크기가 일정한 벡터

$$\|\mathbf{r}(t)\|=C$$

가 상수이면

$$\mathbf{r}(t)\cdot\mathbf{r}(t)=C^2$$

이다.

양변을 미분하면

$$\mathbf{r}(t)\cdot\mathbf{r}'(t)=0$$

이다.

따라서 위치벡터의 크기가 일정하면 위치벡터와 접선벡터는 수직이다.

---

### 벡터값 함수의 부정적분

$$\mathbf{r}(t)=\langle f(t),g(t),h(t)\rangle$$

이면

$$\int\mathbf{r}(t)\,dt=\left\langle\int f(t)\,dt,\int g(t)\,dt,\int h(t)\,dt\right\rangle$$

이다.

적분상수는 상수벡터로 나타낸다.

$$\mathbf{C}=\langle C_1,C_2,C_3\rangle$$

따라서

$$\int\mathbf{r}(t)\,dt=\mathbf{R}(t)+\mathbf{C}$$

이다.

---

### 벡터값 함수의 정적분

$$\int_a^b\mathbf{r}(t)\,dt=\left\langle\int_a^b f(t)\,dt,\int_a^b g(t)\,dt,\int_a^b h(t)\,dt\right\rangle$$

이다.

---

### 벡터값 함수의 기본정리

$$\mathbf{R}'(t)=\mathbf{r}(t)$$

이면

$$\int_a^b\mathbf{r}(t)\,dt=\mathbf{R}(b)-\mathbf{R}(a)$$

이다.

---

### 초기값 문제

속도벡터가 주어졌을 때 위치벡터는

$$\mathbf{r}(t)=\int\mathbf{v}(t)\,dt+\mathbf{C}$$

로 구한다.

초기조건

$$\mathbf{r}(t_0)=\mathbf{r}_0$$

을 이용하여 상수벡터를 결정한다.

---

### 적용 조건과 주의사항

- 벡터값 함수의 미분과 적분은 성분별로 수행한다.
- 접선벡터가 영벡터인 점에서는 접선 방향을 별도로 조사해야 한다.
- 내적과 외적의 미분에는 각각 곱의 미분법이 적용된다.
- 외적은 순서가 중요하다.
- 적분상수는 하나의 스칼라가 아니라 상수벡터다.

---

## 3.3 Arc Length and Curvature
## 호의 길이와 곡률

### 호의 길이

매끄러운 곡선

$$\mathbf{r}(t)=\langle x(t),y(t),z(t)\rangle,\qquad a\le t\le b$$

의 길이는

$$L=\int_a^b\|\mathbf{r}'(t)\|\,dt$$

이다.

성분으로 쓰면

$$L=\int_a^b\sqrt{[x'(t)]^2+[y'(t)]^2+[z'(t)]^2}\,dt$$

이다.

---

### 매끄러운 곡선

곡선이 매끄럽다는 것은 일반적으로

$$\mathbf{r}'(t)$$

가 연속이고

$$\mathbf{r}'(t)\ne\mathbf{0}$$

인 것을 의미한다.

구간별로 이러한 조건을 만족하면 구간별 매끄러운 곡선이라고 한다.

---

### 호의 길이 함수

고정된 시작점 $t=a$에서 현재 시각 $t$까지의 호의 길이를

$$s(t)=\int_a^t\|\mathbf{r}'(u)\|\,du$$

로 정의한다.

미적분학의 기본정리에 의해

$$\frac{ds}{dt}=\|\mathbf{r}'(t)\|$$

이다.

---

### 호의 길이 매개변수

곡선을 호의 길이 $s$로 매개화하면

$$\left\|\frac{d\mathbf{r}}{ds}\right\|=1$$

이다.

즉, 호의 길이 매개변수에서는 단위속력으로 곡선을 추적한다.

---

### 곡률의 정의

곡률은 곡선이 얼마나 빠르게 방향을 바꾸는지를 나타낸다.

$$\kappa=\left\|\frac{d\mathbf{T}}{ds}\right\|$$

이다.

일반 매개변수 $t$를 사용하면

$$\kappa=\frac{\|\mathbf{T}'(t)\|}{\|\mathbf{r}'(t)\|}$$

이다.

---

### 외적을 이용한 곡률 공식

$$\mathbf{r}'(t)\ne\mathbf{0}$$

일 때

$$\kappa=\frac{\|\mathbf{r}'(t)\times\mathbf{r}''(t)\|}{\|\mathbf{r}'(t)\|^3}$$

이다.

---

### 평면곡선의 곡률

평면곡선

$$y=f(x)$$

의 곡률은

$$\kappa=\frac{|f''(x)|}{[1+(f'(x))^2]^{3/2}}$$

이다.

매개곡선

$$x=x(t),\qquad y=y(t)$$

에서는

$$\kappa=\frac{|x'(t)y''(t)-y'(t)x''(t)|}{\left([x'(t)]^2+[y'(t)]^2\right)^{3/2}}$$

이다.

---

### 단위주법선벡터

$$\mathbf{T}'(t)\ne\mathbf{0}$$

일 때 단위주법선벡터는

$$\mathbf{N}(t)=\frac{\mathbf{T}'(t)}{\|\mathbf{T}'(t)\|}$$

이다.

$\mathbf{N}(t)$는 곡선이 휘어지는 방향을 나타낸다.

---

### 단위종법선벡터

단위종법선벡터는

$$\mathbf{B}(t)=\mathbf{T}(t)\times\mathbf{N}(t)$$

이다.

$\mathbf{T},\mathbf{N},\mathbf{B}$는 서로 수직인 단위벡터다.

---

### Frenet frame

세 벡터

$$\mathbf{T},\qquad \mathbf{N},\qquad \mathbf{B}$$

를 함께 Frenet frame이라고 한다.

- $\mathbf{T}$: 진행 방향
- $\mathbf{N}$: 휘어지는 방향
- $\mathbf{B}$: 두 방향에 모두 수직인 방향

---

### 곡률반지름

곡률이

$$\kappa\ne0$$

이면 곡률반지름은

$$\rho=\frac{1}{\kappa}$$

이다.

곡률이 클수록 곡률반지름은 작고 곡선은 더 급하게 휜다.

---

### 접촉원

곡선에 한 점에서 가장 잘 맞는 원을 접촉원이라고 한다.

접촉원의 중심은

$$\mathbf{C}=\mathbf{r}+\frac{1}{\kappa}\mathbf{N}$$

으로 나타낼 수 있다.

---

### 원의 곡률

반지름이 $R$인 원의 곡률은

$$\kappa=\frac{1}{R}$$

이다.

---

### 적용 조건과 주의사항

- 호의 길이에서는 속도벡터가 아니라 그 크기를 적분한다.
- 곡률 공식은 $\mathbf{r}'(t)\ne\mathbf{0}$인 점에서 사용한다.
- 단위법선벡터는 $\mathbf{T}'(t)\ne\mathbf{0}$일 때 정의된다.
- 직선의 곡률은 $0$이다.
- 원의 곡률은 반지름의 역수다.
- 곡률은 곡선의 모양에 관한 양이며 매개화 방식에는 의존하지 않는다.

---

## 3.4 Motion in Space
## 공간에서의 운동

### 위치벡터

시간 $t$에서 입자의 위치를

$$\mathbf{r}(t)=\langle x(t),y(t),z(t)\rangle$$

로 나타낸다.

---

### 속도벡터

속도벡터는 위치벡터의 도함수다.

$$\mathbf{v}(t)=\mathbf{r}'(t)$$

속도벡터는 이동 방향과 변화율을 함께 나타낸다.

---

### 속력

속력은 속도벡터의 크기다.

$$v(t)=\|\mathbf{v}(t)\|=\|\mathbf{r}'(t)\|$$

속력은 스칼라다.

---

### 가속도벡터

가속도벡터는 속도벡터의 도함수다.

$$\mathbf{a}(t)=\mathbf{v}'(t)=\mathbf{r}''(t)$$

---

### 변위와 이동거리

시간구간 $[a,b]$에서 변위는

$$\mathbf{r}(b)-\mathbf{r}(a)$$

이다.

이동거리는

$$\int_a^b\|\mathbf{v}(t)\|\,dt$$

이다.

변위의 크기와 이동거리는 일반적으로 같지 않다.

---

### 가속도로부터 속도 구하기

가속도벡터가 주어지면

$$\mathbf{v}(t)=\int\mathbf{a}(t)\,dt+\mathbf{C}_1$$

이다.

초기속도를 이용해 $\mathbf{C}_1$을 구한다.

---

### 속도로부터 위치 구하기

속도벡터가 주어지면

$$\mathbf{r}(t)=\int\mathbf{v}(t)\,dt+\mathbf{C}_2$$

이다.

초기위치를 이용해 $\mathbf{C}_2$를 구한다.

---

### 접선방향과 법선방향의 가속도

가속도는 다음과 같이 분해할 수 있다.

$$\mathbf{a}=a_T\mathbf{T}+a_N\mathbf{N}$$

여기서

- $a_T$: 접선가속도
- $a_N$: 법선가속도

---

### 접선가속도

속력을 $v=\|\mathbf{v}\|$라고 하면

$$a_T=\frac{dv}{dt}$$

이다.

또는

$$a_T=\frac{\mathbf{v}\cdot\mathbf{a}}{\|\mathbf{v}\|}$$

이다.

접선가속도는 속력의 변화를 나타낸다.

---

### 법선가속도

법선가속도는

$$a_N=\kappa v^2$$

이다.

또한

$$a_N=\frac{\|\mathbf{v}\times\mathbf{a}\|}{\|\mathbf{v}\|}$$

로 계산할 수 있다.

법선가속도는 운동 방향의 변화를 나타낸다.

---

### 가속도의 크기

$\mathbf{T}$와 $\mathbf{N}$은 서로 수직이므로

$$\|\mathbf{a}\|^2=a_T^2+a_N^2$$

이다.

---

### 속력의 증가와 감소

$$\mathbf{v}\cdot\mathbf{a}>0$$

이면 속력이 증가한다.

$$\mathbf{v}\cdot\mathbf{a}<0$$

이면 속력이 감소한다.

$$\mathbf{v}\cdot\mathbf{a}=0$$

이면 순간적으로 속력이 변하지 않는다.

---

### 등속 원운동

반지름이 $R$인 원을 일정한 속력 $v$로 움직이면

$$a_T=0$$

이고

$$a_N=\frac{v^2}{R}$$

이다.

가속도는 원의 중심을 향한다.

---

### 발사체 운동

공기저항을 무시하고 중력만 작용한다고 하자.

초기위치가 $\mathbf{r}_0$, 초기속도가 $\mathbf{v}_0$, 중력가속도가

$$\mathbf{a}=\langle0,0,-g\rangle$$

이면 위치벡터는

$$\mathbf{r}(t)=\mathbf{r}_0+\mathbf{v}_0t+\frac{1}{2}\mathbf{a}t^2$$

이다.

즉,

$$\mathbf{r}(t)=\mathbf{r}_0+\mathbf{v}_0t-\frac{1}{2}gt^2\mathbf{k}$$

이다.

---

### 적용 조건과 주의사항

- 속도는 벡터이고 속력은 스칼라다.
- 이동거리와 변위의 크기는 일반적으로 다르다.
- 속력이 일정해도 방향이 변하면 가속도는 $0$이 아니다.
- 접선가속도는 속력 변화, 법선가속도는 방향 변화를 나타낸다.
- $a_N$은 음수가 아니라 크기로 정의된다.
- 발사체 운동에서는 중력방향의 부호를 좌표축 방향에 맞게 설정해야 한다.

---

## Chapter 3 핵심 공식 요약

### 벡터값 함수

$$\mathbf{r}(t)=\langle x(t),y(t),z(t)\rangle$$

### 미분

$$\mathbf{r}'(t)=\langle x'(t),y'(t),z'(t)\rangle$$

### 적분

$$\int\mathbf{r}(t)\,dt=\left\langle\int x(t)\,dt,\int y(t)\,dt,\int z(t)\,dt\right\rangle+\mathbf{C}$$

### 접선

$$\mathbf{L}(s)=\mathbf{r}(t_0)+s\mathbf{r}'(t_0)$$

### 단위접선벡터

$$\mathbf{T}(t)=\frac{\mathbf{r}'(t)}{\|\mathbf{r}'(t)\|}$$

### 호의 길이

$$L=\int_a^b\|\mathbf{r}'(t)\|\,dt$$

### 곡률

$$\kappa=\frac{\|\mathbf{T}'(t)\|}{\|\mathbf{r}'(t)\|}$$

$$\kappa=\frac{\|\mathbf{r}'(t)\times\mathbf{r}''(t)\|}{\|\mathbf{r}'(t)\|^3}$$

### 단위법선벡터

$$\mathbf{N}(t)=\frac{\mathbf{T}'(t)}{\|\mathbf{T}'(t)\|}$$

### 종법선벡터

$$\mathbf{B}(t)=\mathbf{T}(t)\times\mathbf{N}(t)$$

### 위치·속도·가속도

$$\mathbf{v}(t)=\mathbf{r}'(t)$$

$$\mathbf{a}(t)=\mathbf{r}''(t)$$

### 가속도 분해

$$\mathbf{a}=a_T\mathbf{T}+a_N\mathbf{N}$$

$$a_T=\frac{d}{dt}\|\mathbf{v}\|=\frac{\mathbf{v}\cdot\mathbf{a}}{\|\mathbf{v}\|}$$

$$a_N=\kappa\|\mathbf{v}\|^2=\frac{\|\mathbf{v}\times\mathbf{a}\|}{\|\mathbf{v}\|}$$

---

## 자주 혼동하는 사항

- 벡터값 함수의 정의역은 모든 성분함수 정의역의 교집합이다.
- 접선벡터와 단위접선벡터는 다르다.
- 벡터 적분의 적분상수는 상수벡터다.
- 호의 길이는 $\mathbf{r}'(t)$가 아니라 $\|\mathbf{r}'(t)\|$를 적분한다.
- 곡률 공식의 분모는 $\|\mathbf{r}'(t)\|^3$이다.
- 속도는 벡터이고 속력은 스칼라다.
- 속력이 일정해도 가속도가 존재할 수 있다.
- 접선가속도는 속력 변화, 법선가속도는 방향 변화를 나타낸다.
