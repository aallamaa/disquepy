=========================
Disque Python Client
=========================

Minimalist Disque python client, client to https://github.com/antirez/disque Disque, an in-memory, distributed job queue


Install
=======

sudo python setup.py install

or 

sudo easy_install disque

or

sudo pip install disque



Minimalist disque client
========================


>>> import disque
>>> r=disque.Disque()
>>> r.addjob("queue","body",0)
'DI9af92fc01d473dfdf3781ca248262612b73cf55905a0SQ'
>>> r.getjob("from","queue")
[['queue', 'DI9af92fc01d473dfdf3781ca248262612b73cf55905a0SQ', 'body']]
>>> r.hello()
[1, '9af92fc0714ced7ad38bbe9658ff2a9594ee847d', ['9af92fc0714ced7ad38bbe9658ff2a9594ee847d', '', '7711', '1']]
>>> print r.info()
# Server
disque_version:0.0.1
disque_git_sha1:d01f47d4
disque_git_dirty:0
disque_build_id:681e3a948501c121
os:Linux 3.13.0-49-generic x86_64
arch_bits:64
multiplexing_api:epoll
gcc_version:4.8.2
process_id:22042
run_id:44337dfc70530b893f31140152610ad917584b55
tcp_port:7711
uptime_in_seconds:1576
uptime_in_days:0
hz:10
config_file:
# Clients
connected_clients:1
client_longest_output_list:0
client_biggest_input_buf:0
blocked_clients:0
# Memory
used_memory:457072
used_memory_human:446.36K
used_memory_rss:1851392
used_memory_peak:457072
used_memory_peak_human:446.36K
mem_fragmentation_ratio:4.05
mem_allocator:jemalloc-3.6.0
# Jobs
registered_jobs:3
# Queues
registered_queues:1
# Persistence
loading:0
aof_enabled:0
aof_rewrite_in_progress:0
aof_rewrite_scheduled:0
aof_last_rewrite_time_sec:-1
aof_current_rewrite_time_sec:-1
aof_last_bgrewrite_status:ok
aof_last_write_status:ok
# Stats
total_connections_received:4
total_commands_processed:12
instantaneous_ops_per_sec:0
total_net_input_bytes:367
total_net_output_bytes:4756
instantaneous_input_kbps:0.00
instantaneous_output_kbps:0.00
rejected_connections:0
latest_fork_usec:0
# CPU
used_cpu_sys:6.89
used_cpu_user:5.02
used_cpu_sys_children:0.00
used_cpu_user_children:0.00

