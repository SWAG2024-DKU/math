# 확률과 통계 — 확률부등식과 극한이론

> **개정판 v9 (2026-07-29)**: 전수 검토에서 확인된 수학적 조건, 정의 범위, 경계값, 정확·점근·근사 구분과 Markdown·LaTeX 표기를 반영하였다.

> **v9 추가 반영**: 핵심 공식의 미완성 항목, 효과지표의 정의 조건, 상관계수의 척도변환, 측정오차 해석과 회귀·ANOVA 진단 공식을 보완하였다.

> 각 정리의 정의, 적용 조건, 함의 관계, 반례 가능성을 구분하여 정리한다.


> **표기 원칙**  
> - `[정의]`: 개념을 규정하는 식  
> - `[정확]`: 명시된 조건 아래 유한표본에서 정확한 식  
> - `[점근]`: 표본크기가 증가할 때 성립하는 극한 결과  
> - `[근사]`: 정확한 분포를 다른 분포로 근사한 식  
> - `[상계·하계]`: 확률 또는 오차의 경계  
> - `[경험적 기준]`: 정리가 아닌 실무적 판단 기준  
> `[정의]`, `[정확]`, `[점근]`, `[근사]` 등의 태그는 구분이 특히 필요한 공식에 표시한다. 태그가 없는 공식도 적용 조건, 지지집합, 모수 범위와 해석상 주의점을 함께 확인한다.

## 10.1 Markov 부등식

비음수 확률변수 $X$와 $a>0$에 대해
$$
P(X\ge a)\le\frac{E[X]}{a}
$$
이다. $X\ge0$이고 $E[X]<\infty$가 필요하다.

## 10.2 Chebyshev 부등식

$E[X]=\mu$, $\operatorname{Var}(X)=\sigma^2<\infty$이면 모든 $\varepsilon>0$에 대해
$$
P(|X-\mu|\ge\varepsilon)\le\frac{\sigma^2}{\varepsilon^2}
$$
이다. 특히 $\sigma>0$이고 $k>0$일 때
$$
P(|X-\mu|\ge k\sigma)\le\frac1{k^2}
$$
이다. $\sigma=0$이면 $X=\mu$가 거의 확실하게 성립하므로 $k\sigma=0$을 대입한 위 형태를 사용하지 않고 퇴화분포로 별도 해석한다.

## 10.3 Jensen 부등식과 Chernoff 상계

확률변수 $X$가 적분 가능하고, $\phi$가 $X$의 값이 속하는 볼록집합에서 볼록하며 양변이 정의되면
$$
\phi(E[X])\le E[\phi(X)]
$$
이다.

해당 $t>0$에서 $M_X(t)<\infty$이면
$$
P(X\ge a)\le e^{-ta}M_X(t)
$$
이므로
$$
P(X\ge a)\le\inf_{\substack{t>0\\M_X(t)<\infty}}e^{-ta}M_X(t)
$$
이다.

## 10.4 확률변수열의 수렴

### 거의 확실 수렴
$$
X_n\xrightarrow{a.s.}X
\iff
P\left(\lim_{n\to\infty}X_n=X\right)=1
$$
### 확률수렴
$$
X_n\xrightarrow{P}X
\iff
P(|X_n-X|>\varepsilon)\to0
$$
모든 $\varepsilon>0$에 대해 성립해야 한다.

### $L^1$ 수렴
$$
X_n\xrightarrow{L^1}X
\iff
E|X_n-X|\to0
$$
### $L^2$ 수렴
$$
X_n\xrightarrow{L^2}X
\iff
E[(X_n-X)^2]\to0
$$
### 분포수렴
$$
X_n\xrightarrow{d}X
\iff
F_{X_n}(x)\to F_X(x)
$$
단, $F_X$의 모든 연속점 $x$에서 성립한다.

### 함의 관계
$$
X_n\xrightarrow{L^2}X
\Longrightarrow X_n\xrightarrow{L^1}X
\Longrightarrow X_n\xrightarrow{P}X
\Longrightarrow X_n\xrightarrow{d}X
$$
$$
X_n\xrightarrow{a.s.}X
\Longrightarrow X_n\xrightarrow{P}X
$$
거의 확실 수렴과 $L^2$ 수렴 사이에는 일반적으로 직접적인 함의 관계가 없다.

## 10.5 연속사상정리와 Slutsky 정리

$X_n\xrightarrow{d}X$이고 $g$가 $X$가 취하는 값에서 거의 확실하게 연속이면
$$
g(X_n)\xrightarrow{d}g(X)
$$
이다.

또한
$$
X_n\xrightarrow{d}X,\qquad Y_n\xrightarrow{P}c
$$
이면
$$
X_n+Y_n\xrightarrow{d}X+c,
\qquad
X_nY_n\xrightarrow{d}cX
$$
또한 $c\ne0$이면

$$
\frac{X_n}{Y_n}\xrightarrow{d}\frac{X}{c}
$$
이다.

## 10.6 대수의 법칙

$i.i.d.$ 확률변수 $X_1,X_2,\ldots$가 $E|X_1|<\infty$이고 $E[X_1]=\mu$이면 대표적인 약한 및 강한 대수의 법칙에 의해
$$
\bar X_n\xrightarrow{P}\mu
$$
및
$$
\bar X_n\xrightarrow{a.s.}\mu
$$
가 성립한다. Chebyshev 부등식을 이용한 초급 증명에서는 흔히 $\operatorname{Var}(X_1)<\infty$를 가정한다.

## 10.7 중심극한정리

$X_1,X_2,\ldots$가 $i.i.d.$이고
$$
E[X_i]=\mu,\qquad 0<\operatorname{Var}(X_i)=\sigma^2<\infty
$$
이면
$$
\frac{\sum_{i=1}^{n}X_i-n\mu}{\sigma\sqrt n}
\xrightarrow{d}N(0,1)
$$
이다. 동치인 표본평균 형태는
$$
\frac{\bar X_n-\mu}{\sigma/\sqrt n}
\xrightarrow{d}N(0,1)
$$
이다. 따라서 큰 표본에서
$$
\bar X_n\approx N\left(\mu,\frac{\sigma^2}{n}\right)
$$
으로 근사한다. 필요한 표본크기는 원분포의 왜도, 꼬리, 이상치에 따라 달라지므로 $n\ge30$을 절대 규칙으로 사용하지 않는다.

동일분포가 아닌 독립 확률변수에는 Lindeberg 또는 Lyapunov 조건 등이 필요하다.

## 10.8 Borel--Cantelli 보조정리

사건열 $A_n$에 대해
$$
\sum_{n=1}^{\infty}P(A_n)<\infty
$$
이면
$$
P(A_n\ \text{i.o.})=0
$$
이다. 반대로 사건들이 독립이고
$$
\sum_{n=1}^{\infty}P(A_n)=\infty
$$
이면
$$
P(A_n\ \text{i.o.})=1
$$
이다.


## 10.9 Fatou 보조정리와 지배수렴정리

비음수 확률변수열 $X_n$에 대해 Fatou 보조정리는
$$
E[\liminf_{n\to\infty}X_n]
\le
\liminf_{n\to\infty}E[X_n]
$$
를 준다.

$X_n\to X$가 거의 확실하게 성립하고 적분 가능한 확률변수 $Y$가 존재하여 모든 $n$에 대해 $|X_n|\le Y$이면 지배수렴정리에 의해
$$
E[X_n]\to E[X]
$$
이다. 확률변수의 극한과 기댓값의 순서를 교환하려면 이런 추가 조건이 필요하다.

## 10.10 Hoeffding 부등식

독립 확률변수 $X_i\in[a_i,b_i]$이고 $S_n=\sum_iX_i$이면 모든 $t>0$에 대해
$$
P(S_n-E[S_n]\ge t)
\le
\exp\left(
-\frac{2t^2}{\sum_{i=1}^{n}(b_i-a_i)^2}
\right)
$$
이다. 양쪽 꼬리에 대해서는 우변에 2를 곱한 상계를 사용할 수 있다. 이는 유한분산만 사용하는 Chebyshev 부등식보다 강하지만 독립성과 유계성이라는 더 강한 조건이 필요하다.

## 10.11 중심극한정리의 적용 한계

중심극한정리는 표준화된 합의 분포수렴을 말하며, 원자료가 정규분포가 된다는 뜻이 아니다. 또한 꼬리확률, 극단 분위수, 매우 왜도가 큰 분포에서는 중앙 부분보다 수렴이 느릴 수 있다. 평균이나 분산이 존재하지 않는 분포에는 현재 제시한 고전적 i.i.d. 중심극한정리를 적용할 수 없다.

## 10.12 Cantelli 부등식

$E[X]=\mu$, $\operatorname{Var}(X)=\sigma^2<\infty$이면 모든 $a>0$에 대해
$$
P(X-\mu\ge a)
\le
\frac{\sigma^2}{\sigma^2+a^2}
$$
이다. 이는 한쪽 꼬리만 관심 있을 때 Chebyshev 부등식보다 강한 상계를 줄 수 있다.

## 10.13 Berry--Esseen 정리

$i.i.d.$ 확률변수들이 평균 $\mu$, 분산 $0<\sigma^2<\infty$와 유한한 3차 절대중심적률
$$
\rho=E|X_1-\mu|^3<\infty
$$
를 가지면 어떤 보편상수 $C$에 대해
$$
\sup_x\left|
P\left(\frac{\sum_{i=1}^nX_i-n\mu}{\sigma\sqrt n}\le x\right)
-\Phi(x)
\right|
\le
\frac{C\rho}{\sigma^3\sqrt n}
$$
이다. 이 결과는 중심극한정리의 정규근사 오차가 분포의 3차 절대적률과 표본크기에 영향을 받음을 정량화한다.

## 10.14 수렴 개념의 역방향이 일반적으로 실패하는 이유

- 분포수렴은 확률수렴을 일반적으로 함의하지 않는다.
- 확률수렴은 거의 확실 수렴을 일반적으로 함의하지 않는다.
- 거의 확실 수렴만으로 $L^1$ 수렴이 보장되지 않는다.
- 기대값의 수렴에는 균등적분가능성 또는 지배조건 같은 추가 조건이 필요하다.
