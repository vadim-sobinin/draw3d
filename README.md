# Простой 3d конвеер с использованием Tkinter

Задача этого проекта - написать скрипт, который сможет рисовать 3d модели без использования специализированных библиотек.

В результате работы удалось реализовать построение перспективной проекции геометрических фигур, сортировку граней по глубине (алгоритм художника или Z-буффер), плоское закрашивание граней, и конвертацию файла в формате .obj в 3d объект.

В итоге, опытным путём доказано, что Tkinter не преднозначен и не справляется с рендерингом многогранной 3d модели с парой десятков тысяч граней, с чем успешно справляются более сложные специализированные библиотеки на подобие OpenGL.

![3д модель "звезды", модель](https://i.imgur.com/ZqwuyhA.png)
![3д модель "Мишка", модель](https://i.imgur.com/TLXVzAo.png)

## Как работать с классом Scene

1. Сначала создаем View, этот класс отвечает за преобразование геометрии к экранным координатам

```python
v = View(высота_в_пикселях, ширина_в_пикселях, d=300, persp=True)
# d - константа для перспективного преобразования.
# persp = True - включить перспективу, persp = False - выключить

```

Чем больше константа d, тем ближе будут казаться объекты и наоборот. От 200 до 500 смотрится нормально.

2. Создаем сцену

```python
# flat_shading - включить/выключить закрашивание
# backface_cull - включить/выключить отсечение треугольников, нормали которых повернуты в противоположную от экрана сторону
scene = Scene(v, CanvasRender(canvas), flat_shading=True, backface_cull=False)
```

3. Добавляем к сцене объекты

```python
cube = Cube(side=100)
# задаем начальную позицию и поворот.
star = Star(pos=[500, 100, -100], rot=[pi/4, 0, pi/4])
# здесь уменьшаем масштаб в десять раз, иначе объект не уместится в экран
sphere = ObjMesh('sphere.obj', scale=[0.1, 0.1, 0.1])
```

У наследников Poly3D в конструкторе есть такие параметры:

- **rot** - эйлеровские углы поворота фигуры
- **scale** - вектор масштабирования по осям [x, y, z], по-умолчанию [1, 1, 1]
- **pos** - точка, в которой находится центр объекта

_TODO: по оси x координаты идут от положительных слева до отрицательных справа. Это особо ни на что не влияет, поэтому не исправлял. _

С помощью этих параметров инициализируется поле transform. В ней все эти параметры можно менять вручную, например:

```python
cube = Cube(side=100)
# сдвигаем по оси z
cube.transform.z += 1000
# вращаем
cube.transform.teta += pi/4
# растягиваем по оси x в два раза
cube.transform.sx = 2.0
```

У класса View есть такое же поле transform, которое позволяет делать тоже самое, но для всей сцены сразу.

Эти трансформации не обновляются мгновенно, а вычисляются только при вызове свойства transform.matrix. Это обычно происходит при вызове метода **Poly3D.get_geometry** из **Scene.draw**.

##3) Минимальный кастомный 3d объект

Базовый примитив, который можно нарисовать - треугольник. Пусть для примера у нас будет такой треугольник:

```python
  points = [[0, 0, 0], [0, 1, 0], [0, 1, 1]]
```

Создаем новый класс Triangle и наследуем от Poly3D:

```python
class Triangle(Poly3D):
    def __init__(self, pos=None, rot=None, scale=None, color=(255, 0, 0)):
        points = [[0, 0, 0], [0, 1, 0], [0, 1, 1]]
        super().__init__([координаты], треугольники, pos, rot, scale)
```

Сложность в том, что у нас точки в виде [[x1, y1, z1], .., [xN, yN, zN]]. А для конструктора Poly3D нам нужно:

```python
[[x1, .. xN], [y1, .., yN], [z1, .., zN]]
```

Пока просто вручную приведем координаты к нужному виду:

```python
class Triangle(Poly3D):
    def __init__(self, pos=None, rot=None, scale=None, color=(255, 0, 0)):
        p = [[0, 0, 0], [0, 1, 0], [0, 1, 1]]
        Wx = [p[0][0], p[1][0], p[2][0]]
        Wy = [p[0][1], p[1][1], p[2][1]]
        Wz = [p[0][2], p[1][2], p[2][2]]
        # наш единственный треугольник
        # можно сделать в любом порядке, например (1, 2, 0), (2, 1, 0)
        # но от этого будет зависеть направление нормали, что может повлиять на корректность рендеринга
        polys = [(0, 1, 2), color]
        super().__init__([Wx, Wy, Wz], polys, pos, rot, scale)
```

Теперь построим пирамиду по этому рисунку:
![кривая пирамида, рисунок](https://i.imgur.com/eCcAQkY.png)

```python
class Pyramid(Poly3D):
    def __init__(self, pos=None, rot=None, scale=None):
        # основание нашей пирамиды, прямоугольник из двух треугольников
        Wx = [-1, -1, 1, 1]
        Wz = [-1, 1, 1, -1]
        # по оси Y одни нули, т.к. основание лежит на плоскости
        Wy = [0, 0, 0, 0]
        # сделаем треугольники основания разных цветов для наглядности
        polys = [[(0, 1, 2), (255, 0, 0)], [(3, 0, 2), (0, 0, 255)]]

        # добавляем вершину пирамиды в точке (x:0, y:2, z:0)
        Wx.append(0)
        Wz.append(0)
        Wy.append(2)
        yellow = (255, 255, 0)

        # добавляем треугольники от основания к вершине
        polys += [[(4, 1, 0), yellow],
                  [(3, 4, 0), yellow],
                  [(2, 4, 3), yellow],
                  [(1, 4, 2), yellow]]
        super().__init__([Wx, Wy, Wz], polys, pos, rot, scale)
```

Использование в сцене:

```python
# включим отсечение обратных граней
# чтобы убедиться что у всех треугольников точки указаны в правильном порядке
scene = Scene(v, CanvasRender(c), backface_cull=True)
# увеличиваем пирамиду в 100 раз, т.к. ее размеры заданы как 2x2x2
pyramid = Pyramid(scale=[100, 100, 100])
scene.add_object(pyramid)
```
