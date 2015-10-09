# moebius
Moebius is free, light 0mq-based Dealer-Router generic python server.

Moebius is inspired by Tornado web-server, which is high performance REST and WebSocket server. Like Tornado, Moebius employs the approach with python generators to create light and single-threaded server.

#0mq as transport

Moebius uses well known and robust ZeroMQ library to implement transport. It uses DEALER-ROUTER 0mq pattern two implement two-way communication without specific limitations. Using DEALER-ROUTER pattern it's possible to implement either synchronous request-response communication or arbitrary request-response* (0 or more responses) communication.
