rm -f package.zip

cd package
zip -r ../my_deployment_package.zip .
cd ..
zip my_deployment_package.zip main.py

export AWS_DEFAULT_REGION=eu-central-1

#aws lambda create-function \
#    --function-name flashcards \
#    --runtime python3.9 \
#    --handler main.lambda_handler \
#    --role arn:aws:iam::580115349817:role/helvetia-ai-lambda-role  \
#    --architectures arm64 \
#    --zip-file fileb://my_deployment_package.zip \
#    --timeout 900


aws lambda update-function-code \
    --function-name flashcards \
    --zip-file fileb://my_deployment_package.zip \
    --no-cli-pager

aws lambda wait function-updated \
    --function-name flashcards
