rm -f package.zip

cd package
zip -r ../my_deployment_package.zip .
cd ..
zip my_deployment_package.zip main.py

export AWS_DEFAULT_REGION=eu-central-1

# aws lambda create-function \
#     --function-name flashcards-fileupload \
#     --runtime python3.12 \
#     --handler main.lambda_handler \
#     --role arn:aws:iam::580115349817:role/helvetia-ai-lambda-role  \
#     --architectures arm64 \
#     --zip-file fileb://my_deployment_package.zip \
#     --timeout 900 \
#     --no-cli-pager


aws lambda update-function-code \
    --function-name flashcards-fileupload \
    --zip-file fileb://my_deployment_package.zip \
    --no-cli-pager

aws lambda wait function-updated \
   --function-name flashcards-fileupload
