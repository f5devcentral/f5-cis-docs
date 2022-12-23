#!/bin/bash

#create kubernetes bigip container connecter, authentication and RBAC
kubectl create secret generic bigip-login -n kube-system --from-literal=username=admin --from-literal=password=<secret>
kubectl create serviceaccount k8s-bigip-ctlr -n kube-system
kubectl create clusterrolebinding k8s-bigip-ctlr-clusteradmin --clusterrole=cluster-admin --serviceaccount=kube-system:k8s-bigip-ctlr
kubectl create -f f5-cluster-deployment.yaml
kubectl create -f f5-bigip-node.yaml