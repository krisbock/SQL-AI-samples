"""
Deploying this prompt flow to an endpoint.

Copyright (c) Microsoft Corporation.
Licensed under the MIT license.

"""

# %%
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    Model,
    ManagedOnlineDeployment,
    Environment,
    OnlineRequestSettings,
    BuildContext
)
from azure.identity import DefaultAzureCredential
import hashlib
from dotenv import dotenv_values
import os

def hash_folder(folder_path):
    """
    Generate hash for entire folder.

    Returns:
        hash as string
    """
    sha256 = hashlib.sha256()
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                file_content = f.read()
                sha256.update(file_content)
    return sha256.hexdigest()
# %%
if __name__ == "__main__":

    print("Loading configs from file.")
    config = dotenv_values("../../../.env")
    
    flow_to_execute = "promptflow"
    try:
        ml_client = MLClient(
            DefaultAzureCredential(),
            config['SUBSCRIPTION_ID'],
            config['AZUREML_RESOURCE_GROUP'],
            config['AZUREML_WORKSPACE']
        )
    except Exception as e:
        print(f"Unable to log into AzureML Workspace with error: {e}")

    # Register PromptFlow as Model
    model_name = config['MODEL_NAME']

    model_hash = hash_folder(f"{flow_to_execute}")
    print("Hash of the folder:", model_hash)

    model = Model(
        name=model_name,
        path=f"{flow_to_execute}",
        description=(
            f"{flow_to_execute} model registered for "
            f"prompt flow deployment"
            ),
        properties={"azureml.promptflow.source_flow_id": flow_to_execute},
    )

    try:
        model_info = ml_client.models.get(
            name=model_name,
            label='latest'
        )
        m_hash = dict(model_info.tags).get("model_hash")
        if m_hash is not None:
            if m_hash != model_hash:
                ml_client.models.create_or_update(model)
        else:
            ml_client.models.create_or_update(model)
    except Exception:
        ml_client.models.create_or_update(model)

    # Create the endpoint
    endpoint = ManagedOnlineEndpoint(
        name=config['ENDPOINT_NAME'],
        description="Demo Promptflow endpoint for SQLAI",
        auth_mode="key",
    )

    ml_client.online_endpoints.begin_create_or_update(
                endpoint=endpoint).result()
    

    #Create the environment first
    # env_docker_conda = Environment(conda_file="environment/conda.yml",
    #                                image=config['PROMPTFLOW_IMAGE_BASE'],
    #                                name="promptflow-sql",
    #                                 inference_config={
    #                                     "liveness_route": {"path": "/health", "port": "8080"},
    #                                     "readiness_route": {"path": "/health", "port": "8080"},
    #                                     "scoring_route": {"path": "/score", "port": "8080"},
    #                                 })

    # env_docker_conda = ml_client.environments.create_or_update(Environment(conda_file="environment/conda.yml",
    #                                image=config['PROMPTFLOW_IMAGE_BASE'],
    #                                name="promptflow-sql",
    #                                 inference_config={
    #                                     "liveness_route": {"path": "/health", "port": "8080"},
    #                                     "readiness_route": {"path": "/health", "port": "8080"},
    #                                     "scoring_route": {"path": "/score", "port": "8080"},
    #                                 }))
                                
    env_docker_conda=ml_client.environments.get("promptflow-sql", version="10")

    #ml_client.environments.create_or_update(env_docker_conda)
    # chat_deployment = ManagedOnlineDeployment(
    #     name=config['ENDPOINT_DEPLOYMENT_NAME'],
    #     endpoint_name=config['ENDPOINT_NAME'],
    #     model=model_info,
    #     description="Demo Promptflow deployment for SQLAI",
    #     environment=env_docker_conda,
    #     instance_type="Standard_DS3_v2",
    #     instance_count=1,
    #     environment_variables={
    #         "PROMPTFLOW_RUN_MODE" : "serving",
    #         "PROMPTFLOW_CONNECTION_PROVIDER": f"azureml://subscriptions/{config['SUBSCRIPTION_ID']}/resourceGroups/{config['AZUREML_RESOURCE_GROUP']}/providers/Microsoft.MachineLearningServices/workspaces/{config['AZUREML_WORKSPACE']}"
    #     },
    #     app_insights_enabled=True,
    #     request_settings=OnlineRequestSettings(
    #         request_timeout_ms=90000
    #     ),
    # )
    # env_docker_conda = Environment(
    #                         build = BuildContext(
    #                             path = "promptflow",
    #                             dockerfile_path = "Dockerfile"
    #                         ),
    #                         name="promptflow-sql",
    #                         inference_config={
    #                                 "liveness_route": {"path": "/health", "port": "8080"},
    #                                 "readiness_route": {"path": "/health", "port": "8080"},
    #                                 "scoring_route": {"path": "/score", "port": "8080"},
    #                         })

    # Deploy the model
    chat_deployment = ManagedOnlineDeployment(
        name=config['ENDPOINT_DEPLOYMENT_NAME'],
        endpoint_name=config['ENDPOINT_NAME'],
        model=model_info,
        description="Demo Promptflow deployment for SQLAI",
        environment=env_docker_conda,
        instance_type="Standard_DS3_v2",
        instance_count=1,
        environment_variables={
            "PROMPTFLOW_RUN_MODE" : "serving",
            "PROMPTFLOW_CONNECTION_PROVIDER": f"azureml://subscriptions/{config['SUBSCRIPTION_ID']}/resourceGroups/{config['AZUREML_RESOURCE_GROUP']}/providers/Microsoft.MachineLearningServices/workspaces/{config['AZUREML_WORKSPACE']}"
        },
        app_insights_enabled=True,
        request_settings=OnlineRequestSettings(
            request_timeout_ms=90000
        ),
    )

    ml_client.online_deployments.begin_create_or_update(
        chat_deployment
    ).result()

    endpoint = ml_client.online_endpoints.get(
        config['ENDPOINT_NAME'],
        local=False
    )

    #endpoint.traffic = "100"
    #ml_client.begin_create_or_update(endpoint).result()
