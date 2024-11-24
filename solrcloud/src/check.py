#!/usr/bin/env python

import random
import requests
from sklearn.metrics import mean_absolute_error,mean_squared_error,mean_squared_log_error,r2_score,root_mean_squared_error,mean_absolute_percentage_error

import threading
from queue import Queue

def req(n: str):
    url = 'http://localhost:8983/solr/poc/select'
    sort=f"if(lt({n},cumulative_probability),cumulative_probability,sum(1,cumulative_probability)) asc"
    # sort=f"if(gt(cumulative_probability,{n}),1,0) desc,cumulative_probability asc"
    payload = {
        'q': '*:*',
        'fq': '{!collapse field=group_key sort="' + sort + '"}',
        'rows': 1000,
    }
    res = requests.get(url, params=payload)
    json = res.json()
    return json['response']['docs']

def get_expected():
    url = 'http://localhost:8983/solr/poc/select'
    payload = {
        'q': '*:*',
        'fl': 'id,group_key,probability',
        'rows': 1000,
    }
    res = requests.get(url, params=payload)
    json = res.json()

    results = {}
    for i in json['response']['docs']:
        key = i['group_key']
        if key not in results:
            results[key] = {}
        results[key][i['id']] = i['probability']
    return results

def worker(input_queue, output_queue):
    while not input_queue.empty():
        n = input_queue.get()
        output_queue.put(req(str(n)))

def main():
    n = 20000
    max_threads = 20

    input_queue = Queue()
    output_queue = Queue()

    # insert random numbers to input_queue
    for i in range(n):
        input_queue.put(round(random.uniform(0.0,1.0),4))

    # start threads
    threads = []
    for i in range(max_threads):
        thread = threading.Thread(target=worker, args=(input_queue, output_queue))
        thread.start()
        threads.append(thread)

    # wait for all threads to finish
    for thread in threads:
        thread.join()

    responses = []
    while not output_queue.empty():
        responses.append(output_queue.get())

    results = {}
    for rows in responses:
        for j in rows:
            i = j['id']
            key = j['group_key']
            if key not in results:
                results[key] = {}
            if i not in results[key]:
                results[key][i] = 0
            results[key][i] += 1

    got = {}
    expected = get_expected()
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
    main()
