### TAB_B05 — Squared-error tail attribution

Tail = the ceil(fraction × n) largest squared errors of that model; share = tail SSE / model total SSE.

| run | channel | unit | model | tail_fraction | tail_count | n | total_sse | tail_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24 | MFC-3 | ln/min | persistence | 0.001 | 5 | 4940 | 234 | 0.504274 |
| 24 | MFC-3 | ln/min | persistence | 0.01 | 50 | 4940 | 234 | 1 |
| 24 | MFC-3 | ln/min | persistence | 0.05 | 247 | 4940 | 234 | 1 |
| 24 | MFC-3 | ln/min | ridge | 0.001 | 5 | 4940 | 234.249 | 0.502987 |
| 24 | MFC-3 | ln/min | ridge | 0.01 | 50 | 4940 | 234.249 | 0.994047 |
| 24 | MFC-3 | ln/min | ridge | 0.05 | 247 | 4940 | 234.249 | 0.994764 |
| 24 | P-2 | barg | persistence | 0.001 | 5 | 4940 | 719 | 0.119611 |
| 24 | P-2 | barg | persistence | 0.01 | 50 | 4940 | 719 | 0.232267 |
| 24 | P-2 | barg | persistence | 0.05 | 247 | 4940 | 719 | 0.506259 |
| 24 | P-2 | barg | ridge | 0.001 | 5 | 4940 | 716.097 | 0.119485 |
| 24 | P-2 | barg | ridge | 0.01 | 50 | 4940 | 716.097 | 0.234056 |
| 24 | P-2 | barg | ridge | 0.05 | 247 | 4940 | 716.097 | 0.523535 |
| 28 | MFC-3 | ln/min | persistence | 0.001 | 6 | 5002 | 435.884 | 0.420339 |
| 28 | MFC-3 | ln/min | persistence | 0.01 | 51 | 5002 | 435.884 | 0.910906 |
| 28 | MFC-3 | ln/min | persistence | 0.05 | 251 | 5002 | 435.884 | 0.999892 |
| 28 | MFC-3 | ln/min | ridge | 0.001 | 6 | 5002 | 434.594 | 0.418935 |
| 28 | MFC-3 | ln/min | ridge | 0.01 | 51 | 5002 | 434.594 | 0.908963 |
| 28 | MFC-3 | ln/min | ridge | 0.05 | 251 | 5002 | 434.594 | 0.997961 |
| 28 | P-2 | barg | persistence | 0.001 | 6 | 5002 | 503.08 | 0.116323 |
| 28 | P-2 | barg | persistence | 0.01 | 51 | 5002 | 503.08 | 0.244255 |
| 28 | P-2 | barg | persistence | 0.05 | 251 | 5002 | 503.08 | 0.59744 |
| 28 | P-2 | barg | ridge | 0.001 | 6 | 5002 | 500.821 | 0.116287 |
| 28 | P-2 | barg | ridge | 0.01 | 51 | 5002 | 500.821 | 0.240725 |
| 28 | P-2 | barg | ridge | 0.05 | 251 | 5002 | 500.821 | 0.587863 |
| 29 | MFC-3 | ln/min | persistence | 0.001 | 6 | 5943 | 728.399 | 0.657313 |
| 29 | MFC-3 | ln/min | persistence | 0.01 | 60 | 5943 | 728.399 | 0.931078 |
| 29 | MFC-3 | ln/min | persistence | 0.05 | 298 | 5943 | 728.399 | 0.999437 |
| 29 | MFC-3 | ln/min | ridge | 0.001 | 6 | 5943 | 726.811 | 0.656783 |
| 29 | MFC-3 | ln/min | ridge | 0.01 | 60 | 5943 | 726.811 | 0.930058 |
| 29 | MFC-3 | ln/min | ridge | 0.05 | 298 | 5943 | 726.811 | 0.997328 |
| 29 | P-2 | barg | persistence | 0.001 | 6 | 5943 | 1173.48 | 0.211712 |
| 29 | P-2 | barg | persistence | 0.01 | 60 | 5943 | 1173.48 | 0.36367 |
| 29 | P-2 | barg | persistence | 0.05 | 298 | 5943 | 1173.48 | 0.622729 |
| 29 | P-2 | barg | ridge | 0.001 | 6 | 5943 | 1149.69 | 0.215515 |
| 29 | P-2 | barg | ridge | 0.01 | 60 | 5943 | 1149.69 | 0.363838 |
| 29 | P-2 | barg | ridge | 0.05 | 298 | 5943 | 1149.69 | 0.621975 |
| all 3 runs | P-2 | barg | persistence | 0.001 | 16 | 15885 | 2395.56 | 0.166625 |
| all 3 runs | P-2 | barg | persistence | 0.01 | 159 | 15885 | 2395.56 | 0.306584 |
| all 3 runs | P-2 | barg | persistence | 0.05 | 795 | 15885 | 2395.56 | 0.591361 |
| all 3 runs | P-2 | barg | ridge | 0.001 | 16 | 15885 | 2366.61 | 0.167957 |
| all 3 runs | P-2 | barg | ridge | 0.01 | 159 | 15885 | 2366.61 | 0.304183 |
| all 3 runs | P-2 | barg | ridge | 0.05 | 795 | 15885 | 2366.61 | 0.592599 |
| all 3 runs | MFC-3 | ln/min | persistence | 0.001 | 16 | 15885 | 1398.28 | 0.550409 |
| all 3 runs | MFC-3 | ln/min | persistence | 0.01 | 159 | 15885 | 1398.28 | 0.936451 |
| all 3 runs | MFC-3 | ln/min | persistence | 0.05 | 795 | 15885 | 1398.28 | 0.999939 |
| all 3 runs | MFC-3 | ln/min | ridge | 0.001 | 16 | 15885 | 1395.65 | 0.549106 |
| all 3 runs | MFC-3 | ln/min | ridge | 0.01 | 159 | 15885 | 1395.65 | 0.934446 |
| all 3 runs | MFC-3 | ln/min | ridge | 0.05 | 795 | 15885 | 1395.65 | 0.997523 |
