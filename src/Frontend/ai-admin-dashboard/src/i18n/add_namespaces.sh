#!/bin/bash

# Generate import statements for all new namespaces
echo "// New namespace imports"
for namespace in forms errors modals tenants inventory; do
  echo ""
  echo "// ${namespace^} imports"
  for lang in en es fr zh ar de ja so yue pa tl it pt pl ru vi hi uk fa ko ta ur gu ro nl cr iu bn he; do
    langUpper=$(echo "$lang" | tr '[:lower:]' '[:upper:]')
    namespaceCapital=$(echo "$namespace" | sed 's/\b\(.\)/\u\1/')
    echo "import ${lang}${namespaceCapital} from './locales/${lang}/${namespace}.json';"
  done
done
