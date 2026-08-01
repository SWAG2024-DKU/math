# Calculus Volume 3 — Chapter 5
# Multiple Integration / 다중적분

## 선수 개념

- 정적분
- 리만합
- 미적분학의 기본정리
- 반복적분
- 치환적분
- 부분적분
- 2차원 좌표계
- 3차원 좌표계
- 극좌표
- 원기둥좌표
- 구면좌표
- 영역의 경계
- 함수의 그래프
- 부피
- 질량중심
- 야코비안

---

## 5.1 Double Integrals over Rectangular Regions
## 직사각형 영역에서의 이중적분

### 이중적분의 정의

직사각형 영역

$$R=[a,b]\times[c,d]$$

에서 함수 $f(x,y)$의 이중적분은 리만합의 극한으로 정의한다.

$$\iint_R f(x,y)\,dA=\lim_{m,n\to\infty}\sum_{i=1}^{m}\sum_{j=1}^{n}f(x_{ij}^*,y_{ij}^*)\Delta A$$

여기서

$$\Delta A=\Delta x\Delta y$$

이다.

---

### 기하학적 의미

$f(x,y)\ge0$이면

$$\iint_R f(x,y)\,dA$$

는 곡면

$$z=f(x,y)$$

아래와 영역 $R$ 위에 놓인 입체의 부피를 나타낸다.

$f$가 음수가 될 수 있으면 부호를 고려한 순부피를 나타낸다.

---

### 반복적분

연속함수 $f$에 대해 Fubini 정리에 의해

$$\iint_R f(x,y)\,dA=\int_a^b\int_c^d f(x,y)\,dy\,dx$$

또는

$$\iint_R f(x,y)\,dA=\int_c^d\int_a^b f(x,y)\,dx\,dy$$

로 계산할 수 있다.

---

### 적분 순서

$$\int_a^b\int_c^d f(x,y)\,dy\,dx$$

에서는 먼저 $y$에 대해 적분하고 그다음 $x$에 대해 적분한다.

$$\int_c^d\int_a^b f(x,y)\,dx\,dy$$

에서는 먼저 $x$에 대해 적분한다.

---

### 상수함수의 이중적분

상수 $k$에 대해

$$\iint_R k\,dA=k\,\operatorname{Area}(R)$$

이다.

---

### 이중적분의 선형성

$$\iint_R [af+bg]\,dA=a\iint_R f\,dA+b\iint_R g\,dA$$

이다.

---

### 영역의 분할

영역 $R$이 겹치지 않는 두 영역 $R_1,R_2$로 분할되면

$$\iint_R f\,dA=\iint_{R_1}f\,dA+\iint_{R_2}f\,dA$$

이다.

---

### 평균값

영역 $R$에서 함수 $f$의 평균값은

$$f_{\mathrm{avg}}=\frac{1}{\operatorname{Area}(R)}\iint_R f(x,y)\,dA$$

이다.

---

### 적용 조건과 주의사항

- 반복적분에서는 안쪽 적분변수를 먼저 적분한다.
- 다른 변수는 안쪽 적분에서 상수로 취급한다.
- $dA$는 보통 $dx\,dy$ 또는 $dy\,dx$로 나타낸다.
- 함수가 음수인 부분이 있으면 결과는 기하학적 부피가 아니라 순부피다.
- 적분 순서를 바꾸기 전에 영역과 적분한계를 확인해야 한다.

---

## 5.2 Double Integrals over General Regions
## 일반 영역에서의 이중적분

### Type I 영역

영역 $D$가

$$D=\{(x,y):a\le x\le b,\ g_1(x)\le y\le g_2(x)\}$$

형태이면 Type I 영역이라고 한다.

이때

$$\iint_D f(x,y)\,dA=\int_a^b\int_{g_1(x)}^{g_2(x)}f(x,y)\,dy\,dx$$

이다.

---

### Type II 영역

영역 $D$가

$$D=\{(x,y):c\le y\le d,\ h_1(y)\le x\le h_2(y)\}$$

형태이면 Type II 영역이라고 한다.

이때

$$\iint_D f(x,y)\,dA=\int_c^d\int_{h_1(y)}^{h_2(y)}f(x,y)\,dx\,dy$$

이다.

---

### 적분순서 변경

적분순서를 바꾸려면 같은 영역을 새로운 방식으로 기술해야 한다.

예를 들어

$$\int_a^b\int_{g_1(x)}^{g_2(x)}f(x,y)\,dy\,dx$$

를

$$\int_c^d\int_{h_1(y)}^{h_2(y)}f(x,y)\,dx\,dy$$

형태로 바꾼다.

---

### 영역 분할

한 번에 Type I 또는 Type II로 표현하기 어려운 영역은 여러 부분으로 나누어 적분한다.

$$\iint_D f\,dA=\sum_k\iint_{D_k}f\,dA$$

---

### 넓이

영역 $D$의 넓이는

$$A=\iint_D 1\,dA$$

이다.

---

### 두 곡면 사이의 부피

위쪽 곡면이

$$z=f(x,y)$$

아래쪽 곡면이

$$z=g(x,y)$$

이고 $f\ge g$이면 부피는

$$V=\iint_D [f(x,y)-g(x,y)]\,dA$$

이다.

---

### 평균값

일반 영역 $D$에서 함수의 평균값은

$$f_{\mathrm{avg}}=\frac{1}{\operatorname{Area}(D)}\iint_D f(x,y)\,dA$$

이다.

---

### 적용 조건과 주의사항

- 적분한계는 영역의 경계를 정확히 나타내야 한다.
- 안쪽 적분한계는 바깥 변수의 함수가 될 수 있다.
- 순서를 바꾸면 적분한계도 모두 다시 설정해야 한다.
- 영역이 한 번에 표현되지 않으면 분할해야 한다.
- 부피에서는 항상 위쪽 함수에서 아래쪽 함수를 뺀다.

---

## 5.3 Double Integrals in Polar Coordinates
## 극좌표에서의 이중적분

### 극좌표 변환

직교좌표와 극좌표의 관계는

$$x=r\cos\theta,\qquad y=r\sin\theta$$

이다.

또한

$$x^2+y^2=r^2$$

이다.

---

### 면적요소

극좌표에서 면적요소는

$$dA=r\,dr\,d\theta$$

이다.

따라서

$$\iint_D f(x,y)\,dA=\iint_{D^*}f(r\cos\theta,r\sin\theta)\,r\,dr\,d\theta$$

이다.

---

### 일반적인 극좌표 영역

영역이

$$\alpha\le\theta\le\beta$$

$$g_1(\theta)\le r\le g_2(\theta)$$

로 주어지면

$$\iint_D f(x,y)\,dA=\int_\alpha^\beta\int_{g_1(\theta)}^{g_2(\theta)}f(r\cos\theta,r\sin\theta)\,r\,dr\,d\theta$$

이다.

---

### 원판

반지름이 $a$인 원판은

$$0\le r\le a,\qquad 0\le\theta\le2\pi$$

이다.

---

### 고리영역

내부반지름이 $a$, 외부반지름이 $b$인 고리영역은

$$a\le r\le b,\qquad 0\le\theta\le2\pi$$

이다.

---

### 원형 부채꼴

각도범위가 $\alpha\le\theta\le\beta$이고 반지름이 $a$이면

$$0\le r\le a,\qquad \alpha\le\theta\le\beta$$

이다.

---

### 극좌표가 유리한 경우

다음 형태가 나타나면 극좌표가 유용하다.

- 원 또는 원판
- 고리영역
- $x^2+y^2$
- $\sqrt{x^2+y^2}$
- 방사대칭 함수
- 극방정식으로 주어진 경계

---

### 적용 조건과 주의사항

- 극좌표 변환에서는 반드시 야코비안 인자 $r$을 포함해야 한다.
- $dA$를 단순히 $dr\,d\theta$로 쓰면 안 된다.
- 각도범위가 영역을 중복 추적하지 않는지 확인해야 한다.
- $r$의 범위는 안쪽 경계에서 바깥쪽 경계 순서로 설정한다.
- 직교좌표 함수의 모든 $x,y$를 극좌표로 바꿔야 한다.

---

## 5.4 Triple Integrals
## 삼중적분

### 삼중적분의 정의

공간영역 $E$에서 함수 $f(x,y,z)$의 삼중적분은

$$\iiint_E f(x,y,z)\,dV$$

로 나타낸다.

---

### 기하학적 의미

$f(x,y,z)\ge0$이면 삼중적분은 4차원적 해석보다는 밀도, 질량, 평균값 같은 물리량을 계산하는 데 주로 사용한다.

특히

$$\iiint_E 1\,dV$$

는 영역 $E$의 부피다.

---

### 직육면체 영역

$$E=[a,b]\times[c,d]\times[p,q]$$

이면

$$\iiint_E f\,dV=\int_a^b\int_c^d\int_p^q f(x,y,z)\,dz\,dy\,dx$$

등 여러 순서로 계산할 수 있다.

---

### 일반 공간영역

예를 들어 영역이

$$D=\{(x,y):(x,y)\text{가 평면영역 }D\text{에 속함}\}$$

위에서

$$u_1(x,y)\le z\le u_2(x,y)$$

로 주어지면

$$\iiint_E f\,dV=\iint_D\int_{u_1(x,y)}^{u_2(x,y)}f(x,y,z)\,dz\,dA$$

이다.

---

### 부피

공간영역 $E$의 부피는

$$V=\iiint_E 1\,dV$$

이다.

---

### 평균값

공간영역 $E$에서 함수 $f$의 평균값은

$$f_{\mathrm{avg}}=\frac{1}{\operatorname{Vol}(E)}\iiint_E f\,dV$$

이다.

---

### Fubini 정리

적절한 연속성 조건에서 삼중적분은 반복적분으로 계산할 수 있으며 적분순서를 바꿀 수 있다.

가능한 순서는 총 여섯 가지다.

$$dx\,dy\,dz,\quad dx\,dz\,dy,\quad dy\,dx\,dz$$

$$dy\,dz\,dx,\quad dz\,dx\,dy,\quad dz\,dy\,dx$$

---

### 적용 조건과 주의사항

- 적분순서에 따라 영역 기술 방식이 달라진다.
- 안쪽 적분한계는 바깥 변수들의 함수가 될 수 있다.
- 삼중적분에서 $dV$는 부피요소다.
- 영역을 정확히 투영하여 적분한계를 설정해야 한다.
- 계산이 쉬운 적분순서를 선택하는 것이 중요하다.

---

## 5.5 Triple Integrals in Cylindrical and Spherical Coordinates
## 원기둥좌표와 구면좌표의 삼중적분

### 원기둥좌표

원기둥좌표는

$$(r,\theta,z)$$

로 나타낸다.

직교좌표와의 관계는

$$x=r\cos\theta$$

$$y=r\sin\theta$$

$$z=z$$

이다.

또한

$$x^2+y^2=r^2$$

이다.

---

### 원기둥좌표의 부피요소

원기둥좌표에서

$$dV=r\,dr\,d\theta\,dz$$

이다.

적분순서에 따라

$$dV=r\,dz\,dr\,d\theta$$

등으로 쓸 수 있다.

---

### 원기둥좌표가 유리한 경우

다음과 같은 영역에서 유용하다.

- 원기둥
- 원뿔
- 회전체
- $z$축 대칭 영역
- $x^2+y^2$가 자주 나타나는 식

---

### 구면좌표

구면좌표는

$$(\rho,\theta,\phi)$$

로 나타낸다.

- $\rho$: 원점에서 점까지의 거리
- $\theta$: $xy$평면에서의 방위각
- $\phi$: 양의 $z$축에서 측정한 각

---

### 구면좌표 변환

$$x=\rho\sin\phi\cos\theta$$

$$y=\rho\sin\phi\sin\theta$$

$$z=\rho\cos\phi$$

또한

$$\rho^2=x^2+y^2+z^2$$

이고

$$r=\rho\sin\phi$$

이다.

---

### 구면좌표의 기본범위

전체 공간을 한 번 나타내는 대표범위는

$$0\le\rho<\infty$$

$$0\le\theta\le2\pi$$

$$0\le\phi\le\pi$$

이다.

---

### 구면좌표의 부피요소

구면좌표에서

$$dV=\rho^2\sin\phi\,d\rho\,d\phi\,d\theta$$

이다.

적분순서는 바뀔 수 있지만 야코비안 인자

$$\rho^2\sin\phi$$

는 반드시 포함해야 한다.

---

### 구의 방정식

중심이 원점이고 반지름이 $a$인 구는

$$\rho=a$$

이다.

구 내부는

$$0\le\rho\le a$$

이다.

---

### 원뿔의 방정식

꼭짓점이 원점이고 $z$축을 중심으로 하는 원뿔은

$$\phi=\phi_0$$

형태로 표현된다.

---

### 구면좌표가 유리한 경우

다음과 같은 영역에서 유용하다.

- 구
- 구껍질
- 구면대칭 영역
- 원점을 꼭짓점으로 하는 원뿔
- $x^2+y^2+z^2$가 나타나는 식

---

### 적용 조건과 주의사항

- 원기둥좌표의 야코비안은 $r$이다.
- 구면좌표의 야코비안은 $\rho^2\sin\phi$이다.
- $\theta$와 $\phi$의 의미를 혼동하지 않아야 한다.
- 교재에 따라 $\theta,\phi$ 표기 순서가 다를 수 있다.
- 전체 구를 적분할 때 $\phi$의 범위는 보통 $0$부터 $\pi$다.
- 영역을 중복해서 덮지 않도록 각도범위를 확인해야 한다.

---

## 5.6 Calculating Centers of Mass and Moments of Inertia
## 질량중심과 관성모멘트

### 얇은 판의 질량

영역 $D$에 밀도함수

$$\rho(x,y)$$

가 주어지면 질량은

$$m=\iint_D\rho(x,y)\,dA$$

이다.

---

### 얇은 판의 모멘트

$x$축에 대한 모멘트는

$$M_x=\iint_D y\rho(x,y)\,dA$$

이다.

$y$축에 대한 모멘트는

$$M_y=\iint_D x\rho(x,y)\,dA$$

이다.

---

### 얇은 판의 질량중심

질량중심은

$$\bar{x}=\frac{M_y}{m}$$

$$\bar{y}=\frac{M_x}{m}$$

이다.

즉,

$$\bar{x}=\frac{1}{m}\iint_D x\rho(x,y)\,dA$$

$$\bar{y}=\frac{1}{m}\iint_D y\rho(x,y)\,dA$$

이다.

---

### 균일밀도

밀도가 상수 $\rho_0$이면 질량중심은 영역의 도심과 일치한다.

$$\bar{x}=\frac{1}{A}\iint_D x\,dA$$

$$\bar{y}=\frac{1}{A}\iint_D y\,dA$$

---

### 얇은 판의 관성모멘트

$x$축에 대한 관성모멘트는

$$I_x=\iint_D y^2\rho(x,y)\,dA$$

이다.

$y$축에 대한 관성모멘트는

$$I_y=\iint_D x^2\rho(x,y)\,dA$$

이다.

원점에 대한 극관성모멘트는

$$I_0=\iint_D (x^2+y^2)\rho(x,y)\,dA$$

이다.

따라서

$$I_0=I_x+I_y$$

이다.

---

### 공간물체의 질량

공간영역 $E$에 밀도함수

$$\rho(x,y,z)$$

가 주어지면 질량은

$$m=\iiint_E\rho(x,y,z)\,dV$$

이다.

---

### 공간물체의 질량중심

$$\bar{x}=\frac{1}{m}\iiint_E x\rho\,dV$$

$$\bar{y}=\frac{1}{m}\iiint_E y\rho\,dV$$

$$\bar{z}=\frac{1}{m}\iiint_E z\rho\,dV$$

이다.

---

### 공간물체의 관성모멘트

$x$축에 대한 관성모멘트는

$$I_x=\iiint_E (y^2+z^2)\rho\,dV$$

이다.

$y$축에 대한 관성모멘트는

$$I_y=\iiint_E (x^2+z^2)\rho\,dV$$

이다.

$z$축에 대한 관성모멘트는

$$I_z=\iiint_E (x^2+y^2)\rho\,dV$$

이다.

---

### 대칭성

영역과 밀도가 대칭이면 질량중심의 일부 좌표를 적분 없이 결정할 수 있다.

예를 들어 $y$축 대칭이면

$$\bar{x}=0$$

이다.

---

### 적용 조건과 주의사항

- 질량은 밀도를 적분하여 구한다.
- $M_x$에는 $y$, $M_y$에는 $x$가 들어간다.
- 관성모멘트는 회전축까지 거리의 제곱을 사용한다.
- 밀도가 상수가 아니면 단순한 기하학적 중심과 질량중심이 다를 수 있다.
- 대칭성을 활용하면 계산을 크게 줄일 수 있다.
- 밀도는 일반적으로 음수가 아니어야 한다.

---

## 5.7 Change of Variables in Multiple Integrals
## 다중적분의 변수변환

### 변수변환

새로운 변수 $u,v$를 사용하여

$$x=x(u,v),\qquad y=y(u,v)$$

로 좌표를 바꾸는 것을 변수변환이라고 한다.

---

### 야코비안

변환

$$T(u,v)=(x(u,v),y(u,v))$$

의 야코비안은

$$\frac{\partial(x,y)}{\partial(u,v)}=\begin{vmatrix}\frac{\partial x}{\partial u}&\frac{\partial x}{\partial v}\\\frac{\partial y}{\partial u}&\frac{\partial y}{\partial v}\end{vmatrix}$$

이다.

전개하면

$$\frac{\partial(x,y)}{\partial(u,v)}=\frac{\partial x}{\partial u}\frac{\partial y}{\partial v}-\frac{\partial x}{\partial v}\frac{\partial y}{\partial u}$$

이다.

---

### 면적요소의 변환

변수변환 후 면적요소는

$$dA=\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\,du\,dv$$

이다.

따라서

$$\iint_D f(x,y)\,dA=\iint_S f(x(u,v),y(u,v))\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\,du\,dv$$

이다.

---

### 역야코비안

역변환이 존재하면

$$\frac{\partial(x,y)}{\partial(u,v)}=\frac{1}{\frac{\partial(u,v)}{\partial(x,y)}}$$

이다.

단, 분모가 $0$이 아니어야 한다.

---

### 선형변환

$$x=au+bv$$

$$y=cu+dv$$

이면 야코비안은

$$\frac{\partial(x,y)}{\partial(u,v)}=ad-bc$$

이다.

---

### 극좌표의 야코비안

$$x=r\cos\theta,\qquad y=r\sin\theta$$

이면

$$\left|\frac{\partial(x,y)}{\partial(r,\theta)}\right|=r$$

이다.

따라서

$$dA=r\,dr\,d\theta$$

이다.

---

### 3차원 변수변환

$$x=x(u,v,w),\qquad y=y(u,v,w),\qquad z=z(u,v,w)$$

이면

$$dV=\left|\frac{\partial(x,y,z)}{\partial(u,v,w)}\right|\,du\,dv\,dw$$

이다.

---

### 3차원 야코비안

$$\frac{\partial(x,y,z)}{\partial(u,v,w)}=\begin{vmatrix}x_u&x_v&x_w\\y_u&y_v&y_w\\z_u&z_v&z_w\end{vmatrix}$$

이다.

---

### 변수변환의 목적

변수변환은 다음 상황에서 사용한다.

- 복잡한 영역을 직사각형 영역으로 바꾸기
- 적분함수를 단순화하기
- 경계곡선을 좌표선으로 바꾸기
- 대칭성을 활용하기
- 원, 타원, 회전대칭 영역을 단순화하기

---

### 적용 조건과 주의사항

- 야코비안의 절댓값을 사용해야 한다.
- 변환이 일대일인지 확인해야 한다.
- 야코비안이 $0$인 점에서는 국소적인 역변환이 성립하지 않을 수 있다.
- 적분함수와 영역을 모두 새로운 변수로 바꿔야 한다.
- 원래 영역이 새 변수평면에서 어떤 영역으로 변하는지 정확히 구해야 한다.
- 3차원에서는 $3\times3$ 야코비안을 사용한다.

---

## Chapter 5 핵심 공식 요약

### 직사각형 영역의 이중적분

$$\iint_R f\,dA=\int_a^b\int_c^d f(x,y)\,dy\,dx$$

### 일반 영역의 이중적분

$$\iint_D f\,dA=\int_a^b\int_{g_1(x)}^{g_2(x)}f(x,y)\,dy\,dx$$

### 극좌표 이중적분

$$\iint_D f\,dA=\int_\alpha^\beta\int_{g_1(\theta)}^{g_2(\theta)}f(r\cos\theta,r\sin\theta)\,r\,dr\,d\theta$$

### 삼중적분

$$\iiint_E f(x,y,z)\,dV$$

### 원기둥좌표 부피요소

$$dV=r\,dr\,d\theta\,dz$$

### 구면좌표 부피요소

$$dV=\rho^2\sin\phi\,d\rho\,d\phi\,d\theta$$

### 질량

$$m=\iint_D\rho\,dA$$

$$m=\iiint_E\rho\,dV$$

### 질량중심

$$\bar{x}=\frac{1}{m}\iint_D x\rho\,dA$$

$$\bar{y}=\frac{1}{m}\iint_D y\rho\,dA$$

### 극관성모멘트

$$I_0=\iint_D(x^2+y^2)\rho\,dA$$

### 변수변환

$$\iint_D f(x,y)\,dA=\iint_S f(x(u,v),y(u,v))\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\,du\,dv$$

---

## 자주 혼동하는 사항

- 반복적분에서는 안쪽 변수부터 적분한다.
- 적분순서를 바꾸면 적분한계도 다시 설정해야 한다.
- 극좌표 이중적분에는 반드시 $r$을 곱한다.
- 구면좌표 삼중적분에는 반드시 $\rho^2\sin\phi$를 곱한다.
- $M_x$에는 $y$, $M_y$에는 $x$가 들어간다.
- 관성모멘트는 회전축까지 거리의 제곱을 사용한다.
- 변수변환에서는 야코비안의 절댓값을 사용한다.
- 적분함수와 영역을 모두 새 변수로 변환해야 한다.
