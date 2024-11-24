#!/usr/bin/env python

import json
import sys
import fire
import numpy as np

class Group:
    def __init__(self, name: str, base: int, rng: np.random.Generator):
        self.__name = name

        probabilities = rng.random(rng.integers(2, 10))
        probabilities /= np.sum(probabilities)
        cdf = np.cumsum(probabilities)
        self.__members = [{"id": base + i, "group_key": name, "probability": p, "cumulative_probability": c} for i, (p, c) in enumerate(zip(probabilities, cdf))]

    def list(self):
        return self.__members


def main(n: int = 100, seed: int = 42):
    rng = np.random.default_rng(seed)
    groups = [Group(f"group-{i}", i * 100, rng) for i in range(1, n+1)]

    for group in groups:
        for record in group.list():
            json.dump(record, sys.stdout)
            print()


if __name__ == '__main__':
     fire.Fire(main)