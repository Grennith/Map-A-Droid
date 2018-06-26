## Usage
### Requirement

`TODO: There is one requirement missing... gotta check which one it was`
Linux ( Debian / Ubuntu ):
```
apt-get install python-matplotlib
pip install -r requirements.txt
```

Linux ( Fedora / Redhat ):
```
yum install python-matplotlib
pip install -r requirements.txt
```

Mac OSX:
```
pip install matplotlib
pip install -r requirements.txt
```


### Execute
To simply get a route as `[{latitude: "xxx", longitude: "xxx"}, {latitude: "xxx", longitude: "xxx"}, etc etc]`
simply `from calculate_route import *` and call `getJsonRoute(filepath)` where filepath is the full path to your .csv.
A .csv simply needs to have all the gyms `lat,lon` formatted. One gym per line.
E.g.
```
50.525045,8.647734
50.525621,8.665441
50.526914,8.677226
50.527042,8.6762
```


### Original Repo
https://github.com/tnlin/PokemonGo-TSP

## Original Reference
[1] [Pokemon Go Traveling Salesman Problem](http://www.math.uwaterloo.ca/tsp/poke/index.html) - 國外的Pokemon Go TSP

[2] [Travelling salesman problem](https://en.wikipedia.org/wiki/Travelling_salesman_problem) - TSP背景知識

[3] [Simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing) - 模擬退火背景知識

[4] [模拟退火算法求解旅行商问题](http://blog.csdn.net/lalor/article/details/7688329) - 詳盡的模擬退火解說 ＋ Java實現，提到了三種產生新狀態的方式

[5] [Queen of College Tours](http://www.math.uwaterloo.ca/tsp/college/index.html) - 從Geometric TSP 到 Road TSP

[6] [PokemonGo-Map](https://github.com/PokemonGoMap/PokemonGo-Map) - 地圖掃描工具，開啟後放置一段時間，再把`pogom.db`拿出來，即可取得道館/補給站座標

[7] [A Comparison of Cooling Schedules for Simulated Annealing](http://what-when-how.com/artificial-intelligence/a-comparison-of-cooling-schedules-for-simulated-annealing-artificial-intelligence/) - 不同冷卻計畫的比較
