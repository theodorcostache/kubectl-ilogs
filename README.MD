# Kubectl Interactive Logs

The interactive logs kubectl extension is built on top of the Kubernetes API and aims to provide an interactive approach to retrieving pod logs. 

It supports pattern matching with regular expressions and works by displaying a list of pods matching the requested criteria and prompting the user to select one. Once a pod is selected, the extension will print the list of available containers inside the pod and will ask the user to select one for displaying the logs.

![](demo.gif)

## Dependencies

To use the extension, the following packages have be installed:

For Ubuntu (tested with Ubuntu 18.04):

```
sudo apt-get update && sudo apt-get install -y python3 python3-dev python3-pip
```

For CentOS (tested with Centos 7):

```
sudo yum -y install gcc python3 python3-devel python3-pip
```

For Fedora (tested with Fedora 31):

```
sudo dnf -y update && sudo dnf install -y findutils gcc python3 python3-devel python3-pip
```

## Installation

To install the extension use the following command:

```
sudo ./install.sh
```