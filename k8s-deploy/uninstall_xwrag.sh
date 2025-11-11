#!/bin/bash

NAMESPACE=rag
helm uninstall xwrag --namespace $NAMESPACE
