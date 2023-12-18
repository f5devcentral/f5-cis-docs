# Multicluster Usecases with High Availability CIS

### Prerequisites

* A pair of high availability OpenShift/Kubernetes clusters should be available, which have the same applications running in both clusters.
* An external openshift/kubernetes cluster to additionally distribute the app traffic.
* HealthCheck endpoint should be available to check the health of the primary cluster. Currently, TCP/HTTP Health endpoints are supported.
* In an HA deployment of CIS, CIS needs to be deployed in both the primary and secondary cluster. Also, the same extended ConfigMap needs to be deployed in both the primary and secondary cluster.
* CIS will look for the same service name in both primary and secondary clusters to expose the application via routes or cr resources. 

**Deploying CIS HA:**

### active-active mode (More details at [active-active](../CIS%20HA/Active-Active/README.md))

If CIS is running in active-active mode, the pool members from both virtual servers’ clusters (primary and secondary) are part of the HA cluster, as well as members from other remotely monitored clusters.

### active-standby mode (More details at [active-standby](../CIS%20HA/Active-Standby/README.md))

* If CIS is running in active-standby mode on the primary cluster, the pool members are updated for virtual servers only from the primary cluster, and from all the other remotely monitored clusters except the secondary cluster.
* If the primary cluster is down, and CIS on the secondary cluster has taken control, then pool members from the secondary cluster, as well as all other remotely monitored clusters, are populated for the virtual servers irrespective of the value of HA mode.

### ratio mode (More details at [ratio](../CIS%20HA/Ratio/README.md))

* If CIS is running in ratio mode, pool members from all the Kubernetes/Openshift clusters are updated for the virtual server. However, the traffic distribution is done based on the ratio values defined for each cluster.
Ratio doesn’t require CIS to be running in an HA environment. It is supported in both CIS HA and non-HA environments.

**Note**

* For HA mode [Active-Standby, Active-Active, Ratio], CIS monitored resource manifests(such as routes, CRDs, extendedConfigmaps) must be available in both the clusters.
* The CIS monitored resource manifests must be identical on both primary and Secondary Clusters
* So, In case of CIS failover, CIS on Secondary Cluster will take control and will start processing the CIS monitored resource manifests.
* CIS on Secondary Cluster will not process the CIS monitored resource manifests if they are not available in Secondary Cluster.
* MakeSure to have identical resource manifests in both the clusters to avoid any issues during CIS failover.

**When the primary cluster is healthy and CIS is running on it**

| HA Mode Values | Primary Cluster Pool Members | Secondary Cluster Pool Members | Other Remotely Monitored Cluster Pool Members | Traffic Distribution Based on Ratio |
|----------------|------------------------------|--------------------------------|-----------------------------------------------|-------------------------------------|
| active-active  | Yes	                         | Yes	                           | Yes	                                          | No                                  |
| active-standby | Yes                          | No                             | Yes                                           | No                                  |
| ratio          | Yes                          | Yes                            | Yes                                           | Yes                                 |

**When the primary cluster is down, which means the CIS secondary cluster in control**

| HA Mode Values | Primary Cluster Pool Members | Secondary Cluster Pool Members | Other Remotely Monitored Cluster Pool Members | Traffic Distribution Based on Ratio |
|----------------|------------------------------|--------------------------------|-----------------------------------------------|-------------------------------------|
| active-active  | No                           | Yes	                           | Yes	                                          | No                                  |
| active-standby | No                           | Yes                            | Yes                                           | No                                  |
| ratio          | Yes                          | Yes                            | Yes                                           | Yes                                 |

