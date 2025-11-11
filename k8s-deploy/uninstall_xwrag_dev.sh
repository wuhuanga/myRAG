#!/bin/bash

NAMESPACE=rag
helm uninstall xwrag-dev --namespace $NAMESPACE
