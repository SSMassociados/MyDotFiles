#! /bin/bash
u=$(pgrep polybar | tail -n 1)
kill $u
