"""
Run the PromptFlow locally.

Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""

# %%
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
# azure version promptflow apis
from promptflow.client import PFClient
from azure.core.credentials import TokenCredential
from dotenv import dotenv_values

if __name__ == "__main__":

    print("Loading configs from file.")
    config = dotenv_values('../../../.env')

    # Getting credentials for local access
    # -----------------------------------------------------------------------------

    # %%
    try:
        credential: TokenCredential = DefaultAzureCredential()
        # Check if given credential can get token successfully.
        credential.get_token("https://management.azure.com/.default")
    except Exception:
        # Fall back to InteractiveBrowserCredential in case DefaultAzureCredential not work
        credential = InteractiveBrowserCredential()
    # %%
    # Get a handle to workspace
    pf = PFClient(
        credential=credential,
        # this will look like xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        subscription_id=config['SUBSCRIPTION_ID'],
            resource_group_name=config['AZUREML_RESOURCE_GROUP'],
            workspace_name=config['AZUREML_WORKSPACE'],
    )

    print("currently Azure Promptflow SDK don't support create connection and upload to workspace, so we need to create connection manually IN PORTAL")
    # Loading PromptFLow
    # %%
    # load flow
    flow_path = "./promptflow"
    data_path = "./data/batch_run_data.jsonl"
    # assume you have existing runtime with this name provisioned
    runtime = config['PROMPTFLOW_RUNTIME']

    # %%
    # create run
    base_run = pf.run(
        flow=flow_path,
        data=data_path,
        runtime=runtime,
        column_mapping={  # map the url field from the data to the url input of the flow
            "chat_history": "${data.chat_history}",
            "question": "${data.question}",
            "customer": "${data.customer}"
        },
        display_name="sql-promptflow-demo-1"
    )
    pf.stream(base_run)
    # %%
    details = pf.get_details(base_run)
    details.head(10)

    pf.visualize(base_run)
    # %%
