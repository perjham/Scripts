#!/bin/bash
echo ""
kubectl config view -o jsonpath='{.users[*].name}'
echo ""
echo ""
