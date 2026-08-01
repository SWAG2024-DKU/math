# Calculus Volume 2 — Chapter 6
# Power Series / 멱급수

> 정리 범위: 정의 · 핵심 개념 · 주요 공식 · 적용 조건 · 주의사항  
> 수식 표기: KaTeX 문법  
> 기준 교재: OpenStax *Calculus Volume 2*, Chapter 6

---

## 6.1 Power Series and Functions
## 멱급수와 함수

### 멱급수의 정의

점 $x=a$를 중심으로 하는 멱급수는 다음과 같다.

$$\sum_{n=0}^{\infty} c_n(x-a)^n$$

전개하면

$$c_0+c_1(x-a)+c_2(x-a)^2+\cdots$$

이다.

- $a$: 멱급수의 중심
- $c_n$: 계수
- $x$: 변수

중심이 $a=0$이면

$$\sum_{n=0}^{\infty} c_nx^n$$

형태가 된다.

---

### 수렴반지름

멱급수는 중심 $x=a$에서는 항상 수렴한다.

멱급수의 수렴 형태는 다음 세 가지 중 하나이다.

1. $x=a$에서만 수렴
2. 모든 실수 $x$에서 수렴
3. 어떤 $R>0$에 대해 $|x-a|<R$에서 수렴하고 $|x-a|>R$에서 발산

이때 $R$을 **수렴반지름(radius of convergence)**이라고 한다.

특수한 경우는 다음과 같다.

$$R=0$$

이면 중심에서만 수렴하고,

$$R=\infty$$

이면 모든 실수에서 수렴한다.

---

### 수렴구간

수렴반지름이 $R$이면 기본 수렴구간 후보는

$$a-R<x<a+R$$

이다.

끝점

$$x=a-R,\qquad x=a+R$$

의 수렴 여부는 각각 따로 검사해야 한다.

가능한 수렴구간은 다음과 같다.

$$(a-R,a+R)$$

$$[a-R,a+R)$$

$$(a-R,a+R]$$

$$[a-R,a+R]$$

---

### 비율판정법

멱급수

$$\sum_{n=0}^{\infty} c_n(x-a)^n$$

에 대해 비율판정법을 적용하면

$$L= \lim_{n\to\infty} \left| \frac{c_{n+1}(x-a)^{n+1}} {c_n(x-a)^n} \right|$$

이다.

정리하면

$$L= |x-a| \lim_{n\to\infty} \left| \frac{c_{n+1}}{c_n} \right|$$

이다.

수렴 조건은

$$L<1$$

이다.

만약

$$\lim_{n\to\infty} \left| \frac{c_{n+1}}{c_n} \right| =\ell$$

이면

$$R=\frac{1}{\ell}$$

이다.

단, $\ell=0$이면 $R=\infty$이고, 극한이 무한대이면 $R=0$이다.

---

### 근판정법

근판정법을 적용하면

$$L= \lim_{n\to\infty} \sqrt[n]{|c_n(x-a)^n|}$$

이고,

$$L= |x-a| \lim_{n\to\infty} \sqrt[n]{|c_n|}$$

이다.

수렴 조건은

$$L<1$$

이다.

일반적으로 수렴반지름은

$$R= \frac{1} {\limsup_{n\to\infty}\sqrt[n]{|c_n|}}$$

로 표현할 수 있다.

---

### 기하급수와 멱급수

기하급수 공식은

$$\sum_{n=0}^{\infty} r^n = \frac{1}{1-r}$$

이며 수렴 조건은

$$|r|<1$$

이다.

$r=x$로 두면

$$\frac{1}{1-x} = \sum_{n=0}^{\infty}x^n$$

이고 수렴구간은

$$-1<x<1$$

이다.

이 식은 여러 함수의 멱급수를 만드는 기본식으로 사용된다.

---

### 멱급수로 정의된 함수

수렴구간 안에서 멱급수는 하나의 함수를 정의한다.

$$f(x)=\sum_{n=0}^{\infty}c_n(x-a)^n$$

부분합은

$$S_N(x)=\sum_{n=0}^{N}c_n(x-a)^n$$

이다.

$N$이 증가할수록 부분합은 수렴구간 안에서 함수 $f(x)$에 가까워진다.

---

### 적용 조건과 주의사항

- 비율판정법이나 근판정법은 보통 열린구간만 결정한다.
- 끝점에서는 판정값이 $1$이 되는 경우가 많으므로 반드시 별도 검사해야 한다.
- 수렴반지름과 수렴구간은 서로 다른 개념이다.
- 중심에서는 항상 수렴한다.
- 한쪽 끝점만 포함될 수 있다.
- 끝점의 수렴 여부는 원래 급수에 직접 대입하여 판단해야 한다.

---

## 6.2 Properties of Power Series
## 멱급수의 성질

### 합과 차

두 멱급수

$$\sum_{n=0}^{\infty}a_nx^n$$

과

$$\sum_{n=0}^{\infty}b_nx^n$$

이 공통 수렴구간에서 수렴하면

$$\sum_{n=0}^{\infty}a_nx^n + \sum_{n=0}^{\infty}b_nx^n = \sum_{n=0}^{\infty}(a_n+b_n)x^n$$

이다.

차도 같은 방식으로 계산한다.

$$\sum_{n=0}^{\infty}(a_n-b_n)x^n$$

---

### 상수배

상수 $c$에 대해

$$c\sum_{n=0}^{\infty}a_nx^n = \sum_{n=0}^{\infty}ca_nx^n$$

이다.

---

### 멱급수의 곱

두 멱급수의 곱은 Cauchy 곱으로 계산한다.

$$\left( \sum_{n=0}^{\infty}a_nx^n \right) \left( \sum_{n=0}^{\infty}b_nx^n \right) = \sum_{n=0}^{\infty} \left( \sum_{k=0}^{n}a_kb_{n-k} \right)x^n$$

$x^n$의 계수는

$$\sum_{k=0}^{n}a_kb_{n-k}$$

이다.

---

### 항별 미분

멱급수

$$f(x)=\sum_{n=0}^{\infty}c_n(x-a)^n$$

의 수렴반지름이 $R$이면 $|x-a|<R$에서 항별 미분이 가능하다.

$$f'(x) = \sum_{n=1}^{\infty} nc_n(x-a)^{n-1}$$

미분한 급수의 수렴반지름도 $R$이다.

---

### 항별 적분

같은 조건에서 항별 적분도 가능하다.

$$\int f(x)\,dx = C+ \sum_{n=0}^{\infty} \frac{c_n}{n+1}(x-a)^{n+1}$$

정적분 형태로는

$$\int_a^x f(t)\,dt = \sum_{n=0}^{\infty} \frac{c_n}{n+1}(x-a)^{n+1}$$

이다.

적분한 급수의 수렴반지름도 원래 급수와 같다.

---

### 기하급수의 미분

기본식

$$\frac{1}{1-x} = \sum_{n=0}^{\infty}x^n$$

을 미분하면

$$\frac{1}{(1-x)^2} = \sum_{n=1}^{\infty}nx^{n-1}$$

이다.

인덱스를 바꾸면

$$\frac{1}{(1-x)^2} = \sum_{n=0}^{\infty}(n+1)x^n$$

이다.

수렴구간은 여전히

$$|x|<1$$

이다.

---

### 기하급수의 적분

기본식

$$\frac{1}{1-x} = \sum_{n=0}^{\infty}x^n$$

을 적분하면

$$-\ln(1-x) = \sum_{n=1}^{\infty}\frac{x^n}{n}$$

이다.

따라서 $x$를 $-x$로 바꾸면

$$\ln(1+x) = \sum_{n=1}^{\infty} (-1)^{n+1}\frac{x^n}{n}$$

이다.

---

### 변수 치환

기본 멱급수에서 $x$ 대신 $g(x)$를 대입할 수 있다.

$$\frac{1}{1-g(x)} = \sum_{n=0}^{\infty}[g(x)]^n$$

적용 조건은

$$|g(x)|<1$$

이다.

---

### 계수의 유일성

두 멱급수가 어떤 열린구간에서 같은 함수라면 같은 차수의 계수는 서로 같다.

$$\sum_{n=0}^{\infty}a_n(x-a)^n = \sum_{n=0}^{\infty}b_n(x-a)^n$$

이면

$$a_n=b_n$$

이다.

---

### 적용 조건과 주의사항

- 항별 미분과 적분은 수렴반지름 내부에서 적용한다.
- 미분·적분 후 수렴반지름은 같지만 끝점의 수렴 여부는 달라질 수 있다.
- 변수 치환 후에는 새로운 수렴조건을 다시 계산해야 한다.
- 급수의 곱에서는 같은 차수의 모든 항을 합쳐야 한다.
- 인덱스를 바꿀 때 시작값과 지수를 함께 확인해야 한다.

---

## 6.3 Taylor and Maclaurin Series
## Taylor 급수와 Maclaurin 급수

### Taylor 다항식

함수 $f$가 $x=a$에서 충분히 여러 번 미분가능할 때 $n$차 Taylor 다항식은

$$P_n(x) = \sum_{k=0}^{n} \frac{f^{(k)}(a)}{k!}(x-a)^k$$

이다.

전개하면

$$P_n(x) = f(a) + f'(a)(x-a) + \frac{f''(a)}{2!}(x-a)^2 +\cdots+ \frac{f^{(n)}(a)}{n!}(x-a)^n$$

이다.

---

### Taylor 급수

Taylor 다항식을 무한히 확장하면

$$\sum_{n=0}^{\infty} \frac{f^{(n)}(a)}{n!}(x-a)^n$$

을 얻는다.

이 급수가 실제로 함수 $f(x)$에 수렴하면

$$f(x) = \sum_{n=0}^{\infty} \frac{f^{(n)}(a)}{n!}(x-a)^n$$

이라고 쓴다.

---

### Maclaurin 급수

중심이 $a=0$인 Taylor 급수를 Maclaurin 급수라고 한다.

$$f(x) = \sum_{n=0}^{\infty} \frac{f^{(n)}(0)}{n!}x^n$$

---

### Taylor 계수

멱급수

$$f(x)=\sum_{n=0}^{\infty}c_n(x-a)^n$$

가 함수 $f$의 Taylor 급수라면

$$c_n=\frac{f^{(n)}(a)}{n!}$$

이다.

---

### 자연지수함수

$$e^x = \sum_{n=0}^{\infty} \frac{x^n}{n!}$$

즉,

$$e^x = 1+x+\frac{x^2}{2!} +\frac{x^3}{3!} +\cdots$$

이다.

수렴구간은

$$(-\infty,\infty)$$

이다.

---

### 사인함수

$$\sin x = \sum_{n=0}^{\infty} (-1)^n \frac{x^{2n+1}}{(2n+1)!}$$

즉,

$$\sin x = x-\frac{x^3}{3!} +\frac{x^5}{5!} -\frac{x^7}{7!} +\cdots$$

이다.

수렴구간은 모든 실수이다.

---

### 코사인함수

$$\cos x = \sum_{n=0}^{\infty} (-1)^n \frac{x^{2n}}{(2n)!}$$

즉,

$$\cos x = 1-\frac{x^2}{2!} +\frac{x^4}{4!} -\frac{x^6}{6!} +\cdots$$

이다.

수렴구간은 모든 실수이다.

---

### 로그함수

$$\ln(1+x) = \sum_{n=1}^{\infty} (-1)^{n+1}\frac{x^n}{n}$$

즉,

$$\ln(1+x) = x-\frac{x^2}{2} +\frac{x^3}{3} -\frac{x^4}{4} +\cdots$$

이다.

수렴구간은

$$(-1,1]$$

이다.

---

### 역탄젠트함수

$$\arctan x = \sum_{n=0}^{\infty} (-1)^n \frac{x^{2n+1}}{2n+1}$$

즉,

$$\arctan x = x-\frac{x^3}{3} +\frac{x^5}{5} -\frac{x^7}{7} +\cdots$$

이다.

수렴구간은

$$[-1,1]$$

이다.

---

### 함수와 Taylor 급수의 일치

함수가 무한번 미분가능하더라도 Taylor 급수의 합이 반드시 원래 함수와 같지는 않다.

함수와 Taylor 다항식 사이의 나머지를

$$R_n(x)=f(x)-P_n(x)$$

라고 할 때,

$$\lim_{n\to\infty}R_n(x)=0$$

이면 Taylor 급수는 함수 $f(x)$에 수렴한다.

---

### 적용 조건과 주의사항

- Taylor 다항식은 유한합이고 Taylor 급수는 무한합이다.
- Maclaurin 급수는 중심이 $0$인 Taylor 급수다.
- 모든 차수의 도함수가 존재해도 급수가 원래 함수와 일치하지 않을 수 있다.
- 계수의 분모에 $n!$이 들어간다.
- 짝함수는 일반적으로 짝수차 항만, 홀함수는 홀수차 항만 나타난다.
- 급수식과 함께 수렴구간을 확인해야 한다.

---

## 6.4 Working with Taylor Series
## Taylor 급수의 활용

### Taylor 정리

함수 $f$와 $n$차 Taylor 다항식 $P_n$ 사이에는

$$f(x)=P_n(x)+R_n(x)$$

관계가 있다.

Lagrange 형태의 나머지항은

$$R_n(x) = \frac{f^{(n+1)}(c)} {(n+1)!}(x-a)^{n+1}$$

이다.

여기서 $c$는 $a$와 $x$ 사이의 어떤 값이다.

---

### Taylor 부등식

구간에서

$$|f^{(n+1)}(z)|\le M$$

이면

$$|R_n(x)| \le \frac{M}{(n+1)!}|x-a|^{n+1}$$

이다.

이 식은 다음에 사용한다.

- Taylor 다항식의 최대오차 추정
- 필요한 차수 결정
- Taylor 급수가 실제 함수에 수렴함을 확인

---

### 알려진 급수의 변형

이미 알려진 멱급수에 다음 연산을 적용하여 새로운 급수를 만들 수 있다.

- 변수 치환
- 상수배
- 급수의 합과 차
- 급수의 곱
- 항별 미분
- 항별 적분

예를 들어

$$e^x = \sum_{n=0}^{\infty}\frac{x^n}{n!}$$

에서 $x$ 대신 $-x^2$를 대입하면

$$e^{-x^2} = \sum_{n=0}^{\infty} (-1)^n\frac{x^{2n}}{n!}$$

이다.

---

### 멱급수를 이용한 적분

초등함수로 원시함수를 표현하기 어려운 함수도 멱급수를 항별 적분하여 나타낼 수 있다.

예를 들어

$$e^{-x^2} = \sum_{n=0}^{\infty} (-1)^n\frac{x^{2n}}{n!}$$

이므로

$$\int e^{-x^2}\,dx = C+ \sum_{n=0}^{\infty} (-1)^n \frac{x^{2n+1}}{(2n+1)n!}$$

이다.

---

### 멱급수를 이용한 극한

함수의 Taylor 급수에서 가장 낮은 차수의 비영항을 이용하면 극한의 주된 거동을 확인할 수 있다.

예를 들어

$$e^x = 1+x+\frac{x^2}{2} +\frac{x^3}{6} +\cdots$$

이므로 $x\to0$에서

$$e^x-1-x$$

의 주된 항은

$$\frac{x^2}{2}$$

이다.

---

### 이항급수

실수 $r$에 대해 일반화된 이항계수는

$$\binom{r}{n} = \frac{ r(r-1)(r-2)\cdots(r-n+1) }{n!}$$

이다.

또한

$$\binom{r}{0}=1$$

이다.

이항급수는

$$(1+x)^r = \sum_{n=0}^{\infty} \binom{r}{n}x^n$$

이다.

전개하면

$$(1+x)^r = 1 +rx +\frac{r(r-1)}{2!}x^2 +\frac{r(r-1)(r-2)}{3!}x^3 +\cdots$$

이다.

일반적인 수렴조건은

$$|x|<1$$

이다.

끝점의 수렴 여부는 $r$의 값에 따라 따로 판단해야 한다.

---

## 대표 Maclaurin 급수

### 기하급수

$$\frac{1}{1-x}=\sum_{n=0}^{\infty}x^n,\qquad |x|<1$$

### 자연지수함수

$$e^x=\sum_{n=0}^{\infty}\frac{x^n}{n!},\qquad -\infty<x<\infty$$

### 사인함수

$$\sin x=\sum_{n=0}^{\infty}(-1)^n\frac{x^{2n+1}}{(2n+1)!},\qquad -\infty<x<\infty$$

### 코사인함수

$$\cos x=\sum_{n=0}^{\infty}(-1)^n\frac{x^{2n}}{(2n)!},\qquad -\infty<x<\infty$$

### 로그함수

$$\ln(1+x)=\sum_{n=1}^{\infty}(-1)^{n+1}\frac{x^n}{n},\qquad -1<x\le 1$$

### 역탄젠트함수

$$\arctan x=\sum_{n=0}^{\infty}(-1)^n\frac{x^{2n+1}}{2n+1},\qquad -1\le x\le 1$$

---

## Chapter 6 핵심 공식 요약

### 멱급수

$$\sum_{n=0}^{\infty}c_n(x-a)^n$$

### 수렴반지름

$$|x-a|<R$$

### 항별 미분

$$\frac{d}{dx} \left[ \sum_{n=0}^{\infty}c_n(x-a)^n \right] = \sum_{n=1}^{\infty} nc_n(x-a)^{n-1}$$

### 항별 적분

$$\int \sum_{n=0}^{\infty}c_n(x-a)^n\,dx = C+ \sum_{n=0}^{\infty} \frac{c_n}{n+1}(x-a)^{n+1}$$

### Taylor 급수

$$f(x) = \sum_{n=0}^{\infty} \frac{f^{(n)}(a)}{n!}(x-a)^n$$

### Maclaurin 급수

$$f(x) = \sum_{n=0}^{\infty} \frac{f^{(n)}(0)}{n!}x^n$$

### Taylor 나머지항

$$R_n(x) = \frac{f^{(n+1)}(c)} {(n+1)!}(x-a)^{n+1}$$

### Taylor 오차한계

$$|R_n(x)| \le \frac{M}{(n+1)!}|x-a|^{n+1}$$

### 이항급수

$$(1+x)^r = \sum_{n=0}^{\infty} \binom{r}{n}x^n$$

---

## 자주 혼동하는 사항

- 수렴반지름과 수렴구간은 같은 개념이 아니다.
- 끝점 수렴 여부는 자동으로 결정되지 않는다.
- 미분·적분 후 수렴반지름은 유지되지만 끝점은 달라질 수 있다.
- Taylor 다항식은 유한합이고 Taylor 급수는 무한합이다.
- 함수가 무한번 미분가능해도 Taylor 급수와 반드시 일치하지는 않는다.
- 변수 치환을 하면 수렴조건도 함께 바뀐다.
- $\ln(1+x)$와 $-\ln(1-x)$의 부호를 혼동하지 않아야 한다.
- Taylor 오차에는 $(n+1)$차 도함수가 사용된다.

---

## Source

OpenStax, *Calculus Volume 2*, Chapter 6: Power Series.
