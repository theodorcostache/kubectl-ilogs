# Kubectl Interactive Logs

The interactive logs extension is built on top of the Kubernetes API and aims to provide an interactive approach to retrieving pod logs. 

It supports pattern matching with regular expressions and works by displaying a list of pods matching the requested criteria and prompting the user to select one. Once a pod is selected, the extension will print the list of available containers inside the pod and will ask the user to select one for displaying the logs.

![](demo.gif)

## Installation

To install the extension use the following command:

```
./install.sh
```