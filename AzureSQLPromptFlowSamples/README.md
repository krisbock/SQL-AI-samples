# Azure SQL Promptflow Samples

This is the code repository for Azure SQL Promptflow Demo. It demonstrates how to create a chatbot that can query the data from your own Azure SQL database.

## Prerequisites
- Azure subscription
- Azure AI Search service
- Azure Machine Learning workspace
- Azure SQL Server with Sample AdventureWorksLT database
- Azure Open AI service

and the following python packages

## Developers: Note

This works with the latest Promptflow and AI Search versions as of 18/04/2024.

## Getting started

### Install VSCode and Promptflow

- You need to install Visual studio Code: [Here](https://code.visualstudio.com/).
- You also need to install the PromptFlow extension, available here: [Prompt Flow community ecosystem](https://learn.microsoft.com/azure/machine-learning/prompt-flow/community-ecosystem?view=azureml-api-2).

### Install python packages

**Warning:** Tested against Python 3.9, 3.10.

And install the packages by:

```bash
pip install -r requirements.txt
```

(Optional, install VS code extension: [https://marketplace.visualstudio.com/items?itemName=ms-python.python])

### Filling in configurations needed

Create a .env files in the parent directory based on the sample file. You will need to set up Azure Open AI (AOAI), Azure AI Search (AIS) and Azure SQL Server with sample AdventureWorksLT database.  There is a helper notebook [Azure AI Search Prepare](src/sql-promptflow-demo/acs/azure_ai_search_prepare.ipynb)

Note that we have two models, `AZURE_OPENAI_API_GPT_DEPLOYMENT` and `AZURE_OPENAI_API_EMB_DEPLOYMENT`. These are for the chat model (GPT) and embeddings used as part of AI Search (EMB).

Default build_image: `mcr.microsoft.com/azureml/promptflow/promptflow-runtime:latest`

### Sending secret keys to Key Vault

The AzureML workspace used to deploy this flow comes with a default key vault for storing secret keys. Navigate to the AML workspace in Azure Portal and in the Overview pane find the associated key vault. Grab its URI and add it as the `AZURE_KEYVAULT_URI` key within your .env environment file.

This repo uses .env environment files to load sensitive variables and keys (file not tracked by git).  Please update it to match your environment and save:

```powershell
AZURE_OPENAI_API_GPT_KEY=
AZURE_OPENAI_API_EMB_KEY=
AZURE_OPENAI_API_GPT_BASE=
AZURE_OPENAI_API_EMB_BASE=
AZURE_OPENAI_API_GPT_VERSION=
AZURE_OPENAI_API_EMB_VERSION=
AZURE_OPENAI_API_GPT_DEPLOYMENT=
AZURE_OPENAI_API_EMB_DEPLOYMENT=
AZURE_SEARCH_KEY=
AZURE_SEARCH_INDEX=
AZURE_SEARCH_ENDPOINT=
#Doesn't support vectorQueries body AZURE_SEARCH_API_VERSION=2023-07-01-Preview
AZURE_SEARCH_API_VERSION=
AZURE_SQL_SERVER=
AZURE_SQL_DATABASE_NAME=
AZURE_SQL_USER=
AZURE_SQL_PASSWORD=
AZURE_SQL_CONNECTION_STRING=
AZURE_KEYVAULT_URI=

# PromptFlow Specific
AZURE_OPENAI_CONNECTION_NAME= # User defined name as reference to AOAI connection in PromptFlow
AZURE_SQL_CONNECTION_NAME=  # User defined name as reference to SQL connection in PromptFlow
AZURE_SEARCH_CONNECTION_NAME= # User defined name as reference to AI Search connection in PromptFlow
AZURE_OPENAI_TYPE=azure_open_ai

# DEPLOYMENT
SUBSCRIPTION_ID= # Azure Subscription ID
AZUREML_RESOURCE_GROUP= 
AZUREML_WORKSPACE=
PROMPTFLOW_RUNTIME=automatic
PROMPTFLOW_IMAGE_BASE="mcr.microsoft.com/azureml/promptflow/promptflow-runtime:latest"
# The name for an endpoint must start with an upper- or lowercase letter and only consist of '-'s and alphanumeric characters.
ENDPOINT_NAME=
ENDPOINT_DEPLOYMENT_NAME=
MODEL_NAME=
```

The setup.py script will load keys into KeyVault.

Now your secrets should be in key vault, and the flow can access these secrets locally via your `az login` auth and in deployment via the default key vault association with AML.

**IMPORTANT:** you need to give yourself access to the Key Vault.

- You can do this by navigating to the Key Vault on the Azure Portal
- Click on *Access policies* And *+ Create*.
- Add yourself with all secret privileges.

**Note:** secrets in Azure Key Vault must consist of lowercase alphanumeric characters or dashes (-). Because of this, existing config_local.json values (prior to Key Vault) need to be renamed to fit this format (lowercase, replace `_` with `-`).


### Run setup.py to set up the flow

```powershell
cd src\sql-promptflow-demo
python setup.py
```
In case you experience authentication errors, replace `credential = DefaultAzureCredential()` with `credential = DefaultAzureCredential(exclude_shared_token_cache_credential=True)`. You will need to replace it in promptflow modules as well.
### Test the flow

```bash
cd src/sql-promptflow-demo
# run chat flow with default question in flow.dag.yaml
python -m  promptflow._cli.pf flow test --flow promptflow/. --interactive
```

Alternatively, you can use the VSCode plugin for PromptFlow.  open in VS code the `flow.dag.yaml`, and there is a little "run all" icon that looks like >> at the top right, you can click it to run.

### Batch run and evaluate the flow
Prepare batch run data `data\batch_run_data.jsonl` and run the following command to batch run the flow and evaluate the results.

```bash
cd src/sql-promptflow-demo
python batch_run_and_eval.py
```

### Deploy the flow on local

See below, go to the parent directory first!

```bash
# go to parent directory
cd ..
# run chat flow with default question in flow.dag.yaml
python -m  promptflow._cli.pf flow serve --source promptflow <this is the folder name> --port 8080 --host localhost
```

Then it can be tested with (use git bash):

```bash
curl http://localhost:8080/score --data '{"chat_history":[], "question":"Why my jobs are running slow?", "team_name":"test"}' -X POST  -H "Content-Type: application/json"
```

The above doesn't work in Windows Powershell, this alternate command with Invoke-WebRequest worked instead:

```powershell
$uri = "http://localhost:8080/score"
$body = @{
    chat_history = @()
    question     = "Why my jobs are running slow?"
    team_name    = "test"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

$response = Invoke-WebRequest -Uri $uri -Method POST -Body $body -Headers $headers

# Display the response (if needed)
$response.Content
```

### Run the flow on cloud

The same flow can be executed on cloud, and the code will be uploaded to AML workspace. After that, you can deploy using the portal's UI. The job can be found from the output of the `run.py` as well as from the portal.

1. To run, one need to create runtime first. And in the `configs/flow_config.json`, put the runtime name there.
2. You need to create one AzureOpenAI connection and two custom connections from the Portal; one custom connection is used to connect SQL database, the other is used to connect Azure AI Search/Azure OpenAI Embedding API. The connection names are user generated through the `AZURE_OPENAI_CONNECTION_NAME`, `AZURE_SQL_CONNECTION_NAME` and `AZURE_SEARCH_CONNECTION_NAME` in `../.env`. By running `setup.py` those connections will be automatically created. For detailed steps, see [reference](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/tools-reference/python-tool?view=azureml-api-2#how-to-consume-custom-connection-in-python-tool).

```bash
# go to parent directory
cd ..
# run chat flow with default question in flow.dag.yaml
python run.py
```

### Deploy on cloud

For set up the promptflow, the user should have run the `setup.py` file, which will modify the workload file (`flow.dag.yaml`).

By running the script of `deploy.py` step by step, one can create an endpoint for the flow in their azure machine learning workspace.
The `deploy.py` script will produce various deployment files under the `Deployments/` folder from tempaltes.

**IMPORTANT**: there are two next steps you need to take to finalize setting up the PromptFlow endpoint.

1. As for running on the cloud (see above), you will need to manually create the required connections on your PromptFlow endpoint.
   CF [Create necessary connections](https://promptflow.azurewebsites.net/community/cloud/local-to-cloud.html#create-necessary-connections) for reference.
   The name of the connection should match what you have set in your configuration file.
2. Once deployed, you need to allow the endpoint to use the connection that's stored in Azure ML.
   1. For this, navigate to your *Azure ML workspace* on the *Azure Portal*.
   2. Click on *Access control (IAM)* and click *+ Add*, *Role assignment*.
   3. In the role list, select *AzureML Data Scientist* and click *Next*.
   4. Click on *Managed identity*, *+ Select members*.
   5. Select your subscription and under *Managed identity* select *All system-assigned managed identities*.
   6. Search for an identity with the same name as your deployment endpoint and add it.
   7. Click *save*.
3. In addition, you will need to add the endpoint to access the default AzureML Key Vault for secrets
   1. Grab the application ID by searching the endpoint name in Azure Portal, going to the "Identity" tab and finding the object (principal) ID
   2. Navigate to Key Vault (can find in Overview of AzureML workspace)
   3. Goto *Access policies* and click *Create*
   4. Select *Get* under *Secret permissions*. This is all the endpoints will need.
   5. Hit Next
   6. Enter the app ID for the endpoint or search for it.
   7. Finalize the access policy
   8. The bot should now be able to access Key Vault

**Note:** `key_config_local.json` is not copied to AzureML (security risk). A tmp directory is first created without this file and uploaded with the model.

### Generate a docker

See below, go to the parent directory first!

```bash
# go to parent directory
cd ..
# run chat flow with default question in flow.dag.yaml
python -m  promptflow._cli.pf flow export --source d:\Repos\DRICopilot0725\DRICopilot\src\core\copilot\promptflow <this is the folder name> --output d:\Repos --format docker
```

### Troubleshooting

If running "az ml" results in the extension not being recognized, you may need to upgrade you azure cli: [https://learn.microsoft.com/azure/machine-learning/how-to-configure-cli?view=azureml-api-2&tabs=public]

From the documentation: "The new Machine Learning extension requires Azure CLI version >=2.38.0. Ensure this requirement is met"

After upgrading, run these commands to refresh things:

```bash
az extension remove -n azure-cli-ml
az extension remove -n ml
az extension add -n ml
```

### References
- [Auzre SQL Database documentation](https://docs.microsoft.com/en-us/azure/azure-sql/database)
- [Azure Cognitive Search documentation](https://docs.microsoft.com/en-us/azure/search/)
- [Azure Machine Learning documentation](https://docs.microsoft.com/en-us/azure/machine-learning/)
- [Azure Open AI documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/)
- [PromptFlow documentation](https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/overview-what-is-prompt-flow?view=azureml-api-2/)
