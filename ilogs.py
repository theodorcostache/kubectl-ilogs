#!python
#cython: language_level=3

import re
import time
import argparse

from kubernetes import client, config

def read_args():
    """
    prompts and parses the user input
    
    :return: a tuple containing the pod name and the namespace
    """
    
    parser = argparse.ArgumentParser(description="""List the availble containers inside a pod
                                      for selection and displays the logs of the selected container""")
    parser.add_argument('pod', metavar='pod', type=str, nargs=1, help='pattern to use for searching the pod name')
    parser.add_argument('--namespace', '-n', nargs="?", default=None, help='pattern to use for searching the namespace')

    args = parser.parse_args()
    
    return (args.pod[0], args.namespace)

def search_pod(client, pod, namespace):
    """
    makes a request against the Kubernetes api and searches for all pods that match the given criteria

    :param client the Kubernetes api client
    :param str pod: the search criteria for the pod name
    :param str namespace: the namespace where to search for the pod
    
    :return: the list of pod name and namespace tuples matching the given criteria
    """
    
    response = client.list_pod_for_all_namespaces(watch=False)

    pods = response.items
    
    if namespace:
        pods = filter(lambda p: re.match(namespace, p.metadata.namespace), pods)    
        
    pods = filter(lambda p: re.match(pod, p.metadata.name), pods)
    
    result = [(p.metadata.name, p.metadata.namespace) for p in pods]
    
    return result
    
def get_containers(client, pod, namespace):    
    """
    makes a request against the Kubernetes api and extracts the names of pod's containers

    :param client the Kubernetes api client
    :param str pod: the name of the pod
    :param str namespace: the namespace where to search for the pod
    
    :return: the list of all containers within the pod
    """

    pod = client.read_namespaced_pod(pod, namespace)
    
    containers = []
    
    if pod and pod.spec.containers:
        containers = [ c.name for c in pod.spec.containers] 
    if pod and pod.spec.init_containers:
        containers += [ c.name for c in pod.spec.init_containers]
        
    return containers

def prompt_selection(values, prompt, print_template, headers):
    """
    displays the list of available values with a corresponding id and prompts the user to select one

    :param values: the list of values available for selection
    
    :return: the value selected by the user
    """
    
    values_length = len(values)
     
    print(print_template.format(*headers))
    for id, value in enumerate(values, start=1):
        output = (print_template.format(id, *value) if isinstance(value, tuple) else print_template.format(id, value))
        print(output)
        
    value_id = int(input(f"{prompt} (1,{values_length}): "))
    
    if value_id not in range(1, values_length+1):
        raise RuntimeError(f"Please enter a valid selection (1,{values_length})")
        
    return values[value_id-1]

def get_logs(client, pod, namespace, container=None):
    """
    makes a request against the Kubernetes api and displays the requested log

    :param client the Kubernetes api client
    :param str pod: the name of the pod
    :param str namespace: the namespace where to search for the pod
    :param str container: the name of the container for which to display the logs
    """

    log = client.read_namespaced_pod_log(pod, namespace, container=container)
    
    return log
    
def main():
    (pod_arg, namespace_arg) = read_args()

    try:
        config.load_kube_config()
        clientV1 = client.CoreV1Api()

        pods = search_pod(clientV1, pod_arg, namespace_arg)

        if len(pods) == 0:
            raise RuntimeError('There are no results that match your search')
        elif len(pods) == 1:
            (pod, namespace) = pods[0]
        else:
            (pod, namespace) = prompt_selection(pods, 'Multiple pods match your search criteria. Please select one', 
                                                "{:<6}{:<60}{:<15}", ['NR.', 'POD', 'NAMESPACE'])
        
        containers = get_containers(clientV1, pod, namespace)
        
        if len(containers) == 0:
            raise RuntimeError('There are no containers available')
        elif len(containers) == 1:
            container = containers[0]
        else:
            container = prompt_selection(containers, 'Please select container', "{:<6}{:<50}", ['NR.', 'CONTAINER'])
        
        logs = get_logs(clientV1, pod, namespace, container)
        
        print(logs)
        
    except (KeyboardInterrupt, RuntimeError, FileNotFoundError) as e:
        print(e)
        return 1
    
    return 0

def init():
  if __name__ == "__main__":
    exit(main())

init()