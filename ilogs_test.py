import ilogs
from types import SimpleNamespace
import pytest
from unittest import mock  
import argparse
import kubernetes

##############################################################################
# Fixtures
##############################################################################
POD_NAMES = ['test-pod-1','test-pod-2','test-pod-3','test-pod-4']
POD_NAMESPACE = 'test-namespace'
POD_CONTAINER_NAMES = ['container1', 'container2']
POD_INIT_CONTAINER_NAMES = ['init-container1', 'init-container2']

def create_fake_pod(pod_name, pod_namespace, pod_containers, pod_init_containers):
    fake_pod = SimpleNamespace()
    fake_pod.metadata = SimpleNamespace(name=pod_name, namespace=pod_namespace)
    fake_pod.spec = SimpleNamespace()
    fake_pod.spec.containers = [ SimpleNamespace(name=name) for name in pod_containers]
    fake_pod.spec.init_containers = [ SimpleNamespace(name=name) for name in pod_init_containers]
    
    return fake_pod

@pytest.fixture
def fake_pods():
    fake_pods = [] 
    for pod_name in POD_NAMES:
        fake_pods.append(create_fake_pod(pod_name, POD_NAMESPACE, POD_CONTAINER_NAMES, POD_INIT_CONTAINER_NAMES))
    
    return fake_pods

##############################################################################
# Scenario
##############################################################################
class Scenario:
    def __init__(self, 
                 pod_regex, 
                 pod_namespace_regex, 
                 pods, 
                 expected_output, 
                 expected_exit_code=0,
                 log=None, 
                 pod_selection=None, 
                 container_selection=None):
        self.pod_regex = pod_regex
        self.pod_namespace_regex = pod_namespace_regex
        self.pods = pods
        self.log = log
        self.pod_selection = pod_selection
        self.container_selection = container_selection
        self.expected_exit_code = expected_exit_code
        self.expected_output = expected_output
        
    
    def __noop_load_config(self):
        pass
        
    def __create_fake_input(self, result):
        def fake_input(prompt):
            print(prompt)
            for e in result:
                if prompt == e[0]:
                    return e[1]
            return None
        return fake_input
    
    def execute(self, monkeypatch, capsys):
        
        ilogs.input = self.__create_fake_input([self.pod_selection, self.container_selection])
        
        pod_selection = None
        selected_pod_index = -1
        
        if self.pod_selection:
            selected_pod_index = int(self.pod_selection[1])
        
        if selected_pod_index <= len(self.pods):
            pod_selection = self.pods[selected_pod_index-1]
            
        monkeypatch.setattr(argparse.ArgumentParser, 
                            "parse_args", 
                            mock.MagicMock(return_value=argparse.Namespace(pod=[self.pod_regex], namespace=self.pod_namespace_regex)))
        
        monkeypatch.setattr(kubernetes.client.CoreV1Api, 
                            "list_pod_for_all_namespaces", 
                            mock.MagicMock(return_value=SimpleNamespace(items=self.pods)))
        
        monkeypatch.setattr(kubernetes.client.CoreV1Api, 
                            "read_namespaced_pod", 
                            mock.MagicMock(return_value=pod_selection))
        
        monkeypatch.setattr(kubernetes.client.CoreV1Api, 
                            "read_namespaced_pod_log", 
                            mock.MagicMock(return_value=self.log))
                                
        monkeypatch.setattr(kubernetes.config, "load_kube_config", self.__noop_load_config)
    
        with mock.patch.object(ilogs, "__name__", "__main__"):
            with mock.patch.object(ilogs,'exit') as mock_exit:
                ilogs.init()
        
            assert mock_exit.call_args[0][0] == self.expected_exit_code
        
        captured = capsys.readouterr()
        
        assert captured.out == self.expected_output    
    

##############################################################################
# Tests
##############################################################################   
def test_no_pod_found(monkeypatch, capsys, fake_pods):
    
    test_scenario = Scenario(pod_regex=".*[5]",
                       pod_namespace_regex=".*test.*",
                       pods=fake_pods,
                       expected_exit_code=1,
                       expected_output=("There are no results that match your search\n"))
    
    test_scenario.execute(monkeypatch, capsys)
    
def test_invalid_pod_selection(monkeypatch, capsys, fake_pods):
    
    test_scenario = Scenario(pod_regex=".*[1|2|3]",
                       pod_namespace_regex=".*test.*",
                       pods=fake_pods,
                       log='fake log test',
                       pod_selection=('Multiple pods match your search criteria. Please select one (1,3): ', '4'),
                       container_selection=('Please select container (1,4): ', '1'),
                       expected_exit_code=1,
                       expected_output=(
                           "NR.   POD                                                         NAMESPACE      \n" +
                           "1     test-pod-1                                                  test-namespace \n" +
                           "2     test-pod-2                                                  test-namespace \n" +
                           "3     test-pod-3                                                  test-namespace \n" +
                           "Multiple pods match your search criteria. Please select one (1,3): \n" +
                           "Please enter a valid selection (1,3)\n"))
    
    test_scenario.execute(monkeypatch, capsys)
    
def test_invalid_container_selection(monkeypatch, capsys, fake_pods):
    
    test_scenario = Scenario(pod_regex=".*[1|2|3]",
                       pod_namespace_regex=".*test.*",
                       pods=fake_pods,
                       log='fake log test',
                       pod_selection=('Multiple pods match your search criteria. Please select one (1,3): ', '2'),
                       container_selection=('Please select container (1,4): ', '5'),
                       expected_exit_code=1,
                       expected_output=(
                           "NR.   POD                                                         NAMESPACE      \n" +
                           "1     test-pod-1                                                  test-namespace \n" +
                           "2     test-pod-2                                                  test-namespace \n" +
                           "3     test-pod-3                                                  test-namespace \n" +
                           "Multiple pods match your search criteria. Please select one (1,3): \n" +
                           "NR.   CONTAINER                                         \n"
                           "1     container1                                        \n" +
                           "2     container2                                        \n" +
                           "3     init-container1                                   \n" +
                           "4     init-container2                                   \n" +
                           "Please select container (1,4): \n" +
                           "Please enter a valid selection (1,4)\n"))
    
    test_scenario.execute(monkeypatch, capsys)
    
def test_single_pod_with_no_container(monkeypatch, capsys, fake_pods):
    
    test_scenario = Scenario(pod_regex=".*1",
                       pod_namespace_regex=".*test.*",
                       pods=[create_fake_pod("test-pod-1","test-namespace",[],[])],
                       log='fake log test',
                       pod_selection=('Multiple pods match your search criteria. Please select one (1,1): ', '1'),
                       container_selection=('Please select container (1,4): ', '1'),
                       expected_exit_code=1,
                       expected_output=("There are no containers available\n"))
    
    test_scenario.execute(monkeypatch, capsys)
    
def test_single_pod_with_single_container(monkeypatch, capsys, fake_pods):
    
    test_scenario = Scenario(pod_regex=".*1",
                       pod_namespace_regex=".*test.*",
                       pods=[create_fake_pod("test-pod-1","test-namespace",['container-1'],[])],
                       log='fake log test',
                       pod_selection=('Multiple pods match your search criteria. Please select one (1,1): ', '1'),
                       container_selection=('Please select container (1,1): ', '1'),
                       expected_exit_code=0,
                       expected_output=("fake log test\n"))
    
    test_scenario.execute(monkeypatch, capsys)
    
def test_multiple_pods_with_multiple_containers(monkeypatch, capsys, fake_pods):
    
    test_scenario = Scenario(pod_regex=".*[1|2]",
                       pod_namespace_regex=".*test.*",
                       pods=fake_pods,
                       log='fake log test',
                       pod_selection=('Multiple pods match your search criteria. Please select one (1,2): ', '1'),
                       container_selection=('Please select container (1,4): ', '1'),
                       expected_exit_code=0,
                       expected_output=(
                           "NR.   POD                                                         NAMESPACE      \n" +
                           "1     test-pod-1                                                  test-namespace \n" +
                           "2     test-pod-2                                                  test-namespace \n" +
                           "Multiple pods match your search criteria. Please select one (1,2): \n" +
                           "NR.   CONTAINER                                         \n"
                           "1     container1                                        \n" +
                           "2     container2                                        \n" +
                           "3     init-container1                                   \n" +
                           "4     init-container2                                   \n" +
                           "Please select container (1,4): \n" +
                           "fake log test\n"
                           ))
    
    test_scenario.execute(monkeypatch, capsys)