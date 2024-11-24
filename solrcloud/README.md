# solrcloud

## check result

```bash
λ python src/check.py 100000
A
  100: 49.8 %, 50.0 %
  101: 30.09 %, 30.0 %
  102: 20.12 %, 20.0 %
B
  200: 69.79 %, 70.0 %
  201: 30.21 %, 30.0 %
C
  300: 39.8 %, 40.0 %
  301: 19.95 %, 20.0 %
  302: 20.14 %, 20.0 %
  303: 20.12 %, 20.0 %

MAPE: 0.48 %
MAE: 0.0015
MSE: 0.0
RMSE: 0.0016
MSLE: 0.0
R2: 0.9999
```


```bash
$ curl -s 'http://localhost:8983/solr/poc/select?q=*:*&rows=0'
{
  "responseHeader":{
    "zkConnected":true,
    "status":0,
    "QTime":0,
    "params":{
      "q":"*:*",
      "rows":"0"}},
  "response":{"numFound":5466,"start":0,"numFoundExact":true,"docs":[]
  }}
$ python src/check.py 40000
...
MAPE: 1.4000000000000001 %
MAE: 0.0017
MSE: 0.0
RMSE: 0.0021
MSLE: 0.0
R2: 0.9998
```

## data generation

```bash
$ ./bin/insert.sh <(python src/gen.py 1000)
```

約 5400 件のデータで、10万回リクエストして、MAPE が 0.73 % になった。 

```bash
$ python src/check.py 100000 16
MAPE: 0.73 %
R2: 1.0
```