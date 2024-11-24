#!/usr/bin/env python

import queue
from queue import Queue
import threading

import fire
import requests
from sklearn.metrics import mean_absolute_percentage_error, r2_score
import numpy as np

class SolrClient:
    def __init__(self, collection: str):
        self.__collection = collection
        self.__max_rows = 10000

    def search(self, probability: float):
        url = f"http://localhost:8983/solr/{self.__collection}/select"
        # sort = f"if(lt({probability},cumulative_probability),cumulative_probability,sum(1,cumulative_probability)) asc"
        sort=f"if(gt(cumulative_probability,{probability}),1,0) desc,cumulative_probability asc"
        payload = {
            'q': '*:*',
            'fq': '{!collapse field=group_key sort="' + sort + '"}',
            'rows': self.__max_rows,
        }
        res = requests.get(url, params=payload).json()

        results = {}
        for i in res['response']['docs']:
            key = i['group_key']
            results[key] = i['id']
        # {group_key: id}
        # {"A": "1", "B": "2"}
        return results

    def all(self):
        url = f"http://localhost:8983/solr/{self.__collection}/select"
        payload = {
            'q': '*:*',
            'fl': 'id,group_key,probability',
            'rows': self.__max_rows,
        }
        res = requests.get(url, params=payload).json()

        results = {}
        for i in res['response']['docs']:
            key = i['group_key']
            if key not in results:
                results[key] = {}
            results[key][i['id']] = i['probability']
        # {group_key: {id: probability}}
        # {"A": {"1": 0.3, "2": 0.6, "3": 0.1}, "B": {"1": 0.4, "2": 0.6}}
        return results


def worker(solr, input_queue, output_queue):
    while not input_queue.empty():
        n = input_queue.get()
        output_queue.put(solr.search(n))

def consumer(solr, n, output_queue):
    results = {}
    while True:
        try:
            res = output_queue.get(timeout=1)
            if res is None:
                break
            for key in res:
                if key not in results:
                    results[key] = {}
                if res[key] not in results[key]:
                    results[key][res[key]] = 0
                results[key][res[key]] += 1
        except queue.Empty:
            continue

    got = {}
    for key, value in results.items():
        got[key] = {}
        for i, j in value.items():
            got[key][i] = j / n

    expected, got = merge_nested_dicts_with_default(solr.all(), got)
    for key, value in sorted(expected.items(), key=lambda x: x[0], reverse=False):
        print(f"{key}")
        for i, j in sorted(value.items(), key=lambda x: x[0], reverse=False):
            print(f"\t{i}:\t{round(got[key][i] * 100, 2)} %,\t{round(j * 100, 2)} %")
    print()

    y_true = convert2y(expected)
    y_pred = convert2y(got)
    print(f"MAPE: {error(mean_absolute_percentage_error, y_true, y_pred) * 100} %")
    print(f"R2: {error(r2_score, y_true, y_pred)}")


def main(n: int = 1000, max_threads: int = 4):
    solr = SolrClient('poc')
    input_queue = Queue()
    output_queue = Queue()
    rng = np.random.default_rng()

    for i in range(n):
        # input_queue.put(round(i/n,4))
        input_queue.put(round(rng.uniform(0.0,1.0),4))

    threads = []
    for i in range(max_threads):
        thread = threading.Thread(target=worker, args=(solr, input_queue, output_queue))
        thread.start()
        threads.append(thread)
    consumer_thread = threading.Thread(target=consumer, args=(solr, n, output_queue))
    consumer_thread.start()

    for thread in threads:
        thread.join()

    output_queue.put(None)
    consumer_thread.join()


def merge_nested_dicts_with_default(dict1, dict2, default_value=0):
    # 全体のキーの和集合を取得
    all_keys = set(dict1.keys()).union(set(dict2.keys()))

    merged_dict1 = {}
    merged_dict2 = {}

    for key in all_keys:
        # ネストされた辞書を取得（存在しない場合は空の辞書とする）
        nested_dict1 = dict1.get(key, {})
        nested_dict2 = dict2.get(key, {})

        # ネストされた辞書のキーの和集合を取得
        nested_keys = set(nested_dict1.keys()).union(set(nested_dict2.keys()))

        # 各ネストされた辞書にデフォルト値を補完
        merged_dict1[key] = {k: nested_dict1.get(k, default_value) for k in nested_keys}
        merged_dict2[key] = {k: nested_dict2.get(k, default_value) for k in nested_keys}

    return merged_dict1, merged_dict2

def error(fn, y_true, y_pred):
    return round(fn(y_true, y_pred), 4)

def convert2y(data: dict):
    results = []
    for _, value in sorted(data.items(), key=lambda x: x[0], reverse=False):
        for _i, j in sorted(value.items(), key=lambda x: x[0], reverse=False):
            results.append(j)
    return results


if __name__ == '__main__':
    fire.Fire(main)
