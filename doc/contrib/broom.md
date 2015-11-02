# Broom: Moebius multiprocessed offloading engine

## Purpose

Broom allows to switch from single-threaded processing model to worker-like processing model. It could give You two benefits:

1. Utilize all CPU cores on heavy services.
2. Implement slow query processing (for example slow database response) without additional asynchronous code.

If you just need to balance traffic among several Moebius then it's better to use regular HA-Proxy rather than Broom, because you could utilize less system resources and achieve better performance, but If you need "pure" solution, use Broom.

## Status

It's alfa.

## Usage

First, ensure you have single-threaded Moebius application is designed well and works properly, so it's tested well and passes external specification. It's quite complicated to debug code which runs on multiple cores so better to test all using standard moebius programming model. 


