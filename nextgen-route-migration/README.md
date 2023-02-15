NextGen Route Migration Tool
========================================================

This tool helps in migrating from Legacy Routes to nextGenRoutes.

It needs to be provided with the CIS deployment file or deployment resource name, it generates the required ExtendedConfigmap, policyCR(if as3 override configmap file is provided) and CIS 
deployment file which can be used to migrate to nextGenRoutes mode.

### Dependencies
This migration tool is written in Python 3.8.
Dependencies are included in `requirements.txt` and can be installed
using `pip` with `pip3 install -r requirements.txt`.<br/>
Kubeconfig file may be required if user wants to provide cis deployment name in the CLI parameters.

### CLI Parameters

Following CLI parameters can be provided to the nextGen Route migration tool.

| Parameter        | Required | Description                                 | Default                 | Examples                    |
|------------------|----------|---------------------------------------------|-------------------------|-----------------------------|
| -f, --cis_file   | Required | The path of the CIS deployment file         | N/A                     | cis-deploy.yaml             |
| -d, --cis_name   | Required | Name of CIS deployment                      | N/A                     | kube-system/test-cis-deploy |
| -k, --kubeconfig | Required | Path/Location of Kubeconfig                 | /home/user/.kube/config | /home/user/.kube/config     |
| -cm, --cm_file   | Optional | The path of the AS3 override configmap file | N/A                     | as3-cm.yaml                 |
| -o, --output     | Optional | Path of the output directory                | output                  |                             |
| -log, --loglevel | Optional | Log level for the migration tool            | INFO                    | DEBUG, ERROR, WARNING       |


You may either provide the CIS deployment yaml configuration or CIS deployment name (namespace/deployment-name).<br/>
**_NOTE:_** _If deployment name is provided then this tool will need the kube-config file to access the CIS deployment. 
Please place the kubeconfig in the default location i.e. ~/.kube/config or Use the -k or --kubeconfig parameter to specify kubeconfig loation.

### Running migration script
Simply run the following command to run the script.
```
python main.py
```
**_NOTE:_** _Default output directory is output/_

If you wish to provide the cis deployment file then run the following command (with --cis_file or -f):
```
python main.py --cis_file ~/cis-deploy.yaml
```
or if you wish to provide the cis deployment name then run the following command (with --cis_name or -d):
```
python main.py --cis_name kube-system/cis-deploy
```
or if you wish to provide the cis deployment name along with kubeconfig location then run the following command (with --cis_name or -d and --kubeconfig or -k):
```
python main.py --cis_name kube-system/cis-deploy --kubeconfig /home/user/.kube/config
```

If you wish to provide the as3 Override configmap file then run the following command (with --cm_file or -cm):
```
python main.py --cis_file ~/cis-deploy.yaml --cm_file ~/as3-cm.yaml
```
If you wish to store the output yaml files in any other directory then run the following command (with --output or -o):
```
python main.py --cis_file ~/cis-deploy.yaml --output <path to the output directory>
```
For more details related to the available command line options, run the following command:
```
python main.py -h
```

Running this tool will generate the ExtendedConfigmap, policyCR(if as3 override configmap file is provided) and the CIS deployment file in the output directory which needs to be applied in order to migrate to nextGen Routes.