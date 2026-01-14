# Access Backend/New Products Coding Exercise

This exercise will have you implementing an api that allows the user to fetch logs from a virtual  
camera, without the camera needing to open any ports.     

It is similar to our actual mechanism for communicating with cameras, though of course greatly  
simplified.  

The virtual camera (`camera/camera.py`) will not have any open ports for security reasons. As a  
result, it only makes requests out to the API server.  The camera has actually already been  
almost completely written.  You might need to make some small modifications to it, but right now,   
if you run the container, it already generates logs, polls the API for commands, and responds to  
commands to send logs.  However right now the command returned by the API's `/poll_for_command`  
endpoint does not contain `"startTimestamp"` or `"endTimestamp"` keys, so it always includes all  
logs in the `/send_logs` payload.  (The time-based logs filtering has already been implemented   
also.)  

The API server (`api/api.py`) is a web server that the camera and a web client can both access using  
standard REST APIs.  This is what you'll be working on for the most part in this exercise.  

We use docker to orchestrate the system.  You can try running the server and camera:
   
```
docker compose build
docker compose up
```

The API server and camera will start.  Right now the camera works but the API does not do  
anything meaningful.  You will be adding that functionality.  


## Required Functionality
The camera doesn't actually do much. For the purposes of this exercise, the only thing it does is  
generate an event log, which is a list of events. Each event has a timestamp and description. The  
log is stored locally “on camera”. Every 10 seconds, the camera inserts a new event into the log.   

The camera has no open ports or server, so to communicate with the API server, it will make an  
outgoing HTTP request (`GET /poll_for_command`) to the API server. The API server will keep the  
request open until it wants data from the camera. In this case, it will want to fetch the event  
log.  

When a user requests the event log from the API server by calling `GET /logs`, the server will  
respond to the open `/poll_for_command` request with a "command" for the camera to execute (for  
this exercise the only command is to send logs), including what `"startTimestamp"` and  
`"endTimestamp"` within which it wants logs (these are optional query parameters on the `GET /logs`  
request).  The camera will then send the log to the API server in another HTTP request   
(`POST /send_logs`).  The value of the `"logs"` field in the payload of this request should be  
returned as the `GET /logs` response.  
  
Every minute, the camera times out the outgoing request and opens a new one to ensure the API  
server always has a relatively fresh connection and we avoid any timeouts (likely in production  
we’d have load balancers that terminate connections if they stay open too long).  If you’re  
confused, try googling for “long polling”!  

Hint: be careful about edge cases, boundaries, and race conditions!  

## The task
You will be implementing the API endpoints in `api/api.py`, and maybe making some modifications  
to `camera/camera.py`, to implement the required functionality.  

### `api/api.py`
This file implements the API using Flask.  It has 3 endpoints that have been stubbed out, all of which you need to implement:  

* `/logs (GET)`: Fetch logs from camera (called by user) - takes optional url parameters  
    `startTimestamp` and `endTimestamp` (float)
* `/poll_for_command (GET)`: Get command from API via long-polling (called by camera)
* `/send_logs (POST)`: Send logs from camera to api server (called by camera)

### `camera/camera.py`
This file implements and runs a simulated camera.  It's already implemented but you might want to  
modify it a bit.

## Running the code

```
docker compose build
docker compose up
```

The code directories are mapped as volumes, so you only need to build once unless  
you add packages to the Pipfile (not necessary to solve the problem, but you can if you  
want).  

### Running the code without Docker

Install the required packages first:
```
pip install -r requirements.txt
```

API:
```
MODE=api ./run.sh
```

Camera:
```
MODE=camera API_BASE_URL=http://localhost:8080 ./run.sh
```



## Querying the API for logs
```
curl http://localhost:8080/logs
```

Once a single curl is working, use the included `curl_parallel.sh` to curl multiple times  
simultaneously, to test correctness in the presence of multiple simultaneous callers.  In the  
example below, we make 10 simultaneous calls:  

```
curl_parallel.sh 10 http://localhost:8080/logs
```
