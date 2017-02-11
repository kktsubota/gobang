import numpy as np
import numba
import multiprocessing as mp
import time
import main
from evaluation import *
import cv2
N = 7
M = 4
Fsize = N * N

SIZE = 490
state = False


def on_mouse(event, x, y, flag, params):
    global state
    image, winname, points, board = params
    if not state:
        return
    if event == cv2.EVENT_LBUTTONDOWN:
        # get nearest neighbor
        p = np.array((x, y))
        tmp = points - p
        idx = np.argmin(np.sum(np.square(tmp), axis=1))
        p = points[idx, :]
        cv2.circle(image, center=tuple(p.tolist()), radius=20, color=0, thickness=-1)
        # cv2.imshow(winname, image)
        y, x = (p - 35) // 70
        board[x, y] = -1
        if not main.winning(-board):
            state = not state

def play(model):
    board = np.zeros((N, N), dtype=np.int8)
    turn = True

    global state
    image = np.ones((SIZE, SIZE), dtype=np.uint8) * 180
    points = []
    for i in range(N):
        cv2.line(image, (0, 35 + 70 * i), (SIZE-1, 35 + 70 * i), color=0, thickness=3)
        cv2.line(image, (35 + 70 * i, 0), (35 + 70 * i, SIZE-1), color=0, thickness=3)

        for j in range(N):
            points.append((35 + 70 * i, 35 + 70 * j))

    points = np.array(points)

    cv2.namedWindow('window', flags=cv2.WINDOW_AUTOSIZE)
    reward = 0
    while True:
        cv2.setMouseCallback('window', on_mouse, [image, 'window', points, board])
        cv2.imshow('window', image)
        if main.winning(-board) or reward != 0:
            cv2.imshow('window', image)
            key = cv2.waitKey(10)
            return
        key = cv2.waitKey(1)
        if key == ord('q'):
            return

        if not state:
            board, reward = com_turn(image, board, points)
            if reward == 0:
                state = not state


def com_turn(image, board, points):
    actions = np.array(np.where(board == 0))
    features = main.getFeatures(board, actions)

    r = np.argmax(model.get(features)[:, 0])

    action = actions[:, r]
    feature = features[r, :]

    Reward = main.reward(board, action)

    # put
    board[action[0], action[1]] = 1

    # all masses are filled, win
    p = action * 70 + 35
    p = p.tolist()
    p.reverse()
    cv2.circle(image, center=tuple(p), radius=20, color=255, thickness=-1)

    return (board, Reward)

if __name__ == '__main__':
    model = main.MyChain()
    serializers.load_npz('./params/10000.model', model)
    play(model=model)