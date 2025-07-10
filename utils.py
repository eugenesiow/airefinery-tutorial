import os
import getpass
import yaml
import mermaid as md
from dotenv import load_dotenv, set_key
from air import DistillerClient, login

def secure_login():
    """
    Loads credentials from a .env file if it exists.
    If not, prompts the user to securely enter their AI Refinery account and API key,
    saves them to a .env file for future use, and performs the login.
    """
    # Define the path to the .env file in the current directory
    dotenv_path = '.env'
    
    # Attempt to load credentials from the .env file into environment variables
    load_dotenv(dotenv_path=dotenv_path)
    
    account = os.getenv("ACCOUNT")
    api_key = os.getenv("API_KEY")

    # If credentials are not found in the environment, prompt the user
    if not account or not api_key:
        print("AI Refinery credentials not found. Please enter them below.")
        account = getpass.getpass("Account: ")
        api_key = getpass.getpass("API Key: ")
        
        # Save the credentials to the .env file for the next session
        # The file will be created if it doesn't exist
        set_key(dotenv_path, "ACCOUNT", account)
        set_key(dotenv_path, "API_KEY", api_key)
        print("✅ Credentials saved to .env file for future use.")

        # Also set environment variables for the current session
        os.environ["ACCOUNT"] = account
        os.environ["API_KEY"] = api_key
    else:
        print("✅ Credentials successfully loaded from .env file.")

    # Now, attempt to log in with the credentials (from file or user input)
    try:
        login(
            account=account,
            api_key=api_key,
        )
    except Exception as e:
        print(f"❌ Login failed: {e}")
        # Re-raise the exception to halt execution.
        raise

def initialize_client(config_path: str, project_name: str) -> DistillerClient:
    """
    Initializes and returns a DistillerClient for a given project.

    Args:
        config_path: The path to the YAML configuration file.
        project_name: The name of the project to create or use.

    Returns:
        An initialized DistillerClient instance.
    """
    try:
        distiller_client = DistillerClient()
        # The 'project' parameter is correct for the create_project method.
        distiller_client.create_project(config_path=config_path, project=project_name)
        return distiller_client
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        # Re-raise the exception to halt execution.
        raise

def _generate_mermaid_string(config: dict) -> str:
    """
    Internal function to generate a Mermaid syntax string from agent configuration.
    This function now correctly handles newlines for use in a standard Python file.
    """
    # Use a list to build the string for clarity, performance, and to avoid newline issues.
    lines = [
        "graph TD",
        "    classDef search fill:#cde4ff,stroke:#333,stroke-width:2px;",
        "    classDef author fill:#ffdfb3,stroke:#333,stroke-width:2px;"
    ]

    agent_class_map = {agent['agent_name']: agent['agent_class'] for agent in config.get('utility_agents', [])}
    flow_agents = config.get('super_agents', [{}])[0].get('config', {}).get('agent_list', [])

    # Create a mapping from full agent name to a safe Mermaid ID for all agents in the flow
    agent_name_to_id = {agent['agent_name']: agent['agent_name'].replace(' ', '') for agent in flow_agents}

    # Process all agents defined in the flow
    for agent_details in flow_agents:
        agent_name = agent_details['agent_name']
        agent_id = agent_name_to_id[agent_name]
        
        # Define the node and its style using the ::: syntax
        agent_class = agent_class_map.get(agent_name)
        style_class = 'search' if agent_class == 'SearchAgent' else 'author'
        lines.append(f'    {agent_id}["{agent_name}"]:::{style_class}')

        # Define the edges (arrows) between nodes
        if 'next_step' in agent_details:
            for next_agent_name in agent_details['next_step']:
                # The next_agent must also be in our ID map to create a valid link
                if next_agent_name in agent_name_to_id:
                    next_agent_id = agent_name_to_id[next_agent_name]
                    lines.append(f'    {agent_id} --> {next_agent_id}')
    
    # Join all lines with a proper newline character.
    return "\n".join(lines)


def display_workflow_diagram(config_data: dict):
    """
    Generates and displays the agent workflow diagram from the configuration data.

    Args:
        config_data: A dictionary containing the agent configuration.
    """
    print("Visualizing the agent workflow...")
    try:
        mermaid_syntax = _generate_mermaid_string(config_data)
        svg_data = md.Mermaid(mermaid_syntax)
        return svg_data
    except Exception as e:
        print(f"❌ Could not generate diagram: {e}")
        # Print the generated syntax for debugging purposes
        print("--- Generated Mermaid Syntax ---")
        print(mermaid_syntax)
        print("--------------------------------")
        return None
