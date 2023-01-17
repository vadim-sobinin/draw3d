import numpy as np
from math import *


# рисователь примитивов, абстрактный класс
class Render:
    def __init__(self):
        pass

    # треугольник
    def draw_tri(self, p1, p2, p3, color):
        raise NotImplemented()

    # прямоугольник
    def draw_quad(self, p1, p2, p3, p4, color):
        raise NotImplemented()

    # текст
    def draw_text(self, x, y, color, font):
        raise NotImplemented()

    # линия
    def draw_line(self, p1, p2, width, color):
        raise NotImplemented()

    # очистить экран
    def clear_screen(self):
        raise NotImplemented()


# конвертировать цвет из hex в rgb '#FF00FF -> np.array(255, 0, 255)
def hex_to_rgb(color):
    if isinstance(color, str):
        if color[0] == '#':
            color = color[1:]
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return np.array([r, g, b])
    else:
        return color


# конвертировать rgb цвет в hex, (255, 0, 0) -> '#FF0000'
def rgb_to_hex(rgb):
    r, g, b = rgb
    return f'#{int(r):02x}{int(g):02x}{int(b):02x}'


# рисователь примитивов для Canvas/tkinter
class CanvasRender(Render):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def draw_tri(self, p1, p2, p3, color):
        self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], fill=rgb_to_hex(color))

    def draw_line(self, p1, p2, width, color):
        self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], width=width, fill=rgb_to_hex(color))

    def draw_quad(self, p1, p2, p3, p4, color):
        self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1], fill=rgb_to_hex(color))

    def clear_screen(self):
        self.canvas.delete('all')


# класс-помощник для работы с матрицами аффинных преобразований
class Transform:
    def __init__(self, x=0.0, y=0.0, z=0.0, phi=0.0, teta=0.0, psi=0.0, sx=1.0, sy=1.0, sz=1.0):
        """
        :param x: смещение по x
        :param y: смещение по y
        :param z: смещение по z
        :param phi: угол вращения по оси X
        :param teta: угол вращения по оси Y
        :param psi: угол вращения по оси Z
        """
        self.x = x
        self.y = y
        self.z = z
        self.phi = phi
        self.teta = teta
        self.psi = psi
        self.sx = sx
        self.sy = sy
        self.sz = sz

    @property
    def matrix(self):
        """
        Собрать все преобразования в одну матрицу 4x4
        """
        # масштабирование
        scale = np.diag([self.sx, self.sy, self.sz, 1.0])
        # добавляем вращение
        t = self.rot * scale.T
        # добавляем смещение
        t[3, :3] = np.array([self.x, self.y, self.z])
        return t

    @property
    def rot(self):
        """
        Преобразовать углы эйлера (teta, phi, pis) в матрицу вращения
        """
        x = np.matrix([[1, 0, 0, 0],
                       [0, cos(self.phi), -sin(self.phi), 0],
                       [0, sin(self.phi), cos(self.phi), 0],
                       [0, 0, 0, 1]])

        y = np.matrix([[cos(self.teta), 0, sin(self.teta), 0],
                       [0, 1, 0, 0],
                       [-sin(self.teta), 0, cos(self.teta), 0],
                       [0, 0, 0, 1]])
        z = np.matrix([[cos(self.psi), -sin(self.psi), 0, 0],
                       [sin(self.psi), cos(self.psi), 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]])

        return x*y*z


# параметры камеры/ наблюдателя
class View:
    def __init__(self,  w=400, h=300, d=200, persp=False):
        """
        :param w: ширина в пикселях
        :param h: высота в пикселях
        :persp: включить/выключить перспективные преобразования
        """

        self.transform = Transform()

        self.w = w
        self.h = h
        self.persp = persp
        self.d = d

    def to_screen(self, points):
        res = []
        for v in points:
            x, y, z = v
            # требуется перспективное преобразование
            if self.persp:
                z = z-500
                if z == 0:
                    z = 1
                f = self.d/z
                x = int(x*f) + self.w//2
                y = int(y*f) + self.h//2
            else:
                x = int(x) + self.w//2
                y = int(y) + self.h//2
            res.append((x, y))
        return res


# базовый класс для любых 3d объектов
class Object3D:
    def __init__(self, pos=None, rot=None, scale=None, color=(255, 255, 255)):
        self.color = color

        # задаем координаты объекта по-умолчанию
        if pos is None:
            pos = [0.0, 0.0, 0.0]

        # задаем  масштабирование объекта  по-умолчанию
        if scale is None:
            scale = [1.0, 1.0, 1.0]

        # задаем  вращение объекта по-умолчанию
        if rot is None:
            rot = [0.0, 0.0, 0.0]

        # устанавливаем матрицу трансформации для объекта
        self.transform = Transform(pos[0], pos[1], pos[2], rot[0], rot[1], rot[2], scale[0], scale[1], scale[2])

    # преобразовать геометрию объекта и получить треугольники
    def get_geometry(self, transform: Transform):
        raise NotImplemented()


# объект, состоящий из многоугольников
class Poly3D(Object3D):
    def __init__(self, xyz, polys, pos=None, rot=None, scale=None, color=(255, 255, 255)):
        """
        :param xyz: списки координат точек
        :param polys: грани в формате [0, 1, 2, color]
        :param pos: позиция объекта на сцене [x, y, z]
        :param rot: вращение объекта [phi, teta, psi]
        :param color: цвет граней по умолчанию
        """
        super().__init__(pos, rot, scale, color)
        x, y, z = xyz
        # переводим координаты в вид, удобный для перемножения на матрицу 4x4
        self.V = np.array([x, y, z, [1] * len(x)])
        self.polys = polys

    # получаем список треугольников для отрисовки
    def get_geometry(self, transform: Transform):
        if transform is None:
            M = self.transform.matrix
        else:
            # перемножаем собственное преобразование объекта с видовым
            M = transform.matrix * self.transform.matrix

        # преобразуем все точки фигуры
        points = (self.V.T * M)[:, 0:3]

        # получаем список готовых треугольников с координатами каждой точки
        # p[0] - список граней для каждого треугольника в self.polys, например (0, 1, 2)
        # points[(0, 1, 2), :] - из списка points получаем координаты точек для треугольника
        # np.concatenate - получам np.array из списка списков точек
        # .reshape(len(self.polys), 3, 3) приводит его к следующей форме
        # [[[0,0,0], [0, 1, 0.5], [1, 1, 1]], ...]
        triangles = np.concatenate([np.array(points[p[0], :]) for p in self.polys]).reshape(len(self.polys), 3, 3)

        # все цвета из hex конвертируем в rgb
        colors = [hex_to_rgb(p[1]) for p in self.polys]

        return triangles, colors


# звезда
class Star(Poly3D):
    def __init__(self, pos=None, rot=None, scale=None):
        Wx = [-50, 50, 50, -50, -50, 50, 50, -50, 0, 0, 0, 150, 0, -150]
        Wy = [-50, -50, 50, 50, -50, -50, 50, 50, 0, 0, -150, 0, 150, 0]
        Wz = [-50, -50, -50, -50, 50, 50, 50, 50, -150, 150, 0, 0, 0, 0]


        polys = [
            [(0, 3, 13), '#A98307'],
            [(4, 0, 13), '#3D642D'],
            [(13, 7, 4), '#898176'],
            [(3, 7, 13), '#D84B20'],

            [(1, 0, 10), '#57A639'],
            [(10, 5, 1), '#FF7514'],
            [(4, 5, 10), '#9DA1AA'],
            [(10, 0, 4), '#CFD3CD'],

            [(5, 4, 9), '#C51D34'],
            [(9, 6, 5), '#1D334A'],
            [(7, 6, 9), '#9E9764'],
            [(9, 4, 7), '#8D948D'],

            [(11, 5, 6), '#212121'],
            [(6, 2, 11), '#7FB5B5'],
            [(11, 2, 1), '#E444D8'],
            [(1, 5, 11), '#16988C'],

            [(0, 1, 8), '#2298FB'],
            [(8, 3, 0), '#8902F4'],
            [(2, 3, 8), '#1D1326'],
            [(8, 1, 2), '#1BDA4A'],

            [(6, 7, 12), '#ED2909'],
            [(12, 2, 6), '#3D18DF'],
            [(3, 2, 12), '#4DEAA1'],
            [(12, 7, 3), '#EDAB4E']
        ]

        super().__init__([Wx, Wy, Wz], polys, pos, rot, scale)


# плоский прямоугольник из двух треугольников, который лежит на плоскости X/Z
class Quad(Poly3D):
    def __init__(self, w, h, y=0.0, pos=None, rot=None, scale=None, color=(0, 255, 255)):
        Wx = [-w/2, -w/2, w/2, w/2]
        Wz = [-h/2, h/2, h/2, -h/2]
        Wy = [y, y, y, y]
        polys = [[(2, 1, 0), color], [(3, 2, 0), color]]

        super().__init__([Wx, Wy, Wz], polys, pos, rot, scale)


# куб
class Cube(Poly3D):
    def __init__(self, side, pos=None, rot=None, scale=None, color=(255, 200, 0)):

        Wx = (np.array([0, 1, 1, 0, 0, 1, 1, 0])-0.5)*side
        Wz = (np.array([0, 0, 1, 1, 1, 1, 0, 0])-0.5)*side
        Wy = (np.array([0, 0, 0, 0, 1, 1, 1, 1])-0.5)*side
        polys = [(0, 2, 1),
                 (0, 3, 2),
                 (2, 3, 4),
                 (2, 4, 5),
                 (1, 2, 5),
                 (1, 5, 6),
                 (0, 7, 4),
                 (0, 4, 3),
                 (5, 4, 7),
                 (5, 7, 6),
                 (0, 6, 7),
                 (0, 1, 6)]
        polys = [(t, color) for t in polys]

        super().__init__([Wx, Wy, Wz], polys, pos, rot, scale)


# модель из obj файла
class ObjMesh(Poly3D):
    def __init__(self, filename, pos=None, rot=None, scale=None, color=(255, 200, 0)):
        points, polys = self.parse(filename)
        polys = [(t, color) for t in polys]
        super().__init__(points, polys, pos, rot, scale)

    def parse(self, filename):
        with open(filename, 'rt') as f:
            vx = []
            vy = []
            vz = []
            tris = []

            for line in f.readlines():
                # парсим только два вида данных - точка и треугольник, остальное игнорим
                # v 2.229345 -0.992723 -0.862826
                # f 25 20 22
                cmd, *data = line.split()
                if cmd == 'v':
                    x, y, z = data
                    vx.append(float(x))
                    vy.append(float(y))
                    vz.append(float(z))
                elif cmd == 'f':
                    if '/' in data[0]:
                        # отбрасываем лишние индексы (для нормалей,итп)
                        data[0] = data[0].split('/')[0]
                        data[1] = data[1].split('/')[0]
                        data[2] = data[2].split('/')[0]
                        if len(data) == 4:
                            data[3] = data[3].split('/')[0]
                    if len(data) == 4:
                        p0, p1, p2, p3 = (int(data[0]) - 1,
                                          int(data[1]) - 1,
                                          int(data[2]) - 1,
                                          int(data[3]) - 1)
                        tris.append((p0, p1, p3))
                        tris.append((p1, p2, p3))
                    else:
                        tris.append((int(data[0]) - 1, int(data[1]) - 1, int(data[2]) - 1))
        return [vx, vy, vz], tris


# вычисление нормали по трем точкам
def normal_calc(pts):
    # находим вектора двух граней треугольника
    A = pts[:, 1]-pts[:, 0]
    B = pts[:, 2]-pts[:, 0]
    cross = np.cross(A, B)
    # нормализуем, чтобы получить единичные вектора
    # https://stackoverflow.com/questions/2850743/numpy-how-to-quickly-normalize-many-vectors
    return cross / np.sqrt((cross ** 2).sum(-1))[..., np.newaxis]


# возвращаем центроид Z-координат для треугольника
def zorder(p):
    return (p[0][2] + p[1][2] + p[2][2])/3


# 3d сцена
class Scene:
    def __init__(self, view=None, render: Render=None, flat_shading=True, backface_cull=False):
        """
        :param view: настройки камеры/зрителя
        :param render: класс который рисует
        :param backface_cull: отсечение невидимых граней
        :param flat_shading: включить/выключить плоское закрашивание
        :param objects:
        """
        self.view = view
        self.render = render
        self.objects = []
        self.backface_cull = backface_cull
        self.flat_shading = flat_shading

    def add_object(self, obj):
        self.objects.append(obj)

    def draw(self):
        self.render.clear_screen()
        # все треугольники сцены
        triangles = []
        # цвета треугольников
        colors = []

        for obj in self.objects:
            # геоме
            tris, cols = obj.get_geometry(transform=self.view.transform)
            triangles.extend(tris)
            colors.extend(cols)

        triangles = np.array(triangles)

        # флаг плоского закрашивания включен
        if self.flat_shading:
            # вычисляем нормали
            normals = normal_calc(triangles)

            # "для получения цвета грани нужно умножить каждую компоненту на абсолютное значение nz."
            colors = [np.array(colors[i]) * fabs(normals[i][2]) for i in range(len(normals))]

        def by_z(idx):
            return zorder(triangles[idx])

        # вместо самих треугольников сортируем их индексы
        for i in sorted(range(len(triangles)), key=by_z):
            # отсекаем невидимые грани, нормаль которых повернута от наблюдателя

            if self.backface_cull:
                if normals[i][2] > 0:
                    continue

            # преобразуем треугольник к экранным координатам
            p = self.view.to_screen(triangles[i])

            self.render.draw_tri(p[0], p[1], p[2], colors[i])

            # рисуем красный wireframe, для отладки
            # red = (255, 0, 0)
            # self.render.draw_line(p[0], p[1], 1, red)
            # self.render.draw_line(p[1], p[2], 1, red)
            # self.render.draw_line(p[2], p[0], 1, red)


w = 600
h = 400
v = View(w, h, d=100, persp=True)

from tkinter import *

# создаем объекты
root = Tk()

c = Canvas(root, width=w, height=h, bg='#00ff00')
c.pack()

scene = Scene(v, CanvasRender(c))
# star = Star(pos=[500, 100, -100], rot=[pi/4, 0, pi/4])
sphere = ObjMesh('sphere.obj', scale=[0.1, 0.1, 0.1])
# cat = ObjMesh('cat.obj', scale=[14, 14, 14], rot=[pi/2, 7*pi/4, 0], pos=[0, -300, 180])
# scene.add_object(star)
scene.add_object(sphere)
# scene.add_object(cat) 


# метод нажатия на кнопку ВВЕРХ
def up():
    scene.view.transform.phi += 0.1
    scene.draw()


# метод нажатия на кнопку ВНИЗ
def down():
    scene.view.transform.phi -= 0.1
    scene.draw()


# метод нажатия на кнопку ВЛЕВО
def left():
    scene.view.transform.teta -= 0.1
    scene.draw()


# метод нажатия на кнопку ВПРАВО
def right():
    scene.view.transform.teta += 0.1
    scene.draw()


# реагируем на нажатия вверх-вниз-вправо-влево
def keypress(e):
    if e.keysym == 'Up':
        up()
    elif e.keysym == 'Down':
        down()
    elif e.keysym == 'Left':
        left()
    elif e.keysym == 'Right':
        right()

"""
# пример с анимацией
def update():
    # простая анимация, вращаем звезду каждые 50 мс
    global star
    global scene
    star.transform.teta += 0.05
    scene.draw()
    root.after(50, update)
"""

# регистрируем обработчик клавиатуры
root.bind('<Key>', keypress)

b1 = Button(text='Left', command=left, padx="80")
b1.pack(side=LEFT, fill=Y)

b2 = Button(text='Right', command=right, padx="80")
b2.pack(side=RIGHT, fill=Y)

b3 = Button(text='Up', command=up, pady="35")
b3.pack(side=TOP, fill=X)

b4 = Button(text='Down', command=down, pady="35")
b4.pack(side=BOTTOM, fill=X)

scene.draw()

#root.after(50, update)

root.mainloop()
