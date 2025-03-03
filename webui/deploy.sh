aws s3 cp index.html s3://flashcards-ai/index.html \
    --content-type "text/html" \
    --no-cli-pager

aws s3api wait object-exists \
    --bucket flashcards-ai \
    --key index.html
