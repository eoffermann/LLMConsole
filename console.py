import os
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from llama_cpp import Llama
from huggingface_hub import hf_hub_download

# Detect the shell environment
def detect_shell():
    shell = os.environ.get("SHELL") or os.environ.get("ComSpec")
    if shell is None:
        return "unknown"
    if "bash" in shell:
        return "bash"
    elif "powershell" in shell.lower():
        return "powershell"
    elif "cmd" in shell.lower():
        return "cmd"
    else:
        return "unknown"

# Configure the LLM model
def configure_llm(repo_id: str = "TheBloke/LLaMA-2-7B-chat-GGUF", filename: str = "llama-2-7b-chat.ggmlv3.q6_K.bin"):
    """
    Downloads and configures a specific quantized model from Hugging Face.

    Args:
        repo_id (str): The repository ID on Hugging Face.
        filename (str): The specific model file to download.

    Returns:
        Llama: An instance of the Llama model.
    """
    # Download the specified file from the repository
    model_path = hf_hub_download(repo_id=repo_id, filename=filename)
    # Instantiate the Llama model
    llm = Llama(model_path=model_path)
    return llm

# System prompt for the LLM
def get_system_prompt(shell: str) -> str:
    """
    Returns a system prompt that instructs the LLM to generate commands matching the current shell environment.

    Args:
        shell (str): The detected shell environment (e.g., 'bash', 'powershell', 'cmd').

    Returns:
        str: System prompt string.
    """
    return f"You are an assistant that generates valid and safe shell commands for the '{shell}' environment. " \
           "Always return a single shell command in response to the user's request. Do not provide explanations."

# Call the LLM with the appropriate prompt
def call_llm(llm: Llama, command: str) -> str:
    """
    Calls the LLaMA-based LLM to generate a shell command based on user input.

    Args:
        llm (Llama): The instantiated Llama model.
        command (str): The natural language input provided by the user.

    Returns:
        str: A shell command suggested by the LLM.
    """
    shell = detect_shell()
    system_prompt = get_system_prompt(shell)

    # Prepare the messages for the chat completion
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": command}
    ]

    # Generate the response
    response = llm.create_chat_completion(messages=messages, max_tokens=50, stop=["\n"])
    suggested_command = response["choices"][0]["message"]["content"].strip()

    print(f"LLM suggested command for '{shell}': {suggested_command}")
    return suggested_command

def execute_command(command: str):
    """
    Execute a shell command and display its output.

    Args:
        command (str): The shell command to execute.
    """
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(e.stderr)

def main():
    # Configure the LLM once during initialization
    llm = configure_llm()

    session = PromptSession(history=FileHistory("command_history.txt"))
    completer = WordCompleter(["dir", "cd", "cls", "copy", "move", "del", "mkdir", "rmdir", "exit"], ignore_case=True)

    print("Welcome to the Custom Command Interface! Type your commands below.")
    print("Use '!' to invoke the LLM. Type 'exit' to quit.\n")

    while True:
        try:
            user_input = session.prompt("> ", completer=completer)

            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            if user_input.startswith("!"):
                # Intercept command and pass to call_llm
                llm_command = call_llm(llm, user_input[1:].strip())
                confirmation = session.prompt(f"LLM suggested command: {llm_command}\nDo you want to execute this command? (yes/no): ").strip().lower()

                if confirmation in {"yes", "y"}:
                    execute_command(llm_command)
                else:
                    print("Command execution skipped.")
            else:
                # Execute normal shell command
                execute_command(user_input)

        except KeyboardInterrupt:
            print("\nOperation canceled.")
        except EOFError:
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()
