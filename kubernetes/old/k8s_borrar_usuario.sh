#!/bin/bash
echo ""
read -p "Nombre del usuario: " usuario
kubectl config unset users.$usuario
echo ""
echo ""
