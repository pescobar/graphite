

# graphite

Some scripts to insert performance data to graphite and then plot with grafana.

## sge-qstat-parser.py

Parse the xml output of qstat and qhost to generate metrics in graphite format. 

If you are inserting these metrics to influxdb using the graphite input plugin you will need this in your influxdb config file (bc2 is the content of variable "cluster_name" in the script) :

```
[[graphite]]
  templates = [
     "sge.bc2.total.* sge.cluster.total.measurement",
     "sge.bc2.users.* sge.cluster.users.username.measurement",
     "sge.bc2.queue.* sge.cluster.q.queue.measurement",
     "sge.bc2.project.* sge.cluster.p.project.measurement",
  ]
```

To debug the script comment out the line "print message" at the end of main() function.


## gpfs-stats.py

AN UPDATED VERSION OF THIS SCRIPT WHICH WRITES DIRECTLY TO INFLUXDB USING THE LINE PROTOCOL IS AVAILABLE HERE: https://github.com/pescobar/influxdb

I execute this script with cron every minute in each of my gpfs clients. If you prefer to run it in daemon mode, using the python daemon module to daemonize it should be straightforward.

gpfs-stats.py has some room for improvement in performance terms.

You can avoid calling get_gpfs_global_stats() and then generate the global gpfs stats by summing in python all the values reported by get_gpfs_stats_by_fs(). I tried this approach and the wallclock time went from ~110ms to ~75ms but I decided to use the current approach because I prefer to rely on the values that mmpmon reports without doing further processing and also I think the code is easier to read and modify/adapt like it is written now.

Another approach is to avoid calling get_gpfs_global_stats(), insert to graphite only the information fetched from get_gpfs_stats_by_fs() and then do further processing in grafana to calculate the global gpfs stats. 

If you have only 1 gpfs filesytem or you are only interested in the global performance data you can skip the call to get_gpfs_stats_by_fs()

To debug I suggest commenting lines 59 "send_to_graphite(message)" and line 63 "reset_gpfs_counters()" and comment out line 58 "print message" so you can see in STDOUT what would be sent to graphite.

Up to you how you prefer to do it, the code is quite easy to modify :)


