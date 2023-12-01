# OpenShift OVN-Kubernetes using F5 BIG-IP HA with NO Tunnels

This document demonstrates how to use **OVN-Kubernetes with F5 BIG-IP HA Routes** to Ingress traffic without using an Overlay. Using OVN-Kubernetes with F5 BIG-IP Routes removes the complexity of creating VXLAN tunnels or using Calico. This document demonstrates **High Availability (HA) BIG-IP's working with OVN-Kubernetes**. Diagram below demonstrates a OpenShift Cluster with three masters and three worker nodes. The three applications; **tea,coffee and mocha** are deployed in the **cafe** namespace.
![architecture](https://github.com/f5devcentral/f5-cis-docs/blob/main/user_guides/ovn-kubernetes-ha/diagram/ovn-k8s-ha.png)

Demo on YouTube [video](https://youtu.be/Hzz_UFzU7UA)

### Step 1: Deploy OpenShift using OVNKubernetes

Deploy OpenShift Cluster with **networktype** as **OVNKubernetes**. Change the default to **OVNKubernetes** in the install-config.yaml before creating the cluster

### Step 2: Configure BIG-IP Routes
`Note:` Starting with CIS 2.13 version, configuration of static routes is automated by CIS.To enable static routing mode with ovn-kubernetes CNI, configure --static-routing-mode=true and --orchestration-cni=ovn-k8s in CIS deployment args.For more details, refer [Static-routing](https://github.com/F5Networks/k8s-bigip-ctlr/tree/master/docs/config_examples/StaticRoute)

Configure static routes in BIG-IP with node subnets assigned for the three worker nodes in the OpenShift cluster. Get the node subnet assigned and host address

```
# oc describe node ocp-pm-trw88-worker-d6zsg |grep "node-subnets\|node-primary-ifaddr"
k8s.ovn.org/host-addresses: ["10.192.125.172"]
k8s.ovn.org/node-subnets: {"default":"10.129.2.0/23"}

# oc describe node ocp-pm-trw88-worker-k7lsd |grep "node-subnets\|node-primary-ifaddr"
k8s.ovn.org/node-primary-ifaddr: {"ipv4":"10.192.125.174/24"}
k8s.ovn.org/node-subnets: {"default":"10.131.0.0/23"}

# oc describe node ocp-pm-trw88-worker-vdtmb |grep "node-subnets\|node-primary-ifaddr"
k8s.ovn.org/host-addresses: ["10.192.125.177"]
k8s.ovn.org/node-subnets: {"default":"10.128.2.0/23"}
```

Add static routes to BIG-IP via tmsh for all node subnets using 

```
tmsh create /net route <node_subnet> gw <node_ip>
```
```
tmsh create /net route 10.129.2.0/23 gw 10.192.125.172
tmsh create /net route 10.131.0.0/23 gw 10.192.125.174
tmsh create /net route 10.128.2.0/23 gw 10.192.125.177
```
View static routes created on BIG-IP

![routes](https://github.com/f5devcentral/f5-cis-docs/blob/main/user_guides/ovn-kubernetes-ha/diagram/2022-10-12_13-30-34.png)

**Note:** Manually sync the BIG-IP so the routes are deployed on the standby

**Setup complete!** Deploy CIS and create OpenShift Routes

### Step 3: Deploy CIS for each BIG-IP

F5 Controller Ingress Services (CIS) called **Next Generation Routes Controller**. Next Generation Routes Controller extended F5 CIS to use multiple Virtual IP addresses. Before F5 CIS could only manage one Virtual IP address per CIS instance.

Add the following parameters to the CIS deployment

* Routegroup specific config for each namespace is provided as part of extendedSpec through ConfigMap.
* ConfigMap info is passed to CIS with argument --extended-spec-configmap="namespace/configmap-name"
* Controller mode should be set to openshift to enable multiple VIP support(--controller-mode="openshift")

### BIG-IP 01

```
args: [
  # See the k8s-bigip-ctlr documentation for information about
  # all config options
  # https://clouddocs.f5.com/containers/latest/
  "--bigip-username=$(BIGIP_USERNAME)",
  "--bigip-password=$(BIGIP_PASSWORD)",
  "--bigip-url=10.192.125.60",
  "--bigip-partition=OpenShift",
  "--namespace=cafe",
  "--pool-member-type=cluster",
  "--insecure=true",
  "--manage-routes=true",
  "--extended-spec-configmap="kube-system/extended-cm"
  "--controller-mode="openshift"
  "--as3-validation=true",
  "--log-as3-response=true",
]
```

### BIG-IP 02

```
args: [
  # See the k8s-bigip-ctlr documentation for information about
  # all config options
  # https://clouddocs.f5.com/containers/latest/
  "--bigip-username=$(BIGIP_USERNAME)",
  "--bigip-password=$(BIGIP_PASSWORD)",
  "--bigip-url=10.192.125.61",
  "--bigip-partition=OpenShift",
  "--namespace=cafe",
  "--pool-member-type=cluster",
  "--insecure=true",
  "--manage-routes=true",
  "--extended-spec-configmap="kube-system/extended-cm"
  "--controller-mode="openshift"
  "--as3-validation=true",
  "--log-as3-response=true",
]
```

Deploy CIS in OpenShift

```
oc create secret generic bigip-login -n kube-system --from-literal=username=admin --from-literal=password=<secret>
oc create -f bigip-ctlr-clusterrole.yaml
oc create -f f5-bigip-ctlr-01-deployment.yaml
oc create -f f5-bigip-ctlr-02-deployment.yaml
```

CIS [repo](https://github.com/f5devcentral/f5-cis-docs/tree/main/user_guides/ovn-kubernetes-ha/next-gen-route/cis)

Validate both CIS instances are running 

```
# oc get pod -n kube-system
NAME                                            READY   STATUS    RESTARTS   AGE
k8s-bigip-ctlr-01-deployment-7cc8b7cf94-2csz7   1/1     Running   0          16s
k8s-bigip-ctlr-02-deployment-5c8d8c4676-hjwpr   1/1     Running   0          16s
```

### Step 4: Deploy extended ConfigMap

Using extended ConfigMap

* Extended ConfigMap provides control to the admin to create and maintain the resource configuration centrally.
* namespace: cafe, vserverAddr: 10.192.125.65

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: extended-cm
  namespace: kube-system
  labels:
    f5nr: "true"
data:
  extendedSpec: |
    extendedRouteSpec:
    - namespace: cafe
      vserverAddr: 10.192.125.65
      vserverName: cafe
      allowOverride: true
```

Deploy extended ConfigMap

```
oc create -f global-cm.yaml
```
ConfigMap [repo](https://github.com/f5devcentral/f5-cis-docs/blob/main/user_guides/ovn-kubernetes-ha/next-gen-route/route/global-cm.yaml)

### Step 5 Creating OpenShift Routes for cafe.example.com

User-case for the OpenShift Routes:

- Edge Termination
- Backend listening on PORT 8080

Create OpenShift Routes

```
oc create -f route-tea-edge.yaml
oc create -f route-coffee-edge.yaml
oc create -f route-mocha-edge.yaml
```

Routes [repo](https://github.com/f5devcentral/f5-cis-docs/tree/main/user_guides/ovn-kubernetes-ha/next-gen-route/route/cafe/secure)

Validate OpenShift Routes using the BIG-IP

![big-ip route](https://github.com/f5devcentral/f5-cis-docs/blob/main/user_guides/ovn-kubernetes-ha/diagram/2022-06-07_15-35-21.png)

Validate OpenShift Virtual IP using the BIG-IP

![big-ip pools](https://github.com/f5devcentral/f5-cis-docs/blob/main/user_guides/ovn-kubernetes-ha/diagram/2022-06-07_15-37-33.png)

Validate OpenShift Routes policies on the BIG-IP

![traffic](https://github.com/f5devcentral/f5-cis-docs/blob/main/user_guides/ovn-kubernetes-ha/diagram/2022-06-07_15-38-08.png)

Validate OpenShift Routes policies by connecting to the Public IP

![traffic](https://github.com/f5devcentral/f5-cis-docs/blob/main/user_guides/ovn-kubernetes-ha/diagram/2022-10-12_13-46-30.png)

**Note**:
* Configuration listed above is validated on OCP 4.11 and 4.12 versions. 
