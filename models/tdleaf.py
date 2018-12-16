import rule
import random
from trainer import *

def tdleaf(sess, model, initial_board, red, lamb=0.7, depth=12):
    initial_score = evaluate(sess, model, initial_board, red)
    series = []
    k = 0
    while pv_position(initial_board, red) or k < depth:
        boards = next_boards(initial_board, red)
        gameover_board, gameover_score = contains_gameover(boards, red)
        if gameover_board is not None:
            series.append((gameover_board, not red, gameover_score))
       #     print('gameover score:', gameover_score, 'side:', not red)
            break
        scores = batch_evaluate(sess, model, boards, not red)
        initial_board, score = optimal_board(boards, scores, red)
        if k + 1 == depth:
            score = rule.basic_score(initial_board)
        red = not red
        series.append((initial_board, red, score))
        if abs(score) >= rule.GAMEOVER_THRESHOLD:
            break
        k += 1

    series = series[-depth:]
    weight = 1
    total_score = 0
    last_score = 0
    for _, _, score in series:
        total_score += (score - last_score) * weight
        last_score = score
        weight *= lamb
    return total_score, [(board, red) for board, red, _ in series]
    

def contains_gameover(boards, red):
    for board in boards:
        score = rule.basic_score(board)
        if abs(score) > rule.GAMEOVER_THRESHOLD:
            return board, score
    return None, None


def next_boards(board, red):
    moves = rule.next_steps(board, red)
    return [rule.next_board(board, move) for move in moves]


def evaluate(sess, model, board, red):
    return batch_evaluate(sess, model, [board], red)


def batch_evaluate(sess, model, boards, red):
    batch_board_red = [(board, red) for board in boards]
 #   scores = predict(sess, model, batch_board_red)
    scores = [random.randint(-1000, 1000) for _ in boards]
    return scores


def optimal_board(boards, scores, red):
    combined = list(zip(scores, boards))
    score, board = sorted(combined, reverse=not red)[0]
    return board, score


def pv_position(initial_board, red):
    return False