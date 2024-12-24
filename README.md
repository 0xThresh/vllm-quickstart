# vLLM Quickstart
This quickstart repo uses [Pulumi](https://www.pulumi.com/) to create AWS resources to build a vLLM instance with
the DataDog agent installed. 

## Setup
In order to set the required secrets for DataDog, select your model to serve on vLLM, and set a 
HuggingFace token (if you're pulling gated models), run these commands: 
```
pulumi config set Model <model from HuggingFace>
pulumi config set --secret DataDogAPIKey <secret value>
pulumi config set DataDogSite <site>
pulumi config set --secret HFToken <secret value>
```

Once the model is running, you can test that it's working by connecting to the instance in SSM
and running this curl command: 
```
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "<model>",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What year was Python invented?"}
        ]
    }'
```