"""
Azure ML Pipeline: SmartArchive Archive Forecasting
Automated workflow for data preparation → training → model registration

This pipeline automates the complete ML workflow for SmartArchive archive
volume and storage savings prediction in Azure ML.
"""
import json
import os
from azure.ai.ml import MLClient, command, Input, Output
from azure.ai.ml.entities import Pipeline, Environment, AmlCompute
from azure.ai.ml.constants import AssetTypes
from azure.identity import AzureCliCredential
from azure.ai.ml.dsl import pipeline

def main():
    print("=" * 80)
    print("SmartArchive Azure ML Pipeline Setup")
    print("=" * 80)
    
    # --- Load Azure configuration ---
    config_path = "azure_config.json"
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"{config_path} not found.\n"
            "Please create it with:\n"
            "{\n"
            '  "subscription_id": "your-subscription-id",\n'
            '  "resource_group": "your-resource-group",\n'
            '  "workspace_name": "your-workspace-name"\n'
            "}\n"
        )
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    subscription_id = config["subscription_id"]
    resource_group = config["resource_group"]
    workspace_name = config["workspace_name"]
    
    print(f"\nAzure Configuration:")
    print(f"  Subscription: {subscription_id}")
    print(f"  Resource Group: {resource_group}")
    print(f"  Workspace: {workspace_name}")
    
    # --- Connect to Azure ML workspace ---
    print("\nConnecting to Azure ML workspace...")
    credential = AzureCliCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )
    print(f"✅ Connected to Azure ML workspace: {workspace_name}")
    
    # --- Define compute cluster (or use existing) ---
    compute_name = "cpu-cluster"
    print(f"\nSetting up compute cluster: {compute_name}")
    try:
        compute = ml_client.compute.get(compute_name)
        print(f"✅ Using existing compute cluster: {compute_name}")
    except Exception:
        print(f"Creating new compute cluster: {compute_name}...")
        compute = AmlCompute(
            name=compute_name,
            type="amlcompute",
            size="STANDARD_DS3_V2",
            min_instances=0,
            max_instances=2,
            idle_time_before_scale_down=120,
        )
        ml_client.compute.begin_create_or_update(compute).wait()
        print(f"✅ Compute cluster created: {compute_name}")
    
    # --- Create custom environment with dependencies ---
    env_name = "smartarchive-pipeline-env"
    print(f"\nSetting up environment: {env_name}")
    environment = Environment(
        name=env_name,
        description="Environment for SmartArchive archive forecasting model training",
        conda_file="pipeline_conda.yml",
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
    )
    
    try:
        env = ml_client.environments.create_or_update(environment)
        print(f"✅ Environment registered: {env_name}")
    except Exception as e:
        print(f"⚠️  Using existing environment or error: {e}")
    
    # --- Define pipeline components ---
    print("\nDefining pipeline components...")
    
    # Component 1: Data Preparation
    # Prepares SmartArchive data and engineers features
    data_prep_component = command(
        name="data_preparation",
        display_name="SmartArchive Data Preparation",
        description="Download and prepare SmartArchive archive data with feature engineering",
        code="./src/ml/pipeline_components",
        command="""python prepare_data.py \
            --output_data ${{outputs.prepared_data}} \
            --input_data ${{inputs.input_data}}""",
        environment=f"{env_name}@latest",
        inputs={
            "input_data": Input(type=AssetTypes.URI_FILE, optional=True),
        },
        outputs={
            "prepared_data": Output(type=AssetTypes.URI_FOLDER)
        },
    )
    print("  ✅ Data Preparation component defined")
    
    # Component 2: Model Training
    # Trains RandomForest model with MultiOutput for archive volume and savings prediction
    train_component = command(
        name="model_training",
        display_name="SmartArchive Model Training",
        description="Train RandomForest model to predict archive volume and storage savings",
        code="./src/ml/pipeline_components",
        command="""python train_model.py \
            --input_data ${{inputs.prepared_data}} \
            --n_estimators ${{inputs.n_estimators}} \
            --output_model ${{outputs.trained_model}} \
            --metrics_output ${{outputs.metrics}}""",
        environment=f"{env_name}@latest",
        inputs={
            "prepared_data": Input(type=AssetTypes.URI_FOLDER),
            "n_estimators": 100,
        },
        outputs={
            "trained_model": Output(type=AssetTypes.MLFLOW_MODEL),
            "metrics": Output(type=AssetTypes.URI_FOLDER)
        },
    )
    print("  ✅ Model Training component defined")
    
    # Component 3: Model Registration
    # Registers model to Azure ML Model Registry with metadata
    register_component = command(
        name="model_registration",
        display_name="SmartArchive Model Registration",
        description="Register trained model to Azure ML workspace",
        code="./src/ml/pipeline_components",
        command="""python register_model.py \
            --input_model ${{inputs.trained_model}} \
            --model_name ${{inputs.model_name}} \
            --metrics_input ${{inputs.metrics}}""",
        environment=f"{env_name}@latest",
        inputs={
            "trained_model": Input(type=AssetTypes.MLFLOW_MODEL),
            "model_name": "smartarchive-archive-forecast",
            "metrics": Input(type=AssetTypes.URI_FOLDER)
        },
    )
    print("  ✅ Model Registration component defined")
    
    # --- Build the pipeline ---
    print("\nBuilding pipeline...")
    
    @pipeline(
        name="smartarchive_forecasting_pipeline",
        description="End-to-end pipeline for SmartArchive: data prep → training → registration",
        compute=compute_name,
    )
    def smartarchive_pipeline(
        n_estimators: int = 100,
        input_data_file: Input = None
    ):
        """Pipeline definition"""
        # Step 1: Prepare data
        prep_step = data_prep_component(
            input_data=input_data_file
        )
        
        # Step 2: Train model
        train_step = train_component(
            prepared_data=prep_step.outputs.prepared_data,
            n_estimators=n_estimators
        )
        
        # Step 3: Register model
        register_step = register_component(
            trained_model=train_step.outputs.trained_model,
            model_name="smartarchive-archive-forecast",
            metrics=train_step.outputs.metrics
        )
        
        return {
            "prepared_data": prep_step.outputs.prepared_data,
            "trained_model": train_step.outputs.trained_model,
            "metrics": train_step.outputs.metrics
        }
    
    # --- Create and submit pipeline ---
    print("Creating pipeline job...")
    pipeline_job = smartarchive_pipeline(n_estimators=100)
    
    print("Submitting pipeline to Azure ML...")
    pipeline_run = ml_client.jobs.create_or_update(
        pipeline_job,
        experiment_name="smartarchive-archive-forecasting"
    )
    
    print("\n" + "=" * 80)
    print("✅ Pipeline submitted successfully!")
    print("=" * 80)
    print(f"\nPipeline Details:")
    print(f"  Pipeline Run ID: {pipeline_run.name}")
    print(f"  Experiment: smartarchive-archive-forecasting")
    print(f"  Status: {pipeline_run.status}")
    print(f"\nView pipeline at:")
    print(f"  {pipeline_run.studio_url}")
    print("\nTo stream logs until completion, run:")
    print(f"  ml_client.jobs.stream('{pipeline_run.name}')")
    print("=" * 80)

if __name__ == "__main__":
    main()
