#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import socket
from subprocess import Popen,PIPE
import sys
import time
import os

#os.system("source /import/bc2/sys/profile.d/sge.sh")

#try:
    #cluster_name = os.environ["SGE_CELL"]
#except KeyError:
    #print "SGE_CELL environment variable not found. Please source the SGE settings file"
    #sys.exit(1)

# probably you want here the value of $SGE_CELL
cluster_name = "bc2"

# define which complex value you use for memory reservation
# typical values are h_vmem or m_mem_free
memory_complex_value = "h_rss"

# InfluxDB
CARBON_SERVER = 'sysmon01'
CARBON_PORT = 2003

def main():

    now = int(time.time())
    jobs = parse_qstat()
    hosts = parse_qhost()
    #print jobs
    lines = []

    total_used_slots = get_used_slots(jobs)
    #print "total used slots " + str(used_slots)
    values = ("sge", cluster_name, "total", "slots", total_used_slots, str(now))
    values = '{0}.{1}.{2}.{3} {4} {5}'.format(*values)
    lines.append((values))
    
    total_running_jobs = get_running_jobs(jobs)
    #print "total running jobs " + str(running_jobs)
    values = ("sge", cluster_name, "total", "jobs", total_running_jobs, str(now))
    values = '{0}.{1}.{2}.{3} {4} {5}'.format(*values)
    lines.append((values))

    total_reserved_mem = get_total_reserved_memory(jobs)
    #print total_reserved_mem
    values = ("sge", cluster_name, "total", "reserved_memory", total_reserved_mem, str(now))
    values = '{0}.{1}.{2}.{3} {4} {5}'.format(*values)
    lines.append((values))
    
    total_io = get_total_io_usage(jobs)
    #print total_io
    values = ("sge", cluster_name, "total", "io", total_io, str(now))
    values = '{0}.{1}.{2}.{3} {4} {5}'.format(*values)
    lines.append((values))
    
    users_list = get_users_with_running_jobs(jobs)
    slots_by_user = get_slots_by_user(users_list, jobs)
    jobs_by_user = get_running_jobs_by_user(users_list, jobs)
    #print "slots by user " + str(slots_by_user)
    #print "jobs by user " + str(jobs_by_user)

    #waiting_jobs = get_waiting_jobs(jobs)
    #print "wating jobs " + str(waiting_jobs)

    projects_list = get_projects_with_running_jobs(jobs)
    slots_by_project = get_slots_by_project(projects_list, jobs)
    jobs_by_project = get_running_jobs_by_project(projects_list, jobs)
    #print "slots by project" + str(slots_by_project)
    #print "jobs by project " + str(jobs_by_project)

    queues = get_queues_with_running_jobs(jobs)
    slots_by_queue = get_slots_by_queue(queues, jobs)
    jobs_by_queue = get_running_jobs_by_queue(queues, jobs)
    #print queues
    #print slots_by_queue
    #print jobs_by_queue

    io_by_users = get_io_usage_by_user(users_list, jobs)
    #print io_by_users

    reserved_mem_by_user = get_reserved_memory_by_user(users_list, jobs)
    #print reserved_mem_by_user



    for i in slots_by_user:
        user = i[0]
        slots = i[1]
        values = ("sge", cluster_name, "users", user, "slots", slots, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))

    for i in slots_by_project:
        project = i[0]
        slots = i[1]
        values = ("sge", cluster_name, "project", project, "slots", slots, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))
    
    for i in slots_by_queue:
        queue = i[0]
        queue = queue.replace(".","_")
        slots = i[1]
        values = ("sge", cluster_name, "queue", queue, "slots", slots, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))
    
    for i in jobs_by_user:
        user = i[0]
        jobs = i[1]
        values = ("sge", cluster_name, "users", user, "jobs", jobs, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))

    for i in jobs_by_project:
        project = i[0]
        jobs = i[1]
        values = ("sge", cluster_name, "project", project, "jobs", jobs, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))
    
    for i in jobs_by_queue:
        queue = i[0]
        queue = queue.replace(".","_")
        jobs = i[1]
        values = ("sge", cluster_name, "queue", queue, "jobs", jobs, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))

    for i in reserved_mem_by_user:
        user = i[0]
        reserved_mem = i[1]
        values = ("sge", cluster_name, "users", user, "reserved_memory", reserved_mem, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))
    
    for i in io_by_users:
        user = i[0]
        io = i[1]
        values = ("sge", cluster_name, "users", user, "io", io, str(now))
        values = '{0}.{1}.{2}.{3}.{4} {5} {6}'.format(*values)
        lines.append((values))
    

    message = '\n'.join(lines) + '\n'
    #print message
    send_to_graphite(message)


def get_running_jobs(jobs):
    " returns an integer with total amount of running jobs "
    running_jobs = 0
    for job in jobs:
        if job['state'] == 'r':
            running_jobs += 1
    return running_jobs


def get_used_slots(jobs):
    " return an integer with total amount of used slots"
    used_slots = 0
    for job in jobs:
        if job['state'] == 'r':
            used_slots += int(job['slots'])
    return used_slots


def get_users_with_running_jobs(jobs):
    " returns a list with all the users who have running jobs"
    users = []
    for job in jobs:
        if job['state'] == 'r' and job['JB_owner'] not in users:
            users.append(job['JB_owner'])
    return users


def get_projects_with_running_jobs(jobs):
    " returns a list with all the projects which have running jobs"
    projects = []
    for job in jobs:
        if job['state'] == 'r' and job['JB_project'] not in projects:
            projects.append(job['JB_project'])
    return projects


def get_slots_by_user(users_list, jobs):
    " returns a list of tuples in format: (username, used_slots)"
    slots_by_user = []
    for user in users_list:
        slots = 0
        for job in jobs:
            if job['JB_owner'] == user and job['state'] == 'r':
                slots += int(job['slots'])
        slots_by_user.append((user,slots))
    return slots_by_user


def get_running_jobs_by_user(users_list, jobs):
    " returns a list of tuples in format: (username, running_jobs)"
    jobs_by_user = []
    for user in users_list:
        running_jobs = 0
        for job in jobs:
            if job['JB_owner'] == user and job['state'] == 'r':
                running_jobs += 1
        jobs_by_user.append((user,running_jobs))
    return jobs_by_user


def get_slots_by_project(projects_list, jobs):
    " returns a list of tuples in format: (project, slots)" 
    slots_by_project = []
    for project in projects_list:
        slots = 0
        for job in jobs:
            if job['JB_project'] == project and job['state'] == 'r':
                slots += int(job['slots'])
        slots_by_project.append((project, slots))
    return slots_by_project


def get_running_jobs_by_project(projects_list, jobs):
    " returns a list of tuples in format: (project, running_jobs)"
    jobs_by_project = []
    for project in projects_list:
        running_jobs = 0
        for job in jobs:
            if job['JB_project'] == project and job['state'] == 'r':
                running_jobs += 1
        jobs_by_project.append((project,running_jobs))
    return jobs_by_project


def get_waiting_jobs(jobs):
    " returns and integer with number of waiting jobs"
    waiting_jobs = 0
    for job in jobs:
        if job['state'] == 'qw' or job['state'] == 'hqw':
            waiting_jobs += 1
    return waiting_jobs

def get_queues_with_running_jobs(jobs):
    queues = []
    for job in jobs:
        job_queue = job['queue_name'].split('@')[0]
        if job_queue not in queues and job['state'] == 'r':
            queues.append(job_queue)
    return queues

def get_slots_by_queue(queues_list, jobs):
    slots_by_queue = []
    for queue in queues_list:
        slots = 0
        for job in jobs:
            job_queue = job['queue_name'].split('@')[0]
            if queue == job_queue and job['state'] == 'r':
                slots += int(job['slots'])
        slots_by_queue.append((queue, slots))
    return slots_by_queue

def get_running_jobs_by_queue(queues, jobs):
    jobs_by_queue = []
    for queue in queues:
        running_jobs = 0
        for job in jobs:
            job_queue = job['queue_name'].split('@')[0]
            if queue == job_queue and job['state'] == 'r':
                running_jobs += 1
        jobs_by_queue.append((queue, running_jobs))
    return jobs_by_queue

def get_io_usage_by_user(users_list, jobs):
    " returns a list of tuples in format: (username, io_usage)"
    io_by_user = []
    for user in users_list:
        user_io_usage = 0.0
        for job in jobs:
            if job['JB_owner'] == user and job['state'] == 'r':
                if 'io_usage' in job:
                    user_io_usage += float(job['io_usage'])
        io_by_user.append((user, user_io_usage))
    return io_by_user

def get_total_io_usage(jobs):
    total_io = 0.0
    for job in jobs:
        if job['state'] == 'r':
            if 'io_usage' in job:
                total_io += float(job['io_usage'])
    return total_io

def get_reserved_memory_by_user(users_list, jobs):
    """ Returns a list of tuples in format: (username, reserved_mem_by_user).
        reserved_mem_by_user is in megabytes
        This function assumes that the memory reservation is by-core and that's
        why job_reserved_mem is multiplied by number of slots """
    mem_by_user = []
    for user in users_list:
        user_reserved_mem = 0
        for job in jobs:
            job_reserved_mem = 0
            if job['JB_owner'] == user and job['state'] == 'r':
                requested_mem = 'requested_%s' % (memory_complex_value)
                if requested_mem in job:
                    # get reserved memory (which can be in format 100M or 2G) in bytes
                    job_reserved_mem = human2bytes(job[requested_mem])
                    # multiply reserved memory by number of slots
                    job_reserved_mem = job_reserved_mem * int(job['slots'])
                    # convert bytes to megabytes and remove decimals
                    job_reserved_mem = int((float(job_reserved_mem)/float(1024))/float(1024))
                    user_reserved_mem += job_reserved_mem
        mem_by_user.append((user, user_reserved_mem))
    return mem_by_user

def get_total_reserved_memory(jobs):
    """ Returns total reserved_memory. reserved_memory is in megabytes
        This function assumes that the memory reservation is by-core and that's
        why job_reserved_mem is multiplied by number of slots """
    total_reserved_mem = 0
    for job in jobs:
        if job['state'] == 'r':
            requested_mem = 'requested_%s' % (memory_complex_value)
            if requested_mem in job:
                #print job[requested_mem]
                # get reserved memory (which can be in format 100M or 2G) in bytes
                job_reserved_mem = human2bytes(job[requested_mem])
                # multiply reserved memory by number of slots
                job_reserved_mem = job_reserved_mem * int(job['slots'])
                # convert bytes to megabytes and remove decimals
                job_reserved_mem = int((float(job_reserved_mem)/float(1024))/float(1024))
                total_reserved_mem += job_reserved_mem
    return total_reserved_mem
                    

def parse_qstat():
    " returns a list of dictionaries. Each dictionary contains the info for a job"

    qstat_xml_output = Popen(["qstat", "-ext", "-g", "d", "-u", "*", "-r", "-xml"], stdout=PIPE).communicate()[0]
    tree = ET.ElementTree(ET.fromstring(qstat_xml_output))
    root = tree.getroot()

    job_xml_elements = root.findall("./queue_info/job_list")

    all_jobs_info = []

    for job in job_xml_elements:
        job_info = {}
        for i in job.getiterator():
            if i.tag == "requested_pe":
                job_info[i.tag] = i.attrib['name']
                continue
            if i.tag == "granted_pe":
                job_info[i.tag] = i.attrib['name']
                continue
            if i.tag == "hard_request":
                job_info["requested_" + str(i.attrib['name'])] = i.text
                continue
            job_info[i.tag] = i.text
            #print i.tag
            #print i.attrib
            #print i.text
        del job_info['job_list']
        #print job_info
        all_jobs_info.append(job_info)

    return all_jobs_info

def parse_qhost():
    " returns a list of dictionaries. Each dictionary contains the info for a host"

    qhost_xml_output = Popen(["qhost", "-xml"], stdout=PIPE).communicate()[0]
    tree = ET.ElementTree(ET.fromstring(qhost_xml_output))
    root = tree.getroot()

    hosts_xml_elements = root.findall("./host")

    all_hosts_info = []

    for host in hosts_xml_elements:
        host_info = {}
        for i in host.getiterator():
            # first output from XML is just global info. We skip it
            if i.attrib['name'] == 'global':
                continue
            if i.text == '-':
                continue

            # if the xml tag is 'host' we fetch the machine hostname
            if i.tag == 'host':
                host_info['hostname'] = i.attrib['name']
            
            # if xml tag is 'hostvalue' we fetch the info 
            if i.tag == 'hostvalue':
                host_info[i.attrib['name']] = i.text

        # we verify that host_info is not empty because the first xml entry
        # generates a empty dict
        if host_info:
            all_hosts_info.append(host_info)

    return all_hosts_info
 
def send_to_graphite(message):
    sock = socket.socket()
    try:
        sock.connect( (CARBON_SERVER,CARBON_PORT) )
    except:
        print "Couldn't connect to %(server)s on port %(port)d " % { 'server':CARBON_SERVER, 'port':CARBON_PORT }
        sys.exit(1)
    #print message
    sock.send(message)

def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.

      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776

      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """

    SYMBOLS = {
        'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
        'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                           'zetta', 'iotta'),
        'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
        'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                           'zebi', 'yobi'),
    }

    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]:1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])


if __name__ == "__main__":
    main()
