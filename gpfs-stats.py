#!/usr/bin/env python
# -*- coding: utf-8 -*-

''' 
 get gpfs stats from a compute node and insert them to graphite
 for details in these values check  "Monitoring GPFS I/O performance with the mmpmon command" 
 in the GPFS: Advanced Administration Guide.
'''

import os
import commands
import time
import socket

mmpmon_path = '/usr/lpp/mmfs/bin/mmpmon'

# Carbon
CARBON_SERVER='10.1.0.5'
CARBON_PORT=2003
delay=60

# We use this name when inserting stats to graphite so we can classify the 
# data for the different gpfs environments
gpfs_env = "GPFS33_COMPUTE_NODES"
 
def main():

    global_stats = get_gpfs_global_stats()
    stats_by_fs = get_gpfs_stats_by_fs()
    now = int(time.time())
    lines = []

    #get_gpfs_stats_by_fs()

    hostname = global_stats['gpfs_node_hostname']
    #print global_stats

    for key, value in global_stats.iteritems():
        if key is not 'gpfs_node_hostname':
            values = ("gpfs", gpfs_env, "all_fs", hostname, str(key), str(value), str(now))
            values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
            #print values
            lines.append((values))

    for fs in stats_by_fs:
        for key, value in fs.iteritems():
            if key is not 'gpfs_node_hostname' and key is not 'gpfs_cluster' and key is not 'fs_name':
                #gpfs_cluster = fs['gpfs_cluster']
                #gpfs_cluster = gpfs_cluster.replace(".","_")
                fs_name = fs['fs_name']
                values = ("gpfs", gpfs_env, fs_name, hostname, str(key), str(value), str(now))
                values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
                lines.append((values))
                


    message = '\n'.join(lines) + '\n'
    #print message
    send_to_graphite(message)

    # reset counters provided by mmpmon so next execution of the script we get values
    # just for the latest period
    reset_gpfs_counters()


def get_gpfs_global_stats():
    """ returns a dictionary with the global gpfs statistics (for all filesystems) """

    cmd = 'echo io_s | %s -s -p' % mmpmon_path
    gpfs_stats = commands.getoutput(cmd).split()
    #print gpfs_stats

    gpfs_node_hostname = gpfs_stats[4]

    # _br_ Total number of bytes read, from both disk and cache
    bytes_read = gpfs_stats[12]
    # convert bytest to megabytes and remove decimals
    megabytes_read = int((float(bytes_read)/float(1024))/float(1024))

    # _bw_ Total number of bytes written, to both disk and cache.
    bytes_written = gpfs_stats[14]
    # convert bytes to megabytes and remove decimals
    megabytes_written = int((float(bytes_written)/float(1024))/float(1024))

    # Count of open() call requests serviced by GPFS. The open count also includes creat() call counts.
    open_call_requests = gpfs_stats[16]

    # _cc_ Number of close() call requests serviced by GPFS.
    close_call_requests = gpfs_stats[18]

    #_rdc_ Number of application read requests serviced by GPFS.
    app_read_requests = gpfs_stats[20]

    #_wc_ Number of application write requests serviced by GPFS.
    app_write_requests = gpfs_stats[22]

    # _dir_ Number of readdir() call requests serviced by GPFS.
    readdir_call_requests = gpfs_stats[24]

    # _iu_ Number of inode updates to disk. This includes inodes flushed to disk because of access time updates.
    inodes_updates = gpfs_stats[26]

    return {'gpfs_node_hostname': gpfs_node_hostname,
            'megabytes_read': megabytes_read, 
            'megabytes_written': megabytes_written, 
            'open_call_requests': open_call_requests,
            'close_call_requests': close_call_requests,
            'app_read_requests': app_read_requests,
            'app_write_requests': app_write_requests,
            'readdir_call_requests': readdir_call_requests,
            'inodes_updates': inodes_updates,
            }

def get_gpfs_stats_by_fs():
    """ returns a list of dictionaries.
    Each dictionary contains the stats for one filesytem """

    cmd = 'echo fs_io_s | %s -s -p' % mmpmon_path
    gpfs_stats_by_fs = commands.getoutput(cmd).split('\n')
    stats_by_fs = [] 

    for fs in gpfs_stats_by_fs:
        fs_stats = fs.split()
        #print fs_stats

    
        gpfs_node_hostname = fs_stats[4]
        #print gpfs_node_hostname

        # _cl_ Name of the cluster that owns the file system.
        gpfs_cluster = fs_stats[12]
        #print gpfs_cluster

        # _fs_ The name of the file system for which data are being presented.
        fs_name = fs_stats[14]
        #print fs_name

        # _br_ Total number of bytes read, from both disk and cache.
        bytes_read = fs_stats[18]
        #print bytes_read
        megabytes_read = int((float(bytes_read)/float(1024))/float(1024))
        
        # _bw_ Total number of bytes written, to both disk and cache.
        bytes_written = fs_stats[20]
        #print bytes_written
        megabytes_written = int((float(bytes_written)/float(1024))/float(1024))

        # _oc_ Count of open() call requests serviced by GPFS. This also includes creat() call counts
        open_call_requests = fs_stats[22]
        #print open_call_requests

        # _cc_ Number of close() call requests serviced by GPFS.
        close_call_requests = fs_stats[24]
        #print close_call_requests


        # _rdc_ Number of application read requests serviced by GPFS.
        app_read_requests = fs_stats[26]
        #print app_read_requests

        # _wc_ Number of application write requests serviced by GPFS.
        app_write_requests = fs_stats[28]
        #print app_write_requests

        # _dir_ Number of readdir() call requests serviced by GPFS.
        readdir_call_requests = fs_stats[30]
        #print readdir_call_requests

        # _iu_ Number of inode updates to disk. This includes inodes flushed to disk because of access time updates.
        inodes_updates = fs_stats[32]
        #print inodes_updates

        fs_stats_dict = {'gpfs_node_hostname': gpfs_node_hostname,
                        'gpfs_cluster': gpfs_cluster, 
                        'fs_name': fs_name, 
                        'megabytes_read': megabytes_read, 
                        'megabytes_written': megabytes_written, 
                        'open_call_requests': open_call_requests,
                        'close_call_requests': close_call_requests,
                        'app_read_requests': app_read_requests,
                        'app_write_requests': app_write_requests,
                        'readdir_call_requests': readdir_call_requests,
                        'inodes_updates': inodes_updates,
                        }
        
        stats_by_fs.append(fs_stats_dict)

        #print fs_stats_dict
    return stats_by_fs
 

def reset_gpfs_counters():
    cmd = 'echo reset | %s -s -p &> /dev/null' % mmpmon_path
    os.system(cmd) 

def send_to_graphite(message):
    sock = socket.socket()
    try:
        sock.connect( (CARBON_SERVER,CARBON_PORT) )
    except:
        print "Couldn't connect to %(server)s on port %(port)d, is carbon-agent.py running?" % { 'server':CARBON_SERVER, 'port':CARBON_PORT }
        sys.exit(1)
    #print message
    sock.send(message) 
 
if __name__ == "__main__":
    main()








