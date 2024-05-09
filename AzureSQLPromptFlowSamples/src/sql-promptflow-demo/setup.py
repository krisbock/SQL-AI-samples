"""
This file do the setup for testing the flow locally.

Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
"""
# %%
# Imports
from promptflow.client import PFClient
from promptflow.entities import AzureOpenAIConnection, CustomConnection
import yaml

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import dotenv_values


def get_keyvault_secret(keyvault_uri: str, secret_name: str):
        """Use the default credential (e.g., az login) to get key vault access and retrieve a secret."""

        # changing key to lowercase and replacing underscores with dashes
        secret_name = secret_name.lower().replace('_', '-')

        credential = DefaultAzureCredential(
            exclude_shared_token_cache_credential=True, exclude_visual_studio_credential=True)
        client = SecretClient(vault_url=keyvault_uri, credential=credential)
        secret = client.get_secret(secret_name)
        return secret.value


def upload_secret(vault_url, key, value):
    """Use the default credential (e.g., az login) to get key vault access and set a secret."""

    # changing key to lowercase and replacing underscores with dashes
    key = key.lower().replace('_', '-')

    # Use the default credential (e.g., az login)
    credential = DefaultAzureCredential(
        exclude_shared_token_cache_credential=True, exclude_visual_studio_credential=True)
    client = SecretClient(vault_url=vault_url, credential=credential)

    # Set (or update) the secret
    client.set_secret(key, value)
    
if __name__ == "__main__":
    pf = PFClient()
    # %%
    # Keyvault Setup


    


    # %%
    # Load the config json files
    config = dotenv_values("../../../.env")

    # Send config_local.json contents to key vault
    print("Uploading all secrets from .env to Key Vault")
    print("Note: keys will be converted to lowercase and underscores will be replaced with dashes (Key Vault requirement)")
    for key in ['AZURE_OPENAI_API_GPT_KEY', 'AZURE_OPENAI_API_EMB_KEY', 'AZURE_SEARCH_KEY', 'AZURE_SQL_CONNECTION_STRING']:
        print(f"Uploading secret {key}")
        upload_secret(config['AZURE_KEYVAULT_URI'], key, config[key])
        print(f"Secret {key} uploaded successfully")


    # %%
    # setting up AOAI connection
    print("Setting up AOAI connections.")
    print("Getting AOAI API key from keyvault")
    aoai_api_key = get_keyvault_secret(config['AZURE_KEYVAULT_URI'], 'AZURE_OPENAI_API_GPT_KEY')

    connection = AzureOpenAIConnection(
        name=config['AZURE_OPENAI_CONNECTION_NAME'],
        api_key=aoai_api_key,
        api_base=config['AZURE_OPENAI_API_GPT_BASE'],
        api_type=config['AZURE_OPENAI_TYPE'],
        api_version=config['AZURE_OPENAI_API_GPT_VERSION'],
    )
    conn = pf.connections.create_or_update(connection)
    print("Successfully created connection")
    # %%
    # setting up SQL connection
    print("Setting up SQL connections.")
    print("Getting SQL Connection STRING from keyvault")
    connection_string = get_keyvault_secret(config['AZURE_KEYVAULT_URI'], 'AZURE_SQL_CONNECTION_STRING')

    connection = CustomConnection(
        name=config['AZURE_SQL_CONNECTION_NAME'],
        secrets={'CONNECTION-STRING': connection_string}
    )
    conn = pf.connections.create_or_update(connection)
    print("successfully created connection")

    # %%
    # setting up AI search/Embedding connection
    print("Setting up AI Search connections.")
    print("Getting AIS/Embedding Connection STRING from keyvault")
    acs_key = get_keyvault_secret(config['AZURE_KEYVAULT_URI'], 'AZURE_SEARCH_KEY')
    aoai_api_key_embed = get_keyvault_secret(config['AZURE_KEYVAULT_URI'], 'AZURE_OPENAI_API_EMB_KEY')

    connection = CustomConnection(
        name=config['AZURE_SEARCH_CONNECTION_NAME'],
        configs={'AZURE_OPENAI_API_EMB_BASE': config['AZURE_OPENAI_API_EMB_BASE'],
                'AZURE_OPENAI_API_EMB_VERSION': config['AZURE_OPENAI_API_EMB_VERSION'],
                'AZURE_SEARCH_API_VERSION': config['AZURE_SEARCH_API_VERSION'],
                'AZURE_SEARCH_ENDPOINT': config['AZURE_SEARCH_ENDPOINT'],
                'AZURE_SEARCH_INDEX': config['AZURE_SEARCH_INDEX'],
                'AZURE_OPENAI_API_EMB_DEPLOYMENT': config['AZURE_OPENAI_API_EMB_DEPLOYMENT']
                },
        secrets={'ACS-SEARCH-KEY': acs_key,
                'AZURE_OPENAI_API_EMB_KEY': aoai_api_key_embed
                }
    )
    # Create the connection, note that all secret values will be scrubbed in the returned result
    conn = pf.connections.create_or_update(connection)
    print("successfully created connection")

    # %%
    # Load the yaml file to dictionary path is azure_openai.yml
    print("Setting up flow.dag.yaml.")
    with open('./promptflow/flow.dag.sample.yaml') as f:
        config_flow = yaml.load(f, Loader=yaml.FullLoader)
    # import pdb; pdb.set_trace()
    # replace the deployment_name with the one you want to use
    for node in config_flow['nodes']:
        # Setting up model for the agent chat node.
        if node.get('api') == "chat":
            if 'deployment_name' in node:
                node['deployment_name'] = config['AZURE_OPENAI_API_GPT_DEPLOYMENT']
            if 'deployment_name' in node['inputs']:
                node['inputs']['deployment_name'] = config['AZURE_OPENAI_API_GPT_DEPLOYMENT']
            # Setting up model for the final chat node.
            if 'connection' in node:
                node['connection'] = config['AZURE_OPENAI_CONNECTION_NAME']
        else:
            if 'conn_db' in node['inputs']:
                node['inputs']['conn_db'] = config['AZURE_SQL_CONNECTION_NAME']
            if 'conn' in node['inputs']:
                node['inputs']['conn'] = config['AZURE_SEARCH_CONNECTION_NAME']

    # write the yaml file back
    with open('./promptflow/flow.dag.yaml', 'w') as f:
        yaml.dump(config_flow, f)

    # %%
