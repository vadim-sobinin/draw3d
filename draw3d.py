from tkinter import *
from math import *
import numpy as np


# Матрица вращения по осям X и Y
def R(phi, teta):
    X = np.matrix([[1, 0, 0],
                   [0, cos(phi), -sin(phi)],
                   [0, sin(phi), cos(phi)]])

    Y = np.matrix([[cos(teta), 0, sin(teta)],
                      [0, 1, 0],
                      [-sin(teta), 0, cos(teta)]])
    return X*Y


# метод получения видовых координат
def View():
    for i in range(len(Wx)):
        # получаем матрицу вращения
        rot = R(phi, teta)
        # трансформируем точку
        v = np.array([Wx[i], Wy[i], Wz[i]]) * rot

        Vx[i] = v[0, 0] + w/2
        Vy[i] = v[0, 1] + h/2
        Vz[i] = v[0, 2]


# рисование каркасной модели
def Draw():
    

    # массив граней: индексы в массивах точек и цвет
    triangles = [
        [0, 3, 13, '#A98307'],
        [4, 0, 13, '#3D642D'],
        [4, 7, 13, '#898176'],
        [3, 7, 13, '#D84B20'],

        [1, 0, 10, '#57A639'],
        [1, 5, 10, '#FF7514'],
        [4, 5, 10, '#9DA1AA'],
        [4, 0, 10, '#CFD3CD'],

        [5, 4, 9, '#C51D34'],
        [5, 6, 9, '#1D334A'],
        [7, 6, 9, '#9E9764'],
        [7, 4, 9, '#8D948D'],

        [6, 5, 11, '#212121'],
        [6, 2, 11, '#7FB5B5'],
        [1, 2, 11, '#E444D8'],
        [1, 5, 11, '#16988C'],

        [0, 1, 8, '#2298FB'],
        [0, 3, 8, '#8902F4'],
        [2, 3, 8, '#1D1326'],
        [2, 1, 8, '#1BDA4A'],

        [6, 7, 12, '#ED2909'],
        [6, 2, 12, '#3D18DF'],
        [3, 2, 12, '#4DEAA1'],
        [3, 7, 12, '#EDAB4E']
    ]

    # сортируем по Z координатам, в качестве ключа берем центроиды треугольников
    zorder = sorted(triangles,
                    key=lambda idx: (Vz[idx[0]] + Vz[idx[1]] + Vz[idx[2]])/3)

    for p1, p2, p3, color in zorder:
        c.create_polygon(Vx[p1], Vy[p1], Vx[p2], Vy[p2], Vx[p3], Vy[p3], fill=color)

    

# метод нажатия на кнопку ВВЕРХ
def up():
    global teta
    global phi
    phi += 0.1
    c.delete('all')
    View()
    Draw()


# метод нажатия на кнопку ВНИЗ
def down():
    global teta
    global phi
    phi -= 0.1
    c.delete('all')
    View()
    Draw()


# метод нажатия на кнопку ВЛЕВО
def left():
    global teta
    global phi
    teta -= 0.1
    c.delete('all')
    View()
    Draw()


# метод нажатия на кнопку ВПРАВО
def right():
    global teta
    global phi
    teta += 0.1
    c.delete('all')
    View()
    Draw()


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

# исходные данные
# размер формы
w = 600
h = 400
# мировые координаты объекта
Wx = [-50, 50, 50, -50, -50, 50, 50, -50, 0, 0, 0, 150, 0, -150]
Wy = [-50, -50, 50, 50, -50, -50, 50, 50, 0, 0, -150, 0, 150, 0]
Wz = [-50, -50, -50, -50, 50, 50, 50, 50, -150, 150, 0, 0, 0, 0]
# положение точки наблюдения
teta = pi / 4
phi = pi / 4
ro = 500
d = 200
# видовые координаты
Vx = [0] * len(Wx)
Vy = [0] * len(Wx)
Vz = [0] * len(Wz)
# создаем объекты
root = Tk()

# реагируем обработчик событий клавиатуры
root.bind('<Key>', keypress)
c = Canvas(root, width=w, height=h, bg='#00ff00')
c.pack()

b1 = Button(text='Left', command=left, padx="80")
b1.pack(side=LEFT, fill=Y)

b2 = Button(text='Right', command=right, padx="80")
b2.pack(side=RIGHT, fill=Y)

b3 = Button(text='Up', command=up, pady="35")
b3.pack(side=TOP, fill=X)

b4 = Button(text='Down', command=down, pady="35")
b4.pack(side=BOTTOM, fill=X)

View()
Draw()

root.mainloop()

