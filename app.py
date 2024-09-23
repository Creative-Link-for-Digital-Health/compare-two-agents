import streamlit as st
from openai import OpenAI
import toml
import sys
import vignettes

def load_api_params() -> dict:
    try:
        with open('.secrets.toml', 'r') as f:
            secrets = toml.load(f)
        return {
            'API_KEY': secrets['API_KEY'], 
            'API_URL': secrets['API_URL'],
            'API_MODEL': secrets['API_MODEL']
        }
    except Exception as e:
        print(f"Error loading API key: {e}", file=sys.stderr)
        sys.exit(1)

API_CALL_PARAMS = load_api_params()

client = OpenAI(
    base_url = API_CALL_PARAMS['API_URL'],
    api_key = API_CALL_PARAMS['API_KEY']
)

# Set page title and layout
st.set_page_config(page_title="OpenAI Model Comparison", layout="wide")

# Initialize chat histories
if "messages_adapter" not in st.session_state:
    st.session_state.messages_adapter = []
if "messages_base" not in st.session_state:
    st.session_state.messages_base = []

# Function to generate OpenAI ChatCompletion response
def generate_response(prompt, model, messages):

    vignette_prompt = vignettes.get('Jamela')+"\n\nTake on the role of the main character in the above narrative."

    augmented_messages = [
        {"role": "system", "content": vignette_prompt}
    ] + messages + [{"role": "user", "content": prompt}]
    
    response = client.chat.completions.create(
        model=model,
        messages=augmented_messages,
        max_tokens=3000,
    )
    
    return response.choices[0].message.content

# Function to display chat messages
def display_chat(messages, container):
    for message in messages:
        with container.chat_message(message["role"]):
            container.markdown(message["content"])

# Create a placeholder for the persistent message bar
persistent_message = st.empty()

# Create a container for the main content
main_container = st.container()

with main_container:
    # Display application title and explanation
    st.title("Model Comparison: Trained Adapter vs Default Base")
    st.markdown("""
    This interface allows you to compare responses from the trained adapter and the default base model side by side.
    Enter your prompt in the text input box and click 'Send' to get responses from both models.
    """)

    # Create two columns for side-by-side comparison
    col1, col2 = st.columns(2)

    with col1:
        st.header("Adapter")
        chat_container_adapter = st.container()

    with col2:
        st.header("Base")
        chat_container_base = st.container()

    # Display chat messages from history on app rerun
    display_chat(st.session_state.messages_adapter, chat_container_adapter)
    display_chat(st.session_state.messages_base, chat_container_base)

    # Accept user input
    prompt = st.text_input("Enter your prompt for both models:")

    if st.button("Send"):
        if prompt:
            # Add user message to both chat histories
            st.session_state.messages_adapter.append({"role": "user", "content": prompt})
            st.session_state.messages_base.append({"role": "user", "content": prompt})

            # Display user message in both chat containers
            with chat_container_adapter.chat_message("user"):
                chat_container_adapter.markdown(prompt)
            with chat_container_base.chat_message("user"):
                chat_container_base.markdown(prompt)

            # Generate responses for both models
            response_adapter = generate_response(prompt, API_CALL_PARAMS['API_MODEL'], st.session_state.messages_adapter)
            response_base = generate_response(prompt, "", st.session_state.messages_base)

            # Display responses
            with chat_container_adapter.chat_message("assistant"):
                chat_container_adapter.markdown(response_adapter)
            with chat_container_base.chat_message("assistant"):
                chat_container_base.markdown(response_base)

            # Add assistant responses to chat histories
            st.session_state.messages_adapter.append({"role": "assistant", "content": response_adapter})
            st.session_state.messages_base.append({"role": "assistant", "content": response_base})

# Display the persistent message at the bottom
persistent_message.info("Enjoy using the model comparison tool!")