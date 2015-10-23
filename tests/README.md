# Getting Started with Moebius

## Programming style

First one should know about Moebius is that it's single threaded, so if one handler works, then other handlers stop which in turn means that requests are delayed. So program design should avoid long-running pieces of code which can not be interrupted. 

For example, if You would like to sort very big array of data, you could find that It will take a lot of time to complete it all. So If You just will try to run it in direct way You will find that concurrency stops to work because other clients unable to send queries and server unable to process requests.

You could overcome this limitations using next techniques (for sort):

1. Split array on some parts and run sort for every part, do return management to server in order it could run another handlers and when server will return back management to this handler, continue to do sort of next part of array. Finally, You just merge sorted parts together.
2. Complete offload to external service and just wait until it completes sorting.

Both these methods can be implemented in Moebius effectively using python *generators*. Next in this tutorial I'll explain how to do it.

*NB:* To effectively use Moebius you should understand python [*generators*](https://wiki.python.org/moin/Generators) and able to write your own generators.

Since Moebius is single-threaded this means that overall request bandwidth/second = 1/req-time, where req-time is average time request takes to succeed.
