"""Illustrative weak AI-generated test — NOT collected by pytest."""


def test_model_works():
    # Looks green, proves nothing about the pipeline.
    assert True


def test_random_dice_looks_ok():
    import numpy as np

    pred = np.random.randint(0, 6, size=(32, 32, 32))
    gt = np.random.randint(0, 6, size=(32, 32, 32))
    # "Dice" computed on random noise — no link to the real case.
    overlap = (pred == gt).mean()
    assert overlap >= 0.0
