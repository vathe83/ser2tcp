# Stress Tests

## Preparation 

### Emulate a serial device 

We can emulate a serial device by creating two virtual serial ports linked
with a null modem cable, attaching one end to tested application and the other
end to (usually) serial terminal.

Steps:

1. Create two virtual serial ports, in one terminal execute:
    ``` bash 
    socat -d -d PTY PTY
    # or better 
    socat -d -d PTY,rawer,echo=0,link=/tmp/ttyV0,b115200 \
                PTY,rawer,echo=0,link=/tmp/ttyV1,b115200
    ```
   > **Socat options:**
   > - echo=\<bool\>: Enables or disables local echo (example).
   > - rawer:  Makes terminal rawer than raw option. This option implicitly turns off echo. (example).
   > - link=\<filename\>: Generates a symbolic link that points to the actual pseudo terminal (pty). This
   >   might help to solve the problem that ptys are generated with more or less unpre‐
   >   dictable names, making it difficult to directly access the socat generated pty
   >   automatically. With this option, the user can specify a "fix" point in the file
   >   hierarchy that helps him to access the actual pty (example).  Beginning with socat
   >   version 1.4.3, the symbolic link is removed when the address is closed (but see
   >   option unlink-close).
   > - b19200: Sets the serial line speed to 19200 baud. Some other rates are possible; use some‐
   >   thing like socat -hh |grep ’ b[1-9]’ to find all speeds supported by your implementation.
   >   Note: On some operating systems, these options may not be available. Use ispeed or ospeed instead.

2. Now, the emulated serial device has a symlink `/tmp/ttyV1` and we can feed it with data from the other virtual serial port `/tmp/ttyV0`. Thus, when we run the `ser2tcp` we need to change the serial device to `/tmp/ttyV1`.


## Tests

### <a name="add_remove_consumers"></a>Add/Remove consumers

With this test, we want to make sure that there is non dependency between the consumers, meaning that if we have 3 different consumers and we disconnect one, the other 2 consumers will independently consuming the data.

Steps:
1. Open a terminal and create virtual serial ports:
    ``` bash 
    socat -d -d PTY,rawer,echo=0,link=/tmp/ttyV0,b115200 \
                PTY,rawer,echo=0,link=/tmp/ttyV1,b115200
    ```
2. Edit the `ser2tcp.conf` to set the serial device to `/dev/ttyV1` and create
   3 consumers in localhost and ports `10001`, `10002` and `10003`:
    ``` json
    [
        {
            "serial": {
                "port": "/dev/ttyV1",
                "baudrate": 115200,
                "parity": "NONE",
                "stopbits": "ONE"
            },
            "servers": [
                {
                    "address": "0.0.0.0",
                    "port": 10001,
                    "protocol": "TCP"
                },
                {
                    "address": "0.0.0.0",
                    "port": 10002,
                    "protocol": "TCP"
                },
                {
                    "address": "0.0.0.0",
                    "port": 10003,
                    "protocol": "TCP"
                }
            ]
        }
    ]
    ```
3. Open a terminal and run `ser2tcp`. Navigate to the `ser2tcp` repo and start `ser2tcp`:
    ``` bash
    target1@host:~> cd repos/ser2tcp/
    target1@host:~/repos/ser2tcp> python3 run.py -c ./ser2tcp.conf
    ```
4. Open a terminal a feed the virtual serial port `/tmp/ttyV0` with data (The contents of the script `datagenerate` are in [Appendix](#datagenerate)):
    ``` bash
    datagenerate | /usr/bin/socat -u - /tmp/ttyV0,b115200,rawer
    ```
5. Open 3 different terminals and start 3 consumers:
    ``` bash
    # Consumer 1
    socat -,rawer TCP:localhost:10001
    # Consumer 2
    socat -,rawer TCP:localhost:10002
    # Consumer 3
    socat -,rawer TCP:localhost:10003
    ```
6. Disconnect one of the consumers and observe the behavior of others.


### Check data integrity

We will feed the serial device with the same string 10000 times, then 
we will consume the data and write it to a file. Finally, we will validate 
the data of the file.

Steps (The steps 1-3 are the same as in test [Add/Remove consumers](#add_remove_consumers)):
1. Open a terminal and create virtual serial ports:
    ``` bash 
    socat -d -d PTY,rawer,echo=0,link=/tmp/ttyV0,b115200 \
                PTY,rawer,echo=0,link=/tmp/ttyV1,b115200
    ```
2. Edit the `ser2tcp.conf` to set the serial device to `/dev/ttyV1` and create
   3 consumers in localhost and ports `10001`, `10002` and `10003`:
    ``` json
    [
        {
            "serial": {
                "port": "/dev/ttyV1",
                "baudrate": 115200,
                "parity": "NONE",
                "stopbits": "ONE"
            },
            "servers": [
                {
                    "address": "0.0.0.0",
                    "port": 10001,
                    "protocol": "TCP"
                },
                {
                    "address": "0.0.0.0",
                    "port": 10002,
                    "protocol": "TCP"
                },
                {
                    "address": "0.0.0.0",
                    "port": 10003,
                    "protocol": "TCP"
                }
            ]
        }
    ]
    ```
3. Open a terminal and run `ser2tcp`. Navigate to the `ser2tcp` repo and start `ser2tcp`:
    ``` bash
    target1@host:~> cd repos/ser2tcp/
    target1@host:~/repos/ser2tcp> python3 run.py -c ./ser2tcp.conf
    ```
4. Feed a specific line 10000 times to the emulated serial device:
    ``` bash 
    echo  $'T=abcdefghijklmnopqrstuvwxyz\n \
            for n in {0..9999}; do printf "%7d %s\n" \
            $n $T$T$T$T; done\n' \
    | /usr/bin/socat -u - /tmp/ttyV0,b115200,rawer
    ```
5. Connect a consumer to consume the data and pipe it to a file:
    ``` bash
    socat -,rawer TCP:localhost:10001 | tee test.log
    ```
6. Checks:
   1. Check that the file has 10000 lines:
    ``` bash
    wc -l test.log
    ```
   2. Check that all 10000 lines of the file are the same:
    ``` bash
    grep -v abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz logtest.001 | wc -l
    ```

## Appendix
### <a name="datagenerate"></a> datagenerate 
``` bash 
#! /bin/bash

# Experimenting with data streams and socat
#
# These functions generate distinguishable and identifyable lines of output
# or reply to input oin stdin by prepending a distinguishable and identifyable
# string. The third one simply does both in parallel.
#
# Usage in experiments; the middle one is optional (adapt the port in last line)
#     socat TCP-LISTEN:2001,bind=127.0.0.1,fork EXEC:databoth
#     socat -v TCP-LISTEN:2002,bind=127.0.0.1,fork TCP:localhost:2001
#     datagenerate | socat - TCP:localhost:2002

# Get two strings from $0
# - a regular expression for grepping processes of this name ([d]atagenerate)
# - the name without the `data` prefix
read regexp name < <(sed -E 's=.*/(.)(...)(.*)=[\1]\2\3 \3=' <<< $0)

# How many processes of this name are running? This is used to distinguish them
# in their output. (Is this the first, second, third, ...?
# The subshell for `ps ...` creates another process, therefore `- 1`
id=$(($(ps ax | grep "$regexp" | wc -l) - 1))

generate() {
        local PS4='g '
        local n=0
        local name=${1:-$FUNCNAME}
        # When using these scripts in this command
        #   socat TCP-LISTEN:2001,bind=127.0.0.1,fork EXEC:datagenerate
        # it happens to return `broken pipe` errors, despite it seems to work
        # as expected. Currently I don't know how to prevent them properly,
        # therefore I simply use all this stderr redirections.
        # while sleep 1; do
        while true; do
                t="$(
                        cat /dev/urandom 2>/dev/null \
                        | tr -dc '[:alnum:]' 2>/dev/null \
                        | dd bs=1 count=$((RANDOM%32)) 2>/dev/null
                )"
                timestamp=$(date +"%S.%N")
                msg="$(printf "[%s] %s %d %5d %5d %s\n" "$timestamp" $name $id $$ $n "$t")"
                echo "out $msg" 2>/dev/null || exit
                echo "err $msg" >&2
                ((n++))
        done
}

reply() {
        local PS4='r '
        local n=0
        local name=${1:-$FUNCNAME}
        while read t; do
                msg="$(printf "%s %d %5d %5d -- %s\n" $name $id $$ $n "$t")"
                echo "out $msg"
                echo "err $msg" >&2
                ((n++))
        done
}

both() {
        local name=${1:-$FUNCNAME}
        generate ${name}gen &
        reply ${name}rep
}

doso() {
        echo doso >&2
        tee >(socat -u - UNIX-LISTEN:/home/vath273263/test_1.sock,sndbuf=64000,rcvbuf=64000,fork,nonblock) \
        | tee >(socat -u - UNIX-LISTEN:/home/vath273263/test_2.sock,sndbuf=64000,rcvbuf=64000,fork,nonblock) \
        | sed -u 's/^/PREFIX: /' \
        | tee >(socat -u - UNIX-LISTEN:/home/vath273263/test_3.sock,sndbuf=64000,rcvbuf=64000,fork,nonblock) \
        | tee >(socat -u - UNIX-LISTEN:/home/vath273263/test_4.sock,sndbuf=64000,rcvbuf=64000,fork,nonblock) \
        >/dev/null # >&2

# Vassilis, maybe try out less pipes, `tee` can use multiple `files`
        # tee \
        #       >(socat - TCP-LISTEN:2011,bind=127.0.0.1,fork) \
        #       >(socat - TCP-LISTEN:2012,bind=127.0.0.1,fork) \
        # | sed -u 's/^/PREFIX: /' \
        # | tee \
        #       >(socat - TCP-LISTEN:2013,bind=127.0.0.1,fork) \
        #       >(socat - TCP-LISTEN:2014,bind=127.0.0.1,fork) \
        # >/dev/null # >&2
        # | sed 's/^/DDD: /' >&2
}

# trap exit PIPE
$name

exit

# To use the script create these links
ln -vsr /tmp/test123/datagenerate ~/bin/databoth
ln -vsr /tmp/test123/datagenerate ~/bin/datadoso
ln -vsr /tmp/test123/datagenerate ~/bin/datagenerate
ln -vsr /tmp/test123/datagenerate ~/bin/datareply


# Notes from chat with Vassilis

# Terminal 1: Generating data
datagenerate | socat - TCP-LISTEN:2001,bind=127.0.0.1,fork
#
datagenerate | socat - UNIX-LISTEN:/home/vath273263/test.sock,fork

# Terminal 2: Splitting (one of these)
socat TCP:localhost:2001,forever EXEC:datadoso
socat TCP:localhost:2001,forever - | datadoso
#
socat UNIX-CONNECT:/home/vath273263/test.sock,forever EXEC:datadoso

# In the following commands we ran socat with and without `-U` and it seemed to
# behave the same in both cases.
# Terminal 3: consuming data
p=2011
while sleep 0.5; do socat -U - TCP:localhost:$p,forever; done

# Terminal 4: consuming data
p=2012
while sleep 0.5; do socat -U - TCP:localhost:$p,forever; done

# Terminal 5: consuming data
p=2013
while sleep 0.5; do socat -U - TCP:localhost:$p,forever; done

# Terminal 6: consuming data
p=2014
while sleep 0.5; do socat -U - TCP:localhost:$p,forever; done



# About manual pages
man 1 man
man cfmakeraw | less -p '^ *Raw mode'
```

