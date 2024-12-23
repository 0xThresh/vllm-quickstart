# vLLM Quickstart
This quickstart repo uses [Pulumi](https://www.pulumi.com/) to create AWS resources to build a vLLM instance with
the DataDog agent installed. 

## Setup
In order to set the required secrets for DataDog, select your model to serve on vLLM, and set a 
HuggingFace token (if you're pulling gated models), run these commands: 
```
pulumi config set Model Qwen/Qwen2.5-1.5B-Instruct
pulumi config set --secret DataDogAPIKey <secret-value>
pulumi config set DataDogSite <site>
pulumi config set --secret HFToken <secret-value>
```
