# moebius
Moebius is free, light 0mq-based Dealer-Router generic python server.

Moebius is inspired by Tornado web-server, which is high performance REST and WebSocket server. Like Tornado, Moebius employs the approach with python generators to create light and single-threaded server.

#0mq as transport

Moebius uses well known and robust ZeroMQ library to implement transport. It uses DEALER-ROUTER 0mq pattern to implement two-way communication without specific limitations. DEALER-ROUTER pattern allows to implement three types of communication:
 
* 1 request - 1 response 
* 1 request - N responses
* 1 request - 0 responses
