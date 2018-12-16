import rule
import random
import trainer
import torch
import torch.nn as nn
import numpy as np
import data
import models
import board_queue


def predict(model, batch_board_red):
    feed = data.create_feed(batch_board_red)
    scores = model(feed['square'], feed['length'])
    return data.unfeed(scores, [red for _, red in batch_board_red])


def train(model, criterion, batch_board_red_score, optimizer):
    feed = data.create_train_feed(batch_board_red_score)
    score = model(feed['square'], feed['length'])
    loss = criterion(score, feed['target'])
    optimizer.zero_grad()
    loss.backward()
    nn.utils.clip_grad_norm_(model.parameters(), 5.0)
    optimizer.step()
    return loss.tolist()


def tdleaf(model, initial_board, red, lamb=0.7, depth=12):
    criterion = models.build_loss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1E-3)
    series = []
    while True:
        boards = next_boards(initial_board, red)
        gameover_board, gameover_score = contains_gameover(boards, red)
        if gameover_board is not None:
            series.append((gameover_board, not red, gameover_score))
            break
        scores = batch_evaluate(model, boards, not red)
        board, score = sample(boards, scores.tolist(), red)
        red = not red
        series.append((board, red, score))

    batch_board_red_score = [(board, red, gameover_score)
                             for board, red, _ in series]
    loss = trainer.train(model, criterion, batch_board_red_score, optimizer)
    return loss, len(batch_board_red_score)


def run_train():
    model = models.build_model()
    queue = board_queue.BoardQueue()
    iteration = 0
    while True:
        iteration += 1
        board, red = queue.dequeue()
        loss, size = tdleaf(model, board, red)
        print(f'iteration {iteration}: loss: {loss / size:>.4F}')


def contains_gameover(boards, red):
    for board in boards:
        score = rule.basic_score(board)
        if abs(score) > rule.GAMEOVER_THRESHOLD:
            return board, 1 if score > 0 else 0
    return None, None


def next_boards(board, red):
    moves = rule.next_steps(board, red)
    return [rule.next_board(board, move) for move in moves]


def evaluate(sess, model, board, red):
    return batch_evaluate(model, [board], red)


def batch_evaluate(model, boards, red):
    batch_board_red = [(board, red) for board in boards]
    scores = trainer.predict(model, batch_board_red).sigmoid()
    #scores = [random.randint(-1000, 1000) for _ in boards]
    return scores.tolist()


def sample(boards, scores, red):
    #combined = list(zip(scores, boards))
    if not red:
        weights = 1 - scores
    else:
        weights = scores
    board, score = np.random.choice(zip(boards, scores), 1, weights)[0]
    return board, score


def pv_position(initial_board, red):
    return False


if __name__ == '__main__':
    run_train()
