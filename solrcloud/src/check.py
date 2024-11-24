#!/usr/bin/env python

import random
import fire
import requests
from sklearn.metrics import mean_absolute_error,mean_squared_error,mean_squared_log_error,r2_score,root_mean_squared_error,mean_absolute_percentage_error
import threading
from queue import Queue
import numpy as np

class SolrClient:
    def __init__(self, collection: str):
        self.__collection = collection
        self.__max_rows = 1000

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

def main(n: int = 1000, max_threads: int = 4):
    solr = SolrClient('poc')
    input_queue = Queue()
    output_queue = Queue()
    rng = np.random.default_rng()

    # insert random numbers to input_queue
    for i in range(n):
        # input_queue.put(round(i/n,4))
        input_queue.put(round(rng.uniform(0.0,1.0),4))

    # start threads
    threads = []
    for i in range(max_threads):
        thread = threading.Thread(target=worker, args=(solr, input_queue, output_queue))
        thread.start()
        threads.append(thread)

    # wait for all threads to finish
    for thread in threads:
        thread.join()

    results = {}
    while not output_queue.empty():
        res = output_queue.get()
        for key in res:
            if key not in results:
                results[key] = {}
            if res[key] not in results[key]:
                results[key][res[key]] = 0
            results[key][res[key]] += 1
    got = {}
    expected = solr.all()
    for key, value in results.items():
        print(f"{key}")
        got[key] = {}
        for i, j in sorted(value.items(), key=lambda x: x[0], reverse=False):
            got[key][i] = j/n
            print(f"  {i}: {round(100*j/n, 2)} %, {round(expected[key][i]*100, 2)} %")
    print()


    y_true = convert2y(expected)
    y_pred = convert2y(got)
    print(f"MAPE: {error(mean_absolute_percentage_error,y_true, y_pred) * 100} %")
    print(f"MAE: {error(mean_absolute_error,y_true, y_pred)}")
    print(f"MSE: {error(mean_squared_error,y_true, y_pred)}")
    print(f"RMSE: {error(root_mean_squared_error,y_true, y_pred)}")
    print(f"MSLE: {error(mean_squared_log_error,y_true, y_pred)}")
    print(f"R2: {error(r2_score,y_true, y_pred)}")

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
