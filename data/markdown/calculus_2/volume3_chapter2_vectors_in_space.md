# Calculus Volume 3 — Chapter 2
# Vectors in Space / 공간의 벡터

## 선수 개념

- 좌표평면
- 2차원 벡터
- 벡터의 크기
- 단위벡터
- 벡터의 덧셈과 스칼라배
- 삼각함수
- 피타고라스 정리
- 직선의 방정식
- 평면도형의 넓이
- 연립방정식
- 완전제곱
- 이차방정식

---

## 2.1 Vectors in the Plane
## 평면의 벡터

### 벡터의 정의

벡터는 크기와 방향을 함께 가지는 양이다.

평면에서 벡터는

$$\mathbf{v}=\langle v_1,v_2\rangle$$

형태로 나타낸다.

두 점

$$P(x_1,y_1),\qquad Q(x_2,y_2)$$

에 대해 $P$에서 $Q$로 향하는 벡터는

$$\overrightarrow{PQ}=\langle x_2-x_1,\ y_2-y_1\rangle$$

이다.

---

### 위치벡터

원점 $O=(0,0)$에서 점 $P=(x,y)$로 향하는 벡터는

$$\overrightarrow{OP}=\langle x,y\rangle$$

이다.

이를 점 $P$의 위치벡터라고 한다.

---

### 벡터의 크기

$$\mathbf{v}=\langle v_1,v_2\rangle$$

의 크기는

$$\|\mathbf{v}\|=\sqrt{v_1^2+v_2^2}$$

이다.

---

### 단위벡터

크기가 $1$인 벡터를 단위벡터라고 한다.

$\mathbf{v}\ne\mathbf{0}$일 때 $\mathbf{v}$와 같은 방향의 단위벡터는

$$\mathbf{u}=\frac{\mathbf{v}}{\|\mathbf{v}\|}$$

이다.

---

### 표준단위벡터

평면의 표준단위벡터는

$$\mathbf{i}=\langle1,0\rangle,\qquad \mathbf{j}=\langle0,1\rangle$$

이다.

따라서

$$\mathbf{v}=v_1\mathbf{i}+v_2\mathbf{j}$$

로 쓸 수 있다.

---

### 벡터의 덧셈과 뺄셈

$$\mathbf{u}=\langle u_1,u_2\rangle,\qquad \mathbf{v}=\langle v_1,v_2\rangle$$

이면

$$\mathbf{u}+\mathbf{v}=\langle u_1+v_1,\ u_2+v_2\rangle$$

이고

$$\mathbf{u}-\mathbf{v}=\langle u_1-v_1,\ u_2-v_2\rangle$$

이다.

---

### 스칼라배

스칼라 $c$에 대해

$$c\mathbf{v}=\langle cv_1,cv_2\rangle$$

이다.

$c>0$이면 방향이 유지되고, $c<0$이면 방향이 반대가 된다.

크기는

$$\|c\mathbf{v}\|=|c|\|\mathbf{v}\|$$

이다.

---

### 벡터의 기본 성질

$$\mathbf{u}+\mathbf{v}=\mathbf{v}+\mathbf{u}$$

$$(\mathbf{u}+\mathbf{v})+\mathbf{w}=\mathbf{u}+(\mathbf{v}+\mathbf{w})$$

$$c(\mathbf{u}+\mathbf{v})=c\mathbf{u}+c\mathbf{v}$$

$$(c+d)\mathbf{v}=c\mathbf{v}+d\mathbf{v}$$

$$c(d\mathbf{v})=(cd)\mathbf{v}$$

이다.

---

### 방향각

벡터

$$\mathbf{v}=\langle a,b\rangle$$

가 양의 $x$축과 이루는 각을 $\theta$라고 하면

$$a=\|\mathbf{v}\|\cos\theta,\qquad b=\|\mathbf{v}\|\sin\theta$$

이다.

따라서

$$\mathbf{v}=\|\mathbf{v}\|\langle\cos\theta,\sin\theta\rangle$$

로 나타낼 수 있다.

---

### 적용 조건과 주의사항

- $\overrightarrow{PQ}$는 끝점 좌표에서 시작점 좌표를 빼서 구한다.
- 영벡터는 방향이 정해지지 않으므로 단위벡터로 만들 수 없다.
- 벡터의 크기는 성분의 합이 아니라 제곱합의 제곱근이다.
- 방향각을 구할 때는 사분면을 확인해야 한다.
- 점과 벡터는 표기가 비슷하지만 서로 다른 개념이다.

---

## 2.2 Vectors in Three Dimensions
## 3차원 공간의 벡터

### 3차원 좌표계

3차원 공간의 점은

$$P(x,y,z)$$

로 나타낸다.

세 좌표축은 서로 수직이다.

좌표평면은 다음과 같다.

$$xy\text{-평면}: z=0$$

$$xz\text{-평면}: y=0$$

$$yz\text{-평면}: x=0$$

---

### 팔분공간

세 좌표평면은 공간을 여덟 부분으로 나눈다.

이를 팔분공간이라고 한다.

제1팔분공간에서는

$$x>0,\qquad y>0,\qquad z>0$$

이다.

---

### 두 점 사이의 거리

두 점

$$P(x_1,y_1,z_1),\qquad Q(x_2,y_2,z_2)$$

사이의 거리는

$$d(P,Q)=\sqrt{(x_2-x_1)^2+(y_2-y_1)^2+(z_2-z_1)^2}$$

이다.

---

### 중점

두 점의 중점은

$$M=\left(\frac{x_1+x_2}{2},\frac{y_1+y_2}{2},\frac{z_1+z_2}{2}\right)$$

이다.

---

### 구의 방정식

중심이

$$C(h,k,l)$$

이고 반지름이 $r$인 구는

$$(x-h)^2+(y-k)^2+(z-l)^2=r^2$$

이다.

중심이 원점이면

$$x^2+y^2+z^2=r^2$$

이다.

---

### 3차원 벡터

3차원 벡터는

$$\mathbf{v}=\langle v_1,v_2,v_3\rangle$$

로 나타낸다.

표준단위벡터는

$$\mathbf{i}=\langle1,0,0\rangle$$

$$\mathbf{j}=\langle0,1,0\rangle$$

$$\mathbf{k}=\langle0,0,1\rangle$$

이다.

따라서

$$\mathbf{v}=v_1\mathbf{i}+v_2\mathbf{j}+v_3\mathbf{k}$$

이다.

---

### 3차원 벡터의 크기

$$\|\mathbf{v}\|=\sqrt{v_1^2+v_2^2+v_3^2}$$

이다.

---

### 두 점을 잇는 벡터

$$P(x_1,y_1,z_1)$$

에서

$$Q(x_2,y_2,z_2)$$

로 향하는 벡터는

$$\overrightarrow{PQ}=\langle x_2-x_1,\ y_2-y_1,\ z_2-z_1\rangle$$

이다.

---

### 적용 조건과 주의사항

- 구의 방정식은 세 좌표방향의 거리 제곱합으로 구성된다.
- 3차원 거리공식은 2차원 거리공식에 $z$성분이 추가된 형태다.
- 좌표평면의 방정식은 해당 축의 좌표가 $0$이라는 뜻이다.
- 점의 좌표와 위치벡터의 성분은 같을 수 있지만 개념적으로 구분해야 한다.

---

## 2.3 The Dot Product
## 내적

### 내적의 정의

$$\mathbf{u}=\langle u_1,u_2,u_3\rangle$$

$$\mathbf{v}=\langle v_1,v_2,v_3\rangle$$

일 때 내적은

$$\mathbf{u}\cdot\mathbf{v}=u_1v_1+u_2v_2+u_3v_3$$

이다.

내적의 결과는 스칼라다.

---

### 내적의 기하학적 의미

두 벡터 사이의 각을 $\theta$라고 하면

$$\mathbf{u}\cdot\mathbf{v}=\|\mathbf{u}\|\|\mathbf{v}\|\cos\theta$$

이다.

따라서

$$\cos\theta=\frac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{u}\|\|\mathbf{v}\|}$$

이다.

---

### 직교 조건

두 영이 아닌 벡터에 대해

$$\mathbf{u}\cdot\mathbf{v}=0$$

이면 두 벡터는 수직이다.

---

### 내적의 성질

$$\mathbf{u}\cdot\mathbf{v}=\mathbf{v}\cdot\mathbf{u}$$

$$\mathbf{u}\cdot(\mathbf{v}+\mathbf{w})=\mathbf{u}\cdot\mathbf{v}+\mathbf{u}\cdot\mathbf{w}$$

$$(c\mathbf{u})\cdot\mathbf{v}=c(\mathbf{u}\cdot\mathbf{v})$$

$$\mathbf{u}\cdot\mathbf{u}=\|\mathbf{u}\|^2$$

이다.

---

### 벡터 정사영

$\mathbf{u}$를 $\mathbf{v}$ 방향으로 정사영한 벡터는

$$\operatorname{proj}_{\mathbf{v}}\mathbf{u}=\frac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{v}\|^2}\mathbf{v}$$

이다.

---

### 스칼라 성분

$\mathbf{u}$의 $\mathbf{v}$ 방향 스칼라 성분은

$$\operatorname{comp}_{\mathbf{v}}\mathbf{u}=\frac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{v}\|}$$

이다.

---

### 일

힘벡터 $\mathbf{F}$가 물체를 변위벡터 $\mathbf{D}$만큼 이동시킬 때 한 일은

$$W=\mathbf{F}\cdot\mathbf{D}$$

이다.

또는

$$W=\|\mathbf{F}\|\|\mathbf{D}\|\cos\theta$$

이다.

---

### 방향코사인

벡터

$$\mathbf{v}=\langle a,b,c\rangle$$

가 양의 $x,y,z$축과 이루는 각을 각각 $\alpha,\beta,\gamma$라고 하면

$$\cos\alpha=\frac{a}{\|\mathbf{v}\|}$$

$$\cos\beta=\frac{b}{\|\mathbf{v}\|}$$

$$\cos\gamma=\frac{c}{\|\mathbf{v}\|}$$

이다.

또한

$$\cos^2\alpha+\cos^2\beta+\cos^2\gamma=1$$

이다.

---

### 적용 조건과 주의사항

- 각도공식에서는 두 벡터가 모두 영벡터가 아니어야 한다.
- 내적의 결과는 벡터가 아니라 스칼라다.
- 정사영의 분모는 $\|\mathbf{v}\|^2$이다.
- 내적이 $0$이라고 해서 두 벡터가 모두 영이 아닌지 확인해야 한다.
- 일은 힘의 전체 크기가 아니라 변위 방향 성분에 의해 결정된다.

---

## 2.4 The Cross Product
## 외적

### 외적의 정의

$$\mathbf{u}=\langle u_1,u_2,u_3\rangle$$

$$\mathbf{v}=\langle v_1,v_2,v_3\rangle$$

의 외적은

$$\mathbf{u}\times\mathbf{v}=\begin{vmatrix}\mathbf{i}&\mathbf{j}&\mathbf{k}\\u_1&u_2&u_3\\v_1&v_2&v_3\end{vmatrix}$$

이다.

성분으로 쓰면

$$\mathbf{u}\times\mathbf{v}=\langle u_2v_3-u_3v_2,\ u_3v_1-u_1v_3,\ u_1v_2-u_2v_1\rangle$$

이다.

---

### 외적의 방향

$$\mathbf{u}\times\mathbf{v}$$

는 $\mathbf{u}$와 $\mathbf{v}$ 모두에 수직이다.

방향은 오른손법칙으로 결정한다.

---

### 외적의 크기

두 벡터 사이의 각을 $\theta$라고 하면

$$\|\mathbf{u}\times\mathbf{v}\|=\|\mathbf{u}\|\|\mathbf{v}\|\sin\theta$$

이다.

---

### 외적의 반교환성

$$\mathbf{u}\times\mathbf{v}=-(\mathbf{v}\times\mathbf{u})$$

이다.

외적은 교환법칙이 성립하지 않는다.

---

### 평행 조건

두 영이 아닌 벡터가 평행하면

$$\mathbf{u}\times\mathbf{v}=\mathbf{0}$$

이다.

---

### 평행사변형의 넓이

두 벡터가 만드는 평행사변형의 넓이는

$$A=\|\mathbf{u}\times\mathbf{v}\|$$

이다.

삼각형의 넓이는

$$A_{\triangle}=\frac{1}{2}\|\mathbf{u}\times\mathbf{v}\|$$

이다.

---

### 스칼라 삼중곱

세 벡터 $\mathbf{u},\mathbf{v},\mathbf{w}$에 대해

$$\mathbf{u}\cdot(\mathbf{v}\times\mathbf{w})$$

를 스칼라 삼중곱이라고 한다.

그 절댓값은 세 벡터가 만드는 평행육면체의 부피다.

$$V=\left|\mathbf{u}\cdot(\mathbf{v}\times\mathbf{w})\right|$$

---

### 동일평면 조건

세 벡터가 동일평면상에 있으면

$$\mathbf{u}\cdot(\mathbf{v}\times\mathbf{w})=0$$

이다.

---

### 벡터 삼중곱

$$\mathbf{u}\times(\mathbf{v}\times\mathbf{w})=(\mathbf{u}\cdot\mathbf{w})\mathbf{v}-(\mathbf{u}\cdot\mathbf{v})\mathbf{w}$$

이다.

외적은 결합법칙이 성립하지 않는다.

$$\mathbf{u}\times(\mathbf{v}\times\mathbf{w})\ne(\mathbf{u}\times\mathbf{v})\times\mathbf{w}$$

---

### 적용 조건과 주의사항

- 외적은 3차원 벡터에서 정의된다.
- 외적의 결과는 벡터다.
- 순서를 바꾸면 부호가 바뀐다.
- 외적이 영벡터이면 두 벡터가 평행하거나 둘 중 하나가 영벡터다.
- 스칼라 삼중곱에서는 외적과 내적의 순서를 혼동하지 않아야 한다.
- 외적은 결합법칙이 성립하지 않는다.

---

## 2.5 Equations of Lines and Planes in Space
## 공간의 직선과 평면

### 직선의 벡터방정식

점

$$P_0(x_0,y_0,z_0)$$

을 지나고 방향벡터가

$$\mathbf{v}=\langle a,b,c\rangle$$

인 직선은

$$\mathbf{r}=\mathbf{r}_0+t\mathbf{v}$$

이다.

여기서

$$\mathbf{r}=\langle x,y,z\rangle,\qquad \mathbf{r}_0=\langle x_0,y_0,z_0\rangle$$

이다.

---

### 직선의 매개방정식

$$x=x_0+at$$

$$y=y_0+bt$$

$$z=z_0+ct$$

이다.

---

### 직선의 대칭방정식

$a,b,c\ne0$이면

$$\frac{x-x_0}{a}=\frac{y-y_0}{b}=\frac{z-z_0}{c}$$

로 나타낼 수 있다.

방향벡터의 어떤 성분이 $0$이면 해당 좌표는 상수식으로 따로 표시해야 한다.

---

### 두 점을 지나는 직선

두 점 $P_0$와 $P_1$을 지나는 직선의 방향벡터는

$$\overrightarrow{P_0P_1}$$

이다.

따라서

$$\mathbf{r}=\mathbf{r}_0+t(\mathbf{r}_1-\mathbf{r}_0)$$

로 나타낼 수 있다.

---

### 공간의 두 직선 관계

공간의 두 직선은 다음 관계를 가질 수 있다.

- 일치
- 평행
- 교차
- 꼬인 위치

꼬인 직선은 서로 평행하지도 않고 만나지도 않는 직선이다.

---

### 평면의 법선벡터

평면에 수직인 벡터를 법선벡터라고 한다.

$$\mathbf{n}=\langle a,b,c\rangle$$

---

### 평면의 점-법선형

점

$$P_0(x_0,y_0,z_0)$$

을 지나고 법선벡터가

$$\mathbf{n}=\langle a,b,c\rangle$$

인 평면은

$$a(x-x_0)+b(y-y_0)+c(z-z_0)=0$$

이다.

---

### 평면의 일반형

평면은

$$ax+by+cz=d$$

형태로 나타낼 수 있다.

법선벡터는

$$\mathbf{n}=\langle a,b,c\rangle$$

이다.

---

### 세 점을 지나는 평면

서로 일직선상에 있지 않은 세 점 $P,Q,R$이 주어지면

$$\overrightarrow{PQ}$$

와

$$\overrightarrow{PR}$$

은 평면 위의 두 방향벡터다.

법선벡터는

$$\mathbf{n}=\overrightarrow{PQ}\times\overrightarrow{PR}$$

로 구한다.

---

### 두 평면의 관계

두 평면의 법선벡터를 각각 $\mathbf{n}_1,\mathbf{n}_2$라고 하자.

두 법선벡터가 평행하면 두 평면은 평행하거나 일치한다.

$$\mathbf{n}_1=c\mathbf{n}_2$$

두 법선벡터가 수직이면 두 평면은 수직이다.

$$\mathbf{n}_1\cdot\mathbf{n}_2=0$$

평행하지 않은 두 평면의 교선 방향벡터는

$$\mathbf{n}_1\times\mathbf{n}_2$$

이다.

---

### 두 평면 사이의 각

두 평면 사이의 예각은 법선벡터 사이의 예각으로 구한다.

$$\cos\theta=\frac{|\mathbf{n}_1\cdot\mathbf{n}_2|}{\|\mathbf{n}_1\|\|\mathbf{n}_2\|}$$

이다.

---

### 직선과 평면 사이의 각

직선의 방향벡터를 $\mathbf{v}$, 평면의 법선벡터를 $\mathbf{n}$이라고 하자.

직선과 평면 사이의 각을 $\alpha$라고 하면

$$\sin\alpha=\frac{|\mathbf{v}\cdot\mathbf{n}|}{\|\mathbf{v}\|\|\mathbf{n}\|}$$

이다.

---

### 점과 평면 사이의 거리

점

$$P(x_0,y_0,z_0)$$

과 평면

$$ax+by+cz+d=0$$

사이의 거리는

$$D=\frac{|ax_0+by_0+cz_0+d|}{\sqrt{a^2+b^2+c^2}}$$

이다.

---

### 평행한 두 평면 사이의 거리

평행한 두 평면

$$ax+by+cz=d_1$$

$$ax+by+cz=d_2$$

사이의 거리는

$$D=\frac{|d_2-d_1|}{\sqrt{a^2+b^2+c^2}}$$

이다.

---

### 점과 직선 사이의 거리

점 $P$와, 점 $P_0$을 지나 방향벡터 $\mathbf{v}$를 갖는 직선 사이의 거리는

$$D=\frac{\|\overrightarrow{P_0P}\times\mathbf{v}\|}{\|\mathbf{v}\|}$$

이다.

---

### 적용 조건과 주의사항

- 직선의 방향벡터와 평면의 법선벡터를 혼동하지 않아야 한다.
- 공간에서 평행하지 않은 두 직선이 반드시 만나는 것은 아니다.
- 대칭방정식은 방향벡터 성분이 $0$이면 그대로 사용할 수 없다.
- 세 점으로 평면을 만들려면 세 점이 일직선상에 있지 않아야 한다.
- 평면 사이의 각은 법선벡터 사이의 각으로 구한다.
- 거리공식의 분모는 법선벡터 또는 방향벡터의 크기다.

---

## 2.6 Quadric Surfaces
## 이차곡면

### 이차곡면의 정의

3차원에서 이차방정식으로 표현되는 곡면을 이차곡면이라고 한다.

일반형은

$$Ax^2+By^2+Cz^2+Dxy+Exz+Fyz+Gx+Hy+Iz+J=0$$

이다.

---

### 자취와 단면

곡면의 형태를 파악하기 위해

$$x=k,\qquad y=k,\qquad z=k$$

형태의 평면으로 잘라 단면을 조사한다.

좌표평면과의 교선을 자취라고 한다.

---

### 원기둥

방정식에 한 변수가 나타나지 않으면 그 변수 방향으로 무한히 뻗는 원기둥형 곡면이 된다.

예를 들어

$$x^2+y^2=4$$

는 $z$가 없으므로 $z$축 방향으로 뻗는 원기둥이다.

---

### 타원면

타원면의 표준형은

$$\frac{x^2}{a^2}+\frac{y^2}{b^2}+\frac{z^2}{c^2}=1$$

이다.

세 좌표평면과의 단면은 모두 타원이다.

$a=b=c$이면 구가 된다.

---

### 일엽쌍곡면

표준형은

$$\frac{x^2}{a^2}+\frac{y^2}{b^2}-\frac{z^2}{c^2}=1$$

이다.

두 개의 양의 제곱항과 하나의 음의 제곱항이 있다.

음의 항에 해당하는 축이 중심축이다.

곡면은 하나로 연결되어 있다.

---

### 이엽쌍곡면

표준형은

$$-\frac{x^2}{a^2}-\frac{y^2}{b^2}+\frac{z^2}{c^2}=1$$

이다.

하나의 양의 제곱항과 두 개의 음의 제곱항이 있다.

양의 항에 해당하는 축 방향으로 두 조각이 열린다.

---

### 타원뿔

표준형은

$$\frac{x^2}{a^2}+\frac{y^2}{b^2}-\frac{z^2}{c^2}=0$$

이다.

원점을 꼭짓점으로 하며 양쪽 방향으로 열린다.

---

### 타원포물면

표준형은

$$z=\frac{x^2}{a^2}+\frac{y^2}{b^2}$$

이다.

$z=k>0$에서의 단면은 타원이고, 수직 단면은 포물선이다.

한 방향으로 열린 그릇 모양이다.

---

### 쌍곡포물면

표준형은

$$z=\frac{x^2}{a^2}-\frac{y^2}{b^2}$$

이다.

두 제곱항의 부호가 반대이며 안장 모양을 갖는다.

수직 단면은 서로 반대 방향으로 열린 포물선이고, 수평 단면은 쌍곡선이다.

---

### 이차곡면 식별 기준

- 제곱항의 부호
- 우변이 $0$인지 $1$인지
- 어떤 변수가 일차로 나타나는지
- 어떤 변수가 식에 나타나지 않는지
- 좌표평면 단면의 형태
- 열린 방향과 대칭축

---

### 적용 조건과 주의사항

- 방정식에 한 변수가 없으면 그 방향으로 뻗는 원기둥형 곡면일 수 있다.
- 일엽쌍곡면과 이엽쌍곡면은 양의 항과 음의 항의 개수로 구분한다.
- 타원포물면과 쌍곡포물면은 제곱항의 부호로 구분한다.
- 이차곡면은 좌표평면 단면을 확인하면 형태를 판단하기 쉽다.
- 평행이동된 곡면은 완전제곱을 통해 표준형으로 바꾼다.

---

## Chapter 2 핵심 공식 요약

### 벡터의 크기

$$\|\mathbf{v}\|=\sqrt{v_1^2+v_2^2+v_3^2}$$

### 단위벡터

$$\mathbf{u}=\frac{\mathbf{v}}{\|\mathbf{v}\|}$$

### 내적

$$\mathbf{u}\cdot\mathbf{v}=u_1v_1+u_2v_2+u_3v_3$$

$$\cos\theta=\frac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{u}\|\|\mathbf{v}\|}$$

### 정사영

$$\operatorname{proj}_{\mathbf{v}}\mathbf{u}=\frac{\mathbf{u}\cdot\mathbf{v}}{\|\mathbf{v}\|^2}\mathbf{v}$$

### 외적

$$\mathbf{u}\times\mathbf{v}=\langle u_2v_3-u_3v_2,\ u_3v_1-u_1v_3,\ u_1v_2-u_2v_1\rangle$$

$$\|\mathbf{u}\times\mathbf{v}\|=\|\mathbf{u}\|\|\mathbf{v}\|\sin\theta$$

### 평행사변형의 넓이

$$A=\|\mathbf{u}\times\mathbf{v}\|$$

### 평행육면체의 부피

$$V=\left|\mathbf{u}\cdot(\mathbf{v}\times\mathbf{w})\right|$$

### 직선

$$\mathbf{r}=\mathbf{r}_0+t\mathbf{v}$$

### 평면

$$a(x-x_0)+b(y-y_0)+c(z-z_0)=0$$

### 점과 평면 사이의 거리

$$D=\frac{|ax_0+by_0+cz_0+d|}{\sqrt{a^2+b^2+c^2}}$$

### 구

$$(x-h)^2+(y-k)^2+(z-l)^2=r^2$$

---

## 자주 혼동하는 사항

- 점과 벡터는 표기가 비슷하지만 서로 다른 개념이다.
- 내적의 결과는 스칼라이고 외적의 결과는 벡터다.
- 내적이 $0$이면 수직이고 외적이 영벡터이면 평행이다.
- 외적은 순서를 바꾸면 부호가 바뀐다.
- 정사영 공식의 분모는 $\|\mathbf{v}\|^2$이다.
- 직선의 방향벡터와 평면의 법선벡터를 혼동하지 않아야 한다.
- 공간의 두 직선은 꼬인 위치에 있을 수 있다.
- 일엽쌍곡면과 이엽쌍곡면은 제곱항의 부호 개수로 구분한다.
